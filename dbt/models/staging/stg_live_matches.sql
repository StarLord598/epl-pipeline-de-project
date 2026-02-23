-- Silver: Clean live matches from football-data.org
-- Normalizes status codes, handles nulls, filters to EPL only

with latest_ingest as (
    select max(ingested_at) as max_ts
    from {{ source('raw', 'live_matches') }}
    where source = 'football-data.org'
),

cleaned as (
    select
        lm.match_id,
        lm.utc_date,
        -- Normalize status codes
        case
            when lm.status in ('IN_PLAY', 'LIVE') then 'LIVE'
            when lm.status in ('PAUSED', 'HALFTIME') then 'HALFTIME'
            when lm.status = 'FINISHED' then 'FINISHED'
            when lm.status in ('TIMED', 'SCHEDULED', 'Not Started') then 'SCHEDULED'
            when lm.status = 'POSTPONED' then 'POSTPONED'
            else lm.status
        end as status,
        lm.minute,
        regexp_replace(regexp_replace(lm.home_team_name, ' FC$', ''), '^AFC ', '') as home_team,
        regexp_replace(regexp_replace(lm.away_team_name, ' FC$', ''), '^AFC ', '') as away_team,
        lm.home_team_name as home_team_raw,
        lm.away_team_name as away_team_raw,
        coalesce(lm.home_score, 0) as home_score,
        coalesce(lm.away_score, 0) as away_score,
        lm.winner,
        lm.competition,
        lm.season,
        lm.ingested_at
    from {{ source('raw', 'live_matches') }} lm
    inner join latest_ingest li on lm.ingested_at = li.max_ts
    where lm.source = 'football-data.org'
      and lm.competition = 'Premier League'
)

select
    match_id,
    utc_date,
    status,
    minute,
    home_team,
    away_team,
    home_team_raw,
    away_team_raw,
    home_score,
    away_score,
    winner,
    competition,
    season,
    -- Derived
    cast(strftime(utc_date, '%W') as integer) as matchday_approx,
    ingested_at
from cleaned
order by utc_date desc
