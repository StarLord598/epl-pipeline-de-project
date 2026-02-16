with ranked as (
    select
        *,
        row_number() over (
            partition by player_id
            order by ingested_at desc
        ) as rn
    from {{ source('epl_raw', 'top_scorers') }}
)

select
    player_id,
    player_name,
    nationality,
    position,
    cast(date_of_birth as date) as date_of_birth,
    team_id,
    team_name,
    played_matches,
    goals,
    assists,
    penalties,
    matchday,
    cast(ingested_at as timestamp) as ingested_at
from ranked
where rn = 1
