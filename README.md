# ⚽ EPL Analytics Pipeline

A complete, working Premier League analytics pipeline and dashboard built with DuckDB, Python, dbt, and Next.js.

## Live Features

- **Full 2023-24 EPL Season** — All 380 matches, final standings, real results
- **League Table** — Live standings with qualification zones, form, win rates
- **Top Scorers** — Golden Boot race with goals/assists/per-game stats + charts
- **Match Results** — All matchdays with scores, browseable by round
- **Match Detail** — Click any match for events timeline, stats, goal scorers
- **Team Pages** — Full season summary per club with match history
- **Season Stats** — Radar charts, goals analysis, team comparisons

## Architecture

```
Data Sources
  ├── football-data.co.uk (2023-24 EPL results CSV, free)
  └── StatsBomb Open Data (2003/04 Arsenal events, free)
        ↓
  DuckDB (local OLAP database)
    ├── raw.matches
    ├── raw.events (129k rows)
    └── raw.lineups
        ↓
  dbt (SQL transforms)
    ├── staging/ (views, cleaned data)
    └── mart/ (tables, dashboard-ready)
        ↓
  JSON exports → Next.js Dashboard
```

## Quick Start

### 1. Setup

```bash
cd /path/to/epl-pipeline
python3.13 -m venv venv313
source venv313/bin/activate
pip install duckdb statsbombpy dbt-duckdb requests pandas
```

### 2. Run the full pipeline

```bash
./scripts/run_pipeline.sh
```

Or step by step:

```bash
# Ingest StatsBomb events
source venv313/bin/activate
python3 scripts/ingest_data.py

# Ingest 2023-24 results + top scorers
python3 scripts/ingest_full_season.py

# Run dbt transforms
cd dbt
EPL_DB_PATH=../data/epl_pipeline.duckdb dbt run
EPL_DB_PATH=../data/epl_pipeline.duckdb dbt test  # 17/17 tests pass
```

### 3. Start the dashboard

```bash
cd dashboard
npm install
npm run dev
# Open http://localhost:3000
```

## Data Sources

| Source | Data | Auth |
|--------|------|------|
| [football-data.co.uk](https://www.football-data.co.uk) | Full 2023-24 EPL results CSV | None (free) |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | Match events, lineups (2003-04 Arsenal) | None (fully open) |

## Project Structure

```
epl-pipeline/
├── scripts/
│   ├── ingest_data.py          # StatsBomb ingestion
│   ├── ingest_full_season.py   # football-data.co.uk ingestion
│   └── run_pipeline.sh         # Full pipeline runner
├── dbt/
│   ├── models/staging/         # Cleaned views (stg_matches, stg_standings, etc.)
│   └── models/mart/            # Gold tables (mart_league_table, etc.)
├── airflow/dags/
│   ├── ingest_epl_local.py     # Local DuckDB DAG
│   └── ...                     # Original BigQuery DAGs (for future migration)
├── dashboard/                  # Next.js 14 App Router
│   ├── app/                    # Pages
│   ├── components/             # Reusable components
│   └── lib/data.ts             # Type definitions
├── data/
│   ├── epl_pipeline.duckdb     # Local database
│   └── json/                   # Pre-exported data for dashboard
└── infra/                      # Terraform (for future GCP migration)
```

## dbt Models

| Model | Type | Description |
|-------|------|-------------|
| `stg_matches` | view | Cleaned 2023-24 matches with winner |
| `stg_standings` | view | Points table from match results |
| `stg_top_scorers` | view | Scorers from event data |
| `mart_league_table` | table | Full standings with calculated metrics |
| `mart_recent_results` | table | All matches with H/A results |
| `mart_top_scorers` | table | Golden Boot leaderboard |

## Technology Stack

- **DuckDB 1.4** — Local OLAP database (zero-config, no server)
- **Python 3.13** — Data ingestion and transformation
- **dbt 1.11** + **dbt-duckdb** — SQL transformations
- **StatsBombPy** — Official Python client for StatsBomb open data
- **Next.js 14** — App Router, TypeScript, Tailwind CSS
- **Recharts** — Data visualization
- **Airflow** — DAG orchestration (local or containerized)

## What's Next

- [ ] **BigQuery migration** — Swap DuckDB profile for BigQuery, run on GCP
- [ ] **GitHub Actions CI/CD** — Auto-run pipeline on schedule
- [ ] **Airflow on Docker** — Full containerized orchestration
- [ ] **2024-25 season** — Keep updating with current data
- [ ] **Player profiles** — Deep dive stats with xG, heatmaps
- [ ] **API routes** — Real-time DuckDB queries from dashboard

## Git

```
user.name  = rocket-racoon-tech-bot
user.email = rocket.racoon.tech1@gmail.com
```
