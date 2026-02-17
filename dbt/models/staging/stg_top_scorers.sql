-- Top scorers derived from event data
-- Goals = shots with outcome 'Goal', Assists = passes with outcome 'Goal'

with shot_goals as (
    select
        player_id,
        player_name,
        team_id,
        team_name,
        count(*) as goals
    from {{ source('raw', 'events') }}
    where event_type = 'Shot'
      and outcome = 'Goal'
      and player_id is not null
    group by player_id, player_name, team_id, team_name
),

pass_assists as (
    select
        player_id,
        count(*) as assists
    from {{ source('raw', 'events') }}
    where event_type = 'Pass'
      and outcome = 'Goal'
      and player_id is not null
    group by player_id
),

matches_played as (
    select
        player_id,
        count(distinct match_id) as matches
    from {{ source('raw', 'events') }}
    where player_id is not null
    group by player_id
)

select
    s.player_id,
    s.player_name,
    s.team_name,
    s.goals,
    coalesce(a.assists, 0) as assists,
    s.goals + coalesce(a.assists, 0) as goal_contributions,
    m.matches as matches_played,
    round(cast(s.goals as double) / nullif(m.matches, 0), 2) as goals_per_game
from shot_goals s
left join pass_assists a on s.player_id = a.player_id
left join matches_played m on s.player_id = m.player_id
order by s.goals desc, coalesce(a.assists, 0) desc
