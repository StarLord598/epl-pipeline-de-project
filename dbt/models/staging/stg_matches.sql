-- Cleaned, enriched matches from raw layer
-- Adds derived winner column and casts types

with source as (
    select * from {{ source('raw', 'matches') }}
),

cleaned as (
    select
        match_id,
        competition_id,
        competition_name,
        season_id,
        season_name,
        try_cast(match_date as date) as match_date,
        home_team_id,
        home_team_name,
        away_team_id,
        away_team_name,
        home_score,
        away_score,
        case
            when home_score > away_score then 'HOME_TEAM'
            when away_score > home_score then 'AWAY_TEAM'
            when home_score = away_score then 'DRAW'
            else null
        end as winner,
        match_status,
        matchday,
        ingested_at
    from source
    where match_status = 'available'
      and season_id = 2324  -- 2023-24 Premier League season
)

select * from cleaned
