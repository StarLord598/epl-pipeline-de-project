-- mart_top_scorers: Gold layer top scorers with ranking
-- BigQuery-compatible: uses SAFE_DIVIDE, ROW_NUMBER window function

select
    ROW_NUMBER() OVER (
        ORDER BY s.goals DESC, s.assists DESC
    ) as rank,
    s.player_id,
    s.player_name,
    s.team_name,
    s.goals,
    s.assists,
    s.goal_contributions,
    s.matches_played,
    s.goals_per_game,
    ROUND({{ safe_divide('s.assists', 's.matches_played') }}, 2) as assists_per_game

from {{ ref('stg_top_scorers') }} s
order by s.goals desc, s.assists desc
limit 30
