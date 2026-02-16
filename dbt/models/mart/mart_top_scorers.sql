-- Gold layer: Top scorers with per-game metrics

select
    ts.player_id,
    ts.player_name,
    ts.nationality,
    ts.position,
    ts.date_of_birth,
    ts.team_id,
    ts.team_name,
    ts.played_matches,
    ts.goals,
    ts.assists,
    ts.penalties,

    -- Calculated metrics
    round(safe_divide(ts.goals, ts.played_matches), 2) as goals_per_game,
    round(safe_divide(ts.assists, ts.played_matches), 2) as assists_per_game,
    coalesce(ts.goals, 0) + coalesce(ts.assists, 0) as goal_contributions,
    ts.goals - coalesce(ts.penalties, 0) as non_penalty_goals,
    ts.matchday,
    ts.ingested_at

from {{ ref('stg_top_scorers') }} ts
where ts.goals > 0
order by ts.goals desc, ts.assists desc
