-- Dimension: Matchdays with schedule awareness
-- Enables: matchday-aware DAG scheduling, "next matchday" widget

with matchdays as (
    select distinct on (match_id)
        cast(json_extract_string(raw_json, '$.matchday') as integer) as matchday,
        utc_date,
        status,
        match_id
    from raw.live_matches
    where source = 'football-data.org'
    order by match_id, ingested_at desc
),

per_matchday as (
    select
        matchday,
        min(utc_date) as first_kickoff,
        max(utc_date) as last_kickoff,
        count(*) as total_matches,
        sum(case when status = 'FINISHED' then 1 else 0 end) as completed,
        sum(case when status in ('TIMED', 'SCHEDULED') then 1 else 0 end) as scheduled,
        sum(case when status in ('IN_PLAY', 'LIVE', 'PAUSED', 'HALFTIME') then 1 else 0 end) as live_now
    from matchdays
    group by matchday
)

select
    matchday,
    first_kickoff,
    last_kickoff,
    first_kickoff::date as matchday_start_date,
    last_kickoff::date as matchday_end_date,
    total_matches,
    completed,
    scheduled,
    live_now,
    case
        when live_now > 0 then 'LIVE'
        when completed = total_matches then 'COMPLETED'
        when completed > 0 then 'IN_PROGRESS'
        else 'UPCOMING'
    end as matchday_status,
    -- For scheduling: is today within this matchday window?
    case
        when current_date between first_kickoff::date - 1 and last_kickoff::date + 1 then true
        else false
    end as is_active_window
from per_matchday
order by matchday
