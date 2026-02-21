-- mart_league_table: Gold layer EPL League Table for dashboard
-- BigQuery-compatible: uses SAFE_DIVIDE, ROUND, standard BigQuery SQL

select
    ROW_NUMBER() OVER (
        ORDER BY s.points DESC, s.goal_difference DESC, s.goals_for DESC
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

    -- Calculated metrics (portable across BigQuery + DuckDB)
    ROUND({{ safe_divide('s.points', 's.played * 3') }} * 100, 1) as points_pct,
    ROUND({{ safe_divide('s.won', 's.played') }} * 100, 1)        as win_rate,
    ROUND({{ safe_divide('s.goals_for', 's.played') }}, 2)        as goals_per_game,
    ROUND({{ safe_divide('s.goals_against', 's.played') }}, 2)    as goals_conceded_per_game,

    -- Qualification zones
    CASE
        WHEN ROW_NUMBER() OVER (ORDER BY s.points DESC, s.goal_difference DESC, s.goals_for DESC) <= 4
            THEN 'champions_league'
        WHEN ROW_NUMBER() OVER (ORDER BY s.points DESC, s.goal_difference DESC, s.goals_for DESC) = 5
            THEN 'europa_league'
        WHEN ROW_NUMBER() OVER (ORDER BY s.points DESC, s.goal_difference DESC, s.goals_for DESC) = 6
            THEN 'conference_league'
        WHEN ROW_NUMBER() OVER (ORDER BY s.points DESC, s.goal_difference DESC, s.goals_for DESC) >= 18
            THEN 'relegation'
        ELSE 'midtable'
    END as qualification_zone

from {{ ref('stg_standings') }} s
order by s.points desc, s.goal_difference desc, s.goals_for desc
