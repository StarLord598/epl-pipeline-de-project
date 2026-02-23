-- Silver: Clean live standings from football-data.org
-- Deduplicates to latest ingestion, normalizes team names, validates data

with latest_ingest as (
    select max(ingested_at) as max_ts
    from {{ source('raw', 'live_standings') }}
    where source = 'football-data.org'
),

cleaned as (
    select
        ls.position,
        -- Normalize team names: strip "FC", "AFC" prefixes/suffixes
        regexp_replace(
            regexp_replace(ls.team_name, ' FC$', ''),
            '^AFC ', ''
        ) as team_name,
        ls.team_name as team_name_raw,
        ls.played,
        ls.won,
        ls.draw as drawn,
        ls.lost,
        ls.goals_for,
        ls.goals_against,
        coalesce(ls.goal_difference, ls.goals_for - ls.goals_against) as goal_difference,
        ls.points,
        ls.form,
        ls.season,
        ls.ingested_at
    from {{ source('raw', 'live_standings') }} ls
    inner join latest_ingest li on ls.ingested_at = li.max_ts
    where ls.source = 'football-data.org'
)

select
    position,
    team_name,
    team_name_raw,
    played,
    won,
    drawn,
    lost,
    goals_for,
    goals_against,
    goal_difference,
    points,
    form,
    season,
    -- Derived metrics
    case when played > 0 then round(won * 100.0 / played, 1) else 0 end as win_rate,
    case when played > 0 then round(points * 100.0 / (played * 3), 1) else 0 end as points_pct,
    case when played > 0 then round(goals_for * 1.0 / played, 2) else 0 end as goals_per_game,
    case when played > 0 then round(goals_against * 1.0 / played, 2) else 0 end as goals_conceded_per_game,
    ingested_at
from cleaned
order by position
