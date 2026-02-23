#!/usr/bin/env python3
"""
Export BigQuery mart tables → JSON for Next.js dashboard
=========================================================
Reads from epl_mart (Gold layer) and writes to dashboard/public/data/

Usage:
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/epl-pipeline-sa.json
    python3 scripts/export_to_json.py
"""

import os
import json
import logging
from pathlib import Path
from datetime import date, datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

PROJECT_ID  = "your-gcp-project-id"
DATASET_RAW = "epl_raw"
DATASET_MART = "epl_mart"

REPO_ROOT  = Path(__file__).resolve().parents[1]
DASH_DATA  = REPO_ROOT / "dashboard" / "public" / "data"
DASH_DATA.mkdir(parents=True, exist_ok=True)


def json_serial(obj):
    """JSON serializer for datetime/date objects."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def get_bq_client():
    from google.cloud import bigquery
    return bigquery.Client(project=PROJECT_ID)


def bq_to_records(client, sql: str) -> list[dict]:
    """Run a BigQuery query and return rows as list of dicts."""
    result = client.query(sql).result()
    return [dict(row) for row in result]


def export_league_table(client):
    sql = f"""
    SELECT
        position, team_id, team_name,
        played, won, drawn, lost, points,
        goals_for, goals_against, goal_difference,
        points_pct, win_rate,
        goals_per_game, goals_conceded_per_game,
        qualification_zone
    FROM `{PROJECT_ID}.{DATASET_MART}.mart_league_table`
    ORDER BY position
    """
    rows = bq_to_records(client, sql)
    out = DASH_DATA / "league_table.json"
    out.write_text(json.dumps(rows, indent=2, default=json_serial))
    log.info(f"  ✓ league_table.json ({len(rows)} teams)")
    return rows


def export_recent_results(client):
    sql = f"""
    SELECT
        match_id, matchday, match_date,
        home_team_name, away_team_name,
        home_score, away_score, winner,
        home_result, away_result
    FROM `{PROJECT_ID}.{DATASET_MART}.mart_recent_results`
    ORDER BY match_date DESC, matchday DESC
    LIMIT 380
    """
    rows = bq_to_records(client, sql)
    out = DASH_DATA / "recent_results.json"
    out.write_text(json.dumps(rows, indent=2, default=json_serial))
    log.info(f"  ✓ recent_results.json ({len(rows)} matches)")
    return rows


def export_top_scorers(client):
    sql = f"""
    SELECT
        rank, player_id, player_name, team_name,
        goals, assists, goal_contributions,
        matches_played, goals_per_game, assists_per_game
    FROM `{PROJECT_ID}.{DATASET_MART}.mart_top_scorers`
    ORDER BY rank
    LIMIT 20
    """
    rows = bq_to_records(client, sql)
    out = DASH_DATA / "top_scorers.json"
    out.write_text(json.dumps(rows, indent=2, default=json_serial))
    log.info(f"  ✓ top_scorers.json ({len(rows)} scorers)")
    return rows


def export_matches(client):
    sql = f"""
    SELECT
        match_id, matchday, match_date,
        home_team_name, away_team_name,
        home_score, away_score, winner, match_status
    FROM `{PROJECT_ID}.{DATASET_RAW}.matches`
    WHERE season_id = 2324
    ORDER BY match_date DESC
    """
    rows = bq_to_records(client, sql)
    out = DASH_DATA / "matches.json"
    out.write_text(json.dumps(rows, indent=2, default=json_serial))
    log.info(f"  ✓ matches.json ({len(rows)} rows)")
    return rows


def main():
    log.info("Exporting BigQuery → dashboard JSON…")
    client = get_bq_client()

    export_league_table(client)
    export_recent_results(client)
    export_top_scorers(client)
    export_matches(client)

    log.info(f"✅ All exports written to {DASH_DATA}")


if __name__ == "__main__":
    main()
