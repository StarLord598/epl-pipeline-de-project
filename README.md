# ⚽ EPL Analytics Pipeline

> **A production-grade data engineering platform** that ingests, transforms, tests, and serves Premier League data — orchestrated by Airflow, modeled in dbt, stored in DuckDB, and served through a Next.js dashboard with REST APIs.

[![CI — EPL Pipeline](https://github.com/StarLord598/epl-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/StarLord598/epl-pipeline/actions)
![dbt](https://img.shields.io/badge/dbt-15%20models-orange)
![Tests](https://img.shields.io/badge/tests-29%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                 │
│  football-data.org API ──── StatsBomb Open Data ──── TheSportsDB   │
│  (live scores/standings)    (129K match events)     (fallback API)  │
└──────────┬─────────────────────────┬──────────────────────┬─────────┘
           │                         │                      │
           ▼                         ▼                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    AIRFLOW ORCHESTRATION (Docker)                     │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  ┌────────────┐ │
│  │live_poll_15m │  │hourly_refresh│  │daily_recon│  │ingest_local│ │
│  │  ⚡ 15 min   │  │  🔄 hourly   │  │  🌙 2 AM  │  │  📥 6 AM   │ │
│  │  + matchday  │  │              │  │           │  │            │ │
│  │  awareness   │  │              │  │           │  │            │ │
│  └──────┬───────┘  └──────┬───────┘  └─────┬─────┘  └─────┬──────┘ │
└─────────┼─────────────────┼────────────────┼──────────────┼─────────┘
          │                 │                │              │
          ▼                 ▼                ▼              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    SCHEMA CONTRACTS (pre-validation)                  │
│   Required fields ─── Type checks ─── Enum values ─── Range checks  │
└──────────────────────────────────────┬───────────────────────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          ▼                            ▼                            ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
│  🥉 BRONZE (raw) │   │  🥈 SILVER (stg) │   │   🥇 GOLD (mart)     │
│                  │   │                  │   │                      │
│ live_matches     │──▶│ stg_live_matches │──▶│ mart_live_matches    │
│ live_standings   │──▶│ stg_live_stands  │──▶│ mart_live_league_tbl │
│ matches          │──▶│ stg_matches      │──▶│ mart_league_table    │
│ events (129K)    │   │ stg_standings    │──▶│ mart_recent_results  │
│ top_scorers      │   │ stg_top_scorers  │──▶│ mart_top_scorers     │
│ standings        │   │                  │   │ mart_scd2_standings  │
│                  │   │  5 views         │   │ mart_points_race     │
│  6 tables        │   │  (zero storage)  │   │ mart_rolling_form    │
│  (append-only)   │   │                  │   │ dim_teams            │
│                  │   │                  │   │ dim_matchdays        │
│                  │   │                  │   │  9 tables            │
└──────────────────┘   └──────────────────┘   └──────────┬───────────┘
                                                         │
          ┌────────────────────────┬─────────────────────┤
          ▼                        ▼                     ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────────┐
│ 🛡️ DATA QUALITY  │   │  📡 REST APIs    │   │  🖥️ DASHBOARD        │
│                  │   │                  │   │                      │
│ 29 dbt tests     │   │ /api/league-tbl  │   │ 🏆 Table             │
│ Schema contracts │   │ /api/standings/* │   │ 📈 Points Race       │
│ Freshness SLAs   │   │ /api/race        │   │ 🔥 Form & Momentum  │
│ Quality dashboard│   │ /api/form        │   │ ⚡ Live Matches      │
│                  │   │ /api/teams       │   │ ⚽ Results           │
│                  │   │ /api/quality     │   │ 🎯 Scorers          │
│                  │   │ /api/live        │   │ 📊 Stats            │
│                  │   │ /api/matches     │   │ 🛡️ Quality          │
│                  │   │ /api/scorers     │   │ 🔗 Lineage          │
└──────────────────┘   └──────────────────┘   └──────────────────────┘
```

## ✨ Key Features

### Data Engineering Patterns
| Pattern | Implementation | Details |
|---------|---------------|---------|
| **Medallion Architecture** | Bronze → Silver → Gold | 6 raw tables, 5 staging views, 9 Gold tables |
| **SCD Type 2** | `mart_scd2_standings` | Tracks league position changes across 38 matchdays |
| **Kimball Dimensions** | `dim_teams`, `dim_matchdays` | Fact/dimension modeling with tier classification |
| **Rolling Aggregations** | `mart_rolling_form` | 5-game rolling PPG, momentum classification (HOT/COLD) |
| **Cumulative Metrics** | `mart_points_race` | Running point totals per team per matchday |
| **Incremental Models** | `mart_recent_results` | Append-only — only processes new matches |
| **Matchday-Aware Scheduling** | `ShortCircuitOperator` | Skips API polling on non-matchdays to save resources |
| **Schema Contracts** | `contracts.py` | Validates API responses before Bronze insert; blocks bad batches |
| **Idempotent Backfill** | `backfill_season.py` | Safe to re-run — deduplicates on match_id |
| **Data Quality Framework** | 29 dbt tests + freshness SLAs | Uniqueness, not-null, accepted values, source freshness |

### Platform Capabilities
| Capability | Details |
|-----------|---------|
| **5 Airflow DAGs** | Docker Compose with LocalExecutor + Postgres |
| **15 dbt Models** | 5 views (Silver) + 9 tables + 1 incremental (Gold) |
| **29 Data Tests** | All passing — schema, uniqueness, completeness |
| **9 Dashboard Pages** | Interactive charts, live scores, quality monitoring |
| **8 REST API Endpoints** | Filterable by team, matchday, momentum tier |
| **Data Lineage** | Interactive dbt docs DAG at `/lineage` |
| **CI/CD** | GitHub Actions: lint SQL/Python → dbt test → dashboard build |
| **Full Documentation** | 150+ columns documented across all models and sources |

## 🚀 Quick Start

```bash
# Clone and setup (one command)
git clone https://github.com/StarLord598/epl-pipeline.git
cd epl-pipeline
make setup

# Run everything
make run          # Starts Airflow (localhost:8080) + Dashboard (localhost:3000)

# Or run individual components
make pipeline     # Ingest → dbt transform → JSON export
make test         # dbt tests + Python lint + dashboard build
make docs         # Regenerate data lineage
make demo         # Full pipeline + docs + dashboard
```

### Manual Setup
```bash
# Python
python3.13 -m venv venv313 && source venv313/bin/activate
pip install -r requirements.txt

# Seed data
python scripts/backfill_season.py         # Full 2025-26 season (380 matches)

# dbt
cd dbt && dbt build --profiles-dir . --target local

# Dashboard
cd dashboard && npm ci && npm run dev     # → http://localhost:3000

# Airflow
docker compose up -d                      # → http://localhost:8080 (admin/admin)
```

### Environment Variables
```bash
cp .env.example .env
# Required: FOOTBALL_DATA_API_KEY (free at https://www.football-data.org/client/register)
```

## 📊 Dashboard Pages

| Page | Route | Description |
|------|-------|-------------|
| 🏆 **League Table** | `/` | Live 2025-26 standings with qualification zones, form, per-game stats |
| 📈 **Points Race** | `/race` | Interactive line chart — cumulative points for all 20 teams across matchdays |
| 🔥 **Form & Momentum** | `/form` | Hot/Cold momentum panel (rolling 5-game PPG) + SCD2 position history |
| ⚡ **Live Matches** | `/live` | Real-time scores with status badges (LIVE/HT/FT), auto-refresh |
| ⚽ **Results** | `/results` | Match results browseable by gameweek |
| 🎯 **Top Scorers** | `/scorers` | Golden Boot race with bar charts |
| 📊 **Stats** | `/stats` | Radar charts, team comparisons (select up to 4 teams) |
| 🛡️ **Data Quality** | `/quality` | Test pass rates, freshness SLAs, medallion inventory, table row counts |
| 🔗 **Data Lineage** | `/lineage` | Interactive dbt docs — full dependency graph for all 15 models |

## 📡 REST API

All endpoints return JSON with `Cache-Control` headers.

| Endpoint | Method | Params | Description |
|----------|--------|--------|-------------|
| `/api/league-table` | GET | — | Current league standings |
| `/api/standings/history` | GET | `?team=Arsenal&matchday=15&changes_only=true` | SCD2 position history |
| `/api/race` | GET | `?teams=Arsenal,Chelsea&from=5&to=20` | Cumulative points race |
| `/api/form` | GET | `?team=Arsenal&momentum=HOT` | Rolling 5-game form |
| `/api/teams` | GET | `?tier=TITLE+CONTENDER` | Team dimension with tiers |
| `/api/quality` | GET | — | Pipeline health and test results |
| `/api/live` | GET | — | Current live match data |
| `/api/matches` | GET | — | Full match history |
| `/api/scorers` | GET | — | Top scorers |

### Example
```bash
# Get all teams currently in HOT form
curl "http://localhost:3000/api/form?momentum=HOT"

# Arsenal's position changes this season
curl "http://localhost:3000/api/standings/history?team=Arsenal&changes_only=true"

# Points race for the title contenders
curl "http://localhost:3000/api/race?teams=Arsenal,Manchester%20City,Chelsea"
```

## 🗂️ Project Structure

```
epl-pipeline/
├── Makefile                        # One-command interface (setup/run/test/demo)
├── docker-compose.yml              # Airflow + Postgres
├── requirements.txt                # Python dependencies (pinned)
├── .env.example                    # Environment template
├── .github/workflows/ci.yml        # CI: lint → dbt test → dashboard build
│
├── scripts/                        # Python ingestion + quality + exports
│   ├── ingest_live_matches.py      # Live API → DuckDB (with contract validation)
│   ├── ingest_live_standings.py    # Live standings → DuckDB
│   ├── backfill_season.py          # Full season backfill (idempotent)
│   ├── contracts.py                # Schema contract validation framework
│   ├── validate_live_payloads.py   # Pre-transform validation
│   ├── check_live_freshness.py     # Freshness monitoring
│   ├── is_matchday.py              # Matchday-aware scheduling check
│   ├── export_live_json.py         # Gold → dashboard JSON
│   ├── export_quality.py           # Quality metrics → JSON
│   └── live_common.py              # Shared utilities
│
├── dbt/                            # SQL transformations (dbt-duckdb)
│   ├── models/
│   │   ├── staging/                # 🥈 Silver layer (5 views)
│   │   │   ├── stg_matches.sql
│   │   │   ├── stg_standings.sql
│   │   │   ├── stg_top_scorers.sql
│   │   │   ├── stg_live_matches.sql    # Dedup via ROW_NUMBER()
│   │   │   ├── stg_live_standings.sql  # Dedup via ROW_NUMBER()
│   │   │   └── schema.yml             # 6 sources, 5 models, all columns documented
│   │   └── mart/                   # 🥇 Gold layer (9 tables + 1 incremental)
│   │       ├── mart_league_table.sql
│   │       ├── mart_live_league_table.sql
│   │       ├── mart_live_matches.sql
│   │       ├── mart_recent_results.sql     # Incremental
│   │       ├── mart_top_scorers.sql
│   │       ├── mart_scd2_standings.sql     # SCD Type 2
│   │       ├── mart_points_race.sql        # Cumulative metrics
│   │       ├── mart_rolling_form.sql       # Rolling windows
│   │       ├── dim_teams.sql               # Kimball dimension
│   │       ├── dim_matchdays.sql           # Schedule dimension
│   │       └── schema.yml                  # All models + columns documented
│   ├── macros/
│   │   ├── safe_divide.sql         # Portable division (BigQuery ↔ DuckDB)
│   │   └── generate_schema_name.sql
│   ├── dbt_project.yml
│   └── profiles.yml                # Local (DuckDB) target
│
├── airflow/dags/                   # Orchestration (5 active DAGs)
│   ├── live_poll_15m.py            # ⚡ 15-min + matchday-aware ShortCircuit
│   ├── hourly_refresh.py           # 🔄 Hourly pipeline
│   ├── dbt_transform.py            # 🔧 30-min dbt runs
│   ├── daily_reconcile.py          # 🌙 2 AM full rebuild
│   └── ingest_epl_local.py         # 📥 6 AM StatsBomb refresh
│
├── dashboard/                      # Next.js 14 + TypeScript + Tailwind
│   ├── app/                        # 9 pages (App Router)
│   │   ├── page.tsx                # League table
│   │   ├── race/page.tsx           # Points race chart
│   │   ├── form/page.tsx           # Momentum + SCD2 tracker
│   │   ├── live/page.tsx           # Live matches
│   │   ├── results/page.tsx        # Match results
│   │   ├── scorers/page.tsx        # Top scorers
│   │   ├── stats/page.tsx          # Team comparisons
│   │   ├── quality/page.tsx        # Data quality dashboard
│   │   ├── lineage/page.tsx        # dbt docs embed
│   │   └── api/                    # 8 REST API routes
│   ├── components/                 # Reusable UI (Navigation, TeamBadge, etc.)
│   └── lib/                        # Data fetching + types
│
├── data/
│   └── epl_pipeline.duckdb         # Local OLAP warehouse
│
└── docs/
    ├── architecture.mmd            # Mermaid source
    └── architecture.png            # Rendered diagram
```

## 🧪 Data Quality

### dbt Tests (29 assertions)
- **Uniqueness**: All primary keys (match_id, team_name, player_id)
- **Not-null**: Critical fields across all layers
- **Source freshness**: 1h warn / 4h error SLAs on live tables

### Schema Contracts (`scripts/contracts.py`)
- Pre-ingestion validation of API responses
- Required fields, type checks, enum validation, range checks, nested field validation
- 10% failure threshold blocks entire batch from entering Bronze

### Quality Dashboard (`/quality`)
- Real-time test pass rates
- Data freshness with SLA indicators
- Table inventory across Bronze/Silver/Gold
- Individual test execution times

## 🛠️ Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Ingestion** | Python 3.13, requests | API extraction with contract validation |
| **Storage** | DuckDB 1.1 | Embedded OLAP database (zero-config, columnar) |
| **Transform** | dbt-core 1.8 + dbt-duckdb | SQL transforms, testing, documentation |
| **Orchestration** | Apache Airflow 2.9 (Docker) | 5 DAGs with matchday-aware scheduling |
| **Dashboard** | Next.js 14, TypeScript, Tailwind CSS | 9-page data application |
| **Charts** | Recharts | Line charts, bar charts, radar charts |
| **API** | Next.js API Routes | 8 REST endpoints with query filters |
| **CI/CD** | GitHub Actions | Lint → dbt build → dashboard build |
| **Containers** | Docker Compose | Airflow + Postgres backend |

## 📈 Data Pipeline Details

### Medallion Architecture

| Layer | Schema | Count | Materialization | Retention | Purpose |
|-------|--------|-------|-----------------|-----------|---------|
| 🥉 **Bronze** | `raw` | 6 tables | Append-only | Unlimited | Raw API responses — full audit trail |
| 🥈 **Silver** | `staging` | 5 views | Virtual (zero storage) | N/A | Dedup, normalize, derive metrics |
| 🥇 **Gold** | `mart` | 9 tables + 1 incremental | Full refresh / incremental | Current state | Business-ready data for dashboard + APIs |

### Data Warehouse Patterns

| Pattern | Model | What It Demonstrates |
|---------|-------|---------------------|
| **SCD Type 2** | `mart_scd2_standings` | Position tracking with change detection across 38 matchdays |
| **Kimball Dimensions** | `dim_teams`, `dim_matchdays` | Star schema with tier classification and schedule awareness |
| **Rolling Windows** | `mart_rolling_form` | 5-game rolling PPG, momentum tiers (HOT/STEADY/COOLING/COLD) |
| **Cumulative Metrics** | `mart_points_race` | Running totals for season-long visualization |
| **Incremental** | `mart_recent_results` | Append-only processing — only new matches per run |
| **View-based Staging** | All `stg_*` models | Zero-cost transforms that always reflect latest Bronze data |
| **Schema Contracts** | `contracts.py` | Pre-validation firewall at the ingestion boundary |
| **Matchday-Aware Scheduling** | `is_matchday.py` + DAG | Resource optimization — skip polling when no matches |

### Data Sources

| Source | Data | Frequency | Records |
|--------|------|-----------|---------|
| football-data.org | Live scores, standings (2025-26) | Every 15 min | 380 matches, 20 teams |
| StatsBomb Open Data | Historical match events | Daily batch | 129K+ events |
| TheSportsDB | Fallback scores | On API failure | Auto-failover |

## 💰 Cost

| Component | Cost |
|-----------|------|
| DuckDB | Free (embedded) |
| football-data.org API | Free tier (10 req/min) |
| StatsBomb Open Data | Free (open source) |
| Airflow (Docker) | Free (local) |
| GitHub Actions CI | Free (public repo) |
| **Total** | **$0/month** |

## 🗺️ Roadmap

- [x] Medallion architecture (Bronze → Silver → Gold)
- [x] 5 Airflow DAGs with matchday-aware scheduling
- [x] 15 dbt models with 29 tests
- [x] Full 2025-26 season backfill (380 matches)
- [x] SCD Type 2 position tracking
- [x] Rolling form + momentum classification
- [x] Kimball dimensions (teams, matchdays)
- [x] Schema contract validation
- [x] 9-page Next.js dashboard
- [x] 8 REST API endpoints
- [x] Data quality dashboard
- [x] Data lineage visualization
- [x] CI/CD with GitHub Actions
- [x] One-command setup (Makefile)
- [x] 150+ columns fully documented
- [ ] Streaming simulation (WebSocket live score feed)
- [ ] Player profiles with xG and heatmaps
- [ ] Multi-season support (2024-25 + 2025-26)
- [ ] Alerting on quality failures (Slack/email)
- [ ] dbt docs hosted on GitHub Pages

## 📝 License

[MIT](LICENSE)

---

*Built by [Andres Alvarez](https://github.com/StarLord598) — Data Engineering Portfolio Project*
