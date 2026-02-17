-- Gold layer: Match results ready for dashboard
-- Includes derived result for home/away teams

select
    m.match_id,
    m.matchday,
    m.match_date,
    m.home_team_id,
    m.home_team_name,
    m.away_team_id,
    m.away_team_name,
    m.home_score,
    m.away_score,
    m.winner,
    m.match_status,

    -- Home team result
    case when m.winner = 'HOME_TEAM' then 'W'
         when m.winner = 'DRAW'      then 'D'
         when m.winner = 'AWAY_TEAM' then 'L'
         else null
    end as home_result,

    -- Away team result
    case when m.winner = 'AWAY_TEAM' then 'W'
         when m.winner = 'DRAW'      then 'D'
         when m.winner = 'HOME_TEAM' then 'L'
         else null
    end as away_result

from {{ ref('stg_matches') }} m
order by m.match_date desc, m.matchday desc
