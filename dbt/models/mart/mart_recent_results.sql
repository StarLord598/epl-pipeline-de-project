-- Gold layer: Recent and upcoming fixtures for dashboard

select
    f.match_id,
    f.matchday,
    f.status,
    f.kick_off_utc,
    f.home_team_id,
    f.home_team_name,
    f.away_team_id,
    f.away_team_name,
    f.home_score,
    f.away_score,
    f.winner,

    -- Enrichment
    case
        when f.status = 'FINISHED' then concat(
            cast(f.home_score as string), ' - ', cast(f.away_score as string)
        )
        when f.status = 'IN_PLAY' then 'LIVE'
        when f.status = 'TIMED' then 'Upcoming'
        else f.status
    end as display_status,

    hs.team_crest as home_crest,
    aws.team_crest as away_crest,

    f.ingested_at

from {{ ref('stg_fixtures') }} f
left join {{ ref('stg_standings') }} hs on f.home_team_id = hs.team_id
left join {{ ref('stg_standings') }} aws on f.away_team_id = aws.team_id
where f.kick_off_utc >= timestamp_sub(current_timestamp(), interval 14 day)
order by f.kick_off_utc desc
