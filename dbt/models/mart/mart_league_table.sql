-- Gold layer: EPL League Table ready for dashboard consumption
-- Enriched with calculated metrics

select
    s.position,
    s.team_id,
    s.team_name,
    s.team_crest,
    s.played_games,
    s.won,
    s.draw,
    s.lost,
    s.points,
    s.goals_for,
    s.goals_against,
    s.goal_difference,
    s.form,
    s.matchday,

    -- Calculated metrics
    round(safe_divide(s.points, s.played_games * 3) * 100, 1) as points_pct,
    round(safe_divide(s.won, s.played_games) * 100, 1) as win_rate,
    round(safe_divide(s.goals_for, s.played_games), 2) as goals_per_game,
    round(safe_divide(s.goals_against, s.played_games), 2) as goals_conceded_per_game,

    s.ingested_at

from {{ ref('stg_standings') }} s
order by s.position
