-- Gold: SCD Type 2 — League position history
-- Tracks when each team's position changed across matchdays
-- Enables: "Arsenal moved to #1 on GW8 and has held it since"

with matchday_standings as (
    -- Reconstruct standings at each matchday from match results
    select
        cast(json_extract_string(lm.raw_json, '$.matchday') as integer)
            as matchday,
        cast(max(lm.utc_date) as date) as matchday_date,
        regexp_replace(
            regexp_replace(lm.home_team_name, ' FC$', ''), '^AFC ', ''
        ) as team_name,
        -- We need to compute standings from results up to this matchday
        1 as placeholder
    from raw.live_matches as lm
    where
        lm.source = 'football-data.org'
        and lm.status = 'FINISHED'
    group by 1, 3
),

-- Get all finished match results with matchday
match_results as (
    select distinct on (match_id)
        match_id,
        cast(json_extract_string(raw_json, '$.matchday') as integer)
            as matchday,
        home_score,
        away_score,
        cast(utc_date as date) as match_date,
        regexp_replace(
            regexp_replace(home_team_name, ' FC$', ''), '^AFC ', ''
        ) as home_team,
        regexp_replace(
            regexp_replace(away_team_name, ' FC$', ''), '^AFC ', ''
        ) as away_team
    from raw.live_matches
    where
        source = 'football-data.org'
        and status = 'FINISHED'
        and home_score is not null
    order by match_id asc, ingested_at desc
),

-- Expand to per-team results
team_results as (
    select
        matchday,
        home_team as team,
        home_score as gf,
        away_score as ga,
        case
            when home_score > away_score then 3 when
                home_score = away_score
                then 1
            else 0
        end as pts,
        match_date
    from match_results
    union all
    select
        matchday,
        away_team as team,
        away_score as gf,
        home_score as ga,
        case
            when away_score > home_score then 3 when
                away_score = home_score
                then 1
            else 0
        end as pts,
        match_date
    from match_results
),

-- Cumulative standings at each matchday
cumulative as (
    select
        tr.team,
        tr.matchday as through_matchday,
        sum(tr.pts)
            over (
                partition by tr.team
                order by tr.matchday rows unbounded preceding
            )
            as cum_points,
        sum(tr.gf)
            over (
                partition by tr.team
                order by tr.matchday rows unbounded preceding
            )
            as cum_gf,
        sum(tr.ga)
            over (
                partition by tr.team
                order by tr.matchday rows unbounded preceding
            )
            as cum_ga,
        count(*)
            over (
                partition by tr.team
                order by tr.matchday rows unbounded preceding
            )
            as cum_played,
        max(tr.match_date)
            over (
                partition by tr.team
                order by tr.matchday rows unbounded preceding
            )
            as matchday_date
    from team_results as tr
),

-- Deduplicate to one row per team per matchday
per_matchday as (
    select
        team as team_name,
        through_matchday as matchday,
        max(cum_points) as points,
        max(cum_gf) as goals_for,
        max(cum_ga) as goals_against,
        max(cum_gf) - max(cum_ga) as goal_difference,
        max(cum_played) as played,
        max(matchday_date) as matchday_date
    from cumulative
    group by team, through_matchday
),

-- Rank at each matchday
ranked as (
    select
        *,
        row_number() over (
            partition by matchday
            order by
                points desc, goal_difference desc, goals_for desc, team_name asc
        ) as position
    from per_matchday
),

-- SCD Type 2: detect position changes
with_changes as (
    select
        *,
        lag(position)
            over (partition by team_name order by matchday)
            as prev_position,
        case
            when
                lag(position)
                    over (partition by team_name order by matchday)
                is null
                then true
            when
                lag(position) over (partition by team_name order by matchday)
                != position
                then true
            else false
        end as position_changed
    from ranked
)

select
    team_name,
    matchday,
    matchday_date,
    position,
    prev_position,
    position_changed,
    points,
    played,
    goals_for,
    goals_against,
    goal_difference,
    -- Movement direction
    case
        when prev_position is null then 'NEW'
        when position < prev_position then 'UP'
        when position > prev_position then 'DOWN'
        else 'SAME'
    end as movement,
    coalesce(prev_position - position, 0) as positions_moved
from with_changes
order by matchday, position
