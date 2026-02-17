-- Gold layer: Top scorers with ranking and per-game stats

select
    row_number() over (
        order by s.goals desc, s.assists desc
    ) as rank,
    s.player_id,
    s.player_name,
    s.team_name,
    s.goals,
    s.assists,
    s.goal_contributions,
    s.matches_played,
    s.goals_per_game,
    round(cast(s.assists as double) / nullif(s.matches_played, 0), 2) as assists_per_game

from {{ ref('stg_top_scorers') }} s
order by s.goals desc, s.assists desc
limit 30
