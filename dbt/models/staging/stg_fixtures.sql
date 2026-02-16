-- Deduplicated, cleaned fixtures from raw layer
-- Takes the latest ingestion per match_id

with ranked as (
    select
        *,
        row_number() over (
            partition by match_id
            order by ingested_at desc
        ) as rn
    from {{ source('epl_raw', 'fixtures') }}
)

select
    match_id,
    matchday,
    status,
    cast(utc_date as timestamp) as kick_off_utc,
    home_team_id,
    home_team_name,
    away_team_id,
    away_team_name,
    home_score,
    away_score,
    winner,
    cast(ingested_at as timestamp) as ingested_at
from ranked
where rn = 1
