# EPL Analytics Pipeline — API Reference

Base URL: `http://localhost:3000/api`

All endpoints return JSON. Responses include `Cache-Control` headers for client-side caching.

---

## League Table

### `GET /api/league-table`

Returns the current 2025-26 EPL standings.

**Response:** Array of 20 team objects, ordered by position.

```json
[
  {
    "position": 1,
    "team_name": "Arsenal",
    "played": 27,
    "won": 19,
    "drawn": 3,
    "lost": 5,
    "goals_for": 52,
    "goals_against": 24,
    "goal_difference": 28,
    "points": 60,
    "form": "W,W,D,W,D",
    "qualification_zone": "champions_league"
  }
]
```

---

## Standings History (SCD2)

### `GET /api/standings/history`

Returns SCD Type 2 position tracking — how each team's league position changed across matchdays.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `team` | string | Filter by team name (case-insensitive) |
| `matchday` | integer | Filter by specific matchday (1-38) |
| `changes_only` | boolean | If `true`, only return rows where position changed |

**Examples:**
```bash
# Arsenal's full position history
GET /api/standings/history?team=Arsenal

# All position changes on matchday 10
GET /api/standings/history?matchday=10&changes_only=true
```

**Response:**
```json
{
  "count": 5,
  "data": [
    {
      "team_name": "Arsenal",
      "matchday": 1,
      "position": 6,
      "prev_position": null,
      "movement": "NEW",
      "positions_moved": 0,
      "points": 3
    },
    {
      "team_name": "Arsenal",
      "matchday": 2,
      "position": 1,
      "prev_position": 6,
      "movement": "UP",
      "positions_moved": 5,
      "points": 6
    }
  ]
}
```

---

## Points Race

### `GET /api/race`

Returns cumulative points per team per matchday — designed for line chart visualization.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `teams` | string | Comma-separated team names |
| `from` | integer | Start matchday |
| `to` | integer | End matchday |

**Example:**
```bash
GET /api/race?teams=Arsenal,Chelsea&from=1&to=15
```

**Response:**
```json
{
  "count": 30,
  "data": [
    {
      "team_name": "Arsenal",
      "matchday": 1,
      "matchday_points": 3,
      "cumulative_points": 3
    }
  ]
}
```

---

## Rolling Form

### `GET /api/form`

Returns rolling 5-game form data with momentum classification.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `team` | string | Filter by team name |
| `momentum` | string | Filter by tier: `HOT`, `STEADY`, `COOLING`, `COLD` |

**Momentum Tiers:**
| Tier | PPG Range | Meaning |
|------|-----------|---------|
| HOT | ≥ 2.2 | Title/European form |
| STEADY | ≥ 1.5 | Solid mid-table pace |
| COOLING | ≥ 0.8 | Dropping results |
| COLD | < 0.8 | Relegation form |

**Example:**
```bash
GET /api/form?momentum=HOT
```

**Response:**
```json
{
  "count": 5,
  "data": [
    {
      "team_name": "Manchester City",
      "matchday": 27,
      "last_5_form": "WDWWW",
      "rolling_5_ppg": 2.6,
      "rolling_5_goals_scored": 2.4,
      "rolling_5_goals_conceded": 0.8,
      "current_momentum": "HOT"
    }
  ]
}
```

---

## Teams Dimension

### `GET /api/teams`

Returns the team dimension with tier classification and season metrics.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `team` | string | Filter by team name |
| `tier` | string | Filter by tier: `TITLE CONTENDER`, `EUROPEAN HOPEFUL`, `MID-TABLE`, `RELEGATION BATTLE`, `RELEGATION ZONE` |

**Example:**
```bash
GET /api/teams?tier=TITLE+CONTENDER
```

---

## Data Quality

### `GET /api/quality`

Returns pipeline health metrics: test results, freshness SLAs, and table inventory.

**Response:**
```json
{
  "generated_at": "2026-02-23T19:07:42Z",
  "summary": {
    "total_tables": 32,
    "bronze_tables": 6,
    "silver_tables": 17,
    "gold_tables": 9,
    "total_rows": 135420
  },
  "tests": {
    "total": 29,
    "passed": 29,
    "failed": 0,
    "warned": 0
  },
  "freshness": [
    {
      "table": "raw.live_matches",
      "last_updated": "2026-02-23T18:45:00",
      "sla_hours": 1
    }
  ]
}
```

---

## Live Matches

### `GET /api/live`

Returns current live/recent match data (yesterday through 2 days ahead).

---

## Match History

### `GET /api/matches`

Returns full match results.

---

## Top Scorers

### `GET /api/scorers`

Returns top scorers with goals, assists, and per-game metrics.
