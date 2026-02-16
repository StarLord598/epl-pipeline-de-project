with ranked as (
    select
        *,
        row_number() over (
            partition by team_id, standing_type
            order by ingested_at desc
        ) as rn
    from {{ source('epl_raw', 'standings') }}
)

select
    team_id,
    team_name,
    team_crest,
    position,
    played_games,
    won,
    draw,
    lost,
    points,
    goals_for,
    goals_against,
    goal_difference,
    form,
    standing_type,
    matchday,
    cast(ingested_at as timestamp) as ingested_at
from ranked
where rn = 1 and standing_type = 'TOTAL'
