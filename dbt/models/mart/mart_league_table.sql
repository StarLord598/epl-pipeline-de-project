-- Gold layer: EPL League Table ready for dashboard consumption
-- Enriched with calculated metrics (DuckDB compatible)

select
    row_number() over (
        order by s.points desc, s.goal_difference desc, s.goals_for desc
    ) as position,
    s.team_id,
    s.team_name,
    s.played,
    s.won,
    s.drawn,
    s.lost,
    s.points,
    s.goals_for,
    s.goals_against,
    s.goal_difference,

    -- Calculated metrics (DuckDB uses standard division, no safe_divide needed)
    round(cast(s.points as double)      / nullif(s.played * 3, 0) * 100, 1) as points_pct,
    round(cast(s.won as double)         / nullif(s.played, 0) * 100, 1)     as win_rate,
    round(cast(s.goals_for as double)   / nullif(s.played, 0), 2)           as goals_per_game,
    round(cast(s.goals_against as double) / nullif(s.played, 0), 2)         as goals_conceded_per_game

from {{ ref('stg_standings') }} s
order by s.points desc, s.goal_difference desc, s.goals_for desc
