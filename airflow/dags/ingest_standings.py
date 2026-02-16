"""
DAG: ingest_standings
Ingests EPL league table/standings from football-data.org
Schedule: Every 2 hours
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import requests
from airflow.decorators import dag, task
from google.cloud import bigquery

API_BASE = "https://api.football-data.org/v4"
COMPETITION = "PL"
API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
RAW_DATASET = os.environ.get("BQ_RAW_DATASET", "epl_raw")


@dag(
    dag_id="ingest_standings",
    description="Ingest EPL standings from football-data.org",
    schedule="0 */2 * * *",
    start_date=datetime(2024, 8, 1),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "epl-pipeline",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["ingest", "football-data", "standings"],
)
def ingest_standings():

    @task()
    def extract_standings() -> dict:
        url = f"{API_BASE}/competitions/{COMPETITION}/standings"
        response = requests.get(
            url, headers={"X-Auth-Token": API_KEY}, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return {
            "standings": data.get("standings", []),
            "season": data.get("season", {}),
            "extracted_at": datetime.utcnow().isoformat(),
        }

    @task()
    def load_to_bigquery(payload: dict):
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.{RAW_DATASET}.standings"

        rows = []
        for standing_type in payload["standings"]:
            for entry in standing_type.get("table", []):
                rows.append(
                    {
                        "team_id": entry["team"]["id"],
                        "team_name": entry["team"]["name"],
                        "team_crest": entry["team"].get("crest", ""),
                        "position": entry["position"],
                        "played_games": entry["playedGames"],
                        "won": entry["won"],
                        "draw": entry["draw"],
                        "lost": entry["lost"],
                        "points": entry["points"],
                        "goals_for": entry["goalsFor"],
                        "goals_against": entry["goalsAgainst"],
                        "goal_difference": entry["goalDifference"],
                        "form": entry.get("form"),
                        "standing_type": standing_type.get("type", "TOTAL"),
                        "season_start": payload["season"].get("startDate"),
                        "season_end": payload["season"].get("endDate"),
                        "matchday": payload["season"].get("currentMatchday"),
                        "raw_json": json.dumps(entry),
                        "ingested_at": payload["extracted_at"],
                    }
                )

        if rows:
            errors = client.insert_rows_json(table_id, rows)
            if errors:
                raise Exception(f"BigQuery insert errors: {errors}")

        print(f"Loaded {len(rows)} standings rows to {table_id}")

    data = extract_standings()
    load_to_bigquery(data)


ingest_standings()
