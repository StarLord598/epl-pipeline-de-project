"""
DAG: ingest_player_stats
Ingests EPL top scorers and player statistics from football-data.org
Schedule: Daily at 06:00 UTC
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
    dag_id="ingest_player_stats",
    description="Ingest EPL top scorers from football-data.org",
    schedule="0 6 * * *",
    start_date=datetime(2024, 8, 1),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "epl-pipeline",
        "retries": 2,
        "retry_delay": timedelta(minutes=5),
    },
    tags=["ingest", "football-data", "players"],
)
def ingest_player_stats():

    @task()
    def extract_scorers() -> dict:
        url = f"{API_BASE}/competitions/{COMPETITION}/scorers"
        params = {"limit": 100}
        response = requests.get(
            url, headers={"X-Auth-Token": API_KEY}, params=params, timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return {
            "scorers": data.get("scorers", []),
            "season": data.get("season", {}),
            "extracted_at": datetime.utcnow().isoformat(),
        }

    @task()
    def load_to_bigquery(payload: dict):
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.{RAW_DATASET}.top_scorers"

        rows = []
        for scorer in payload["scorers"]:
            player = scorer.get("player", {})
            team = scorer.get("team", {})
            rows.append(
                {
                    "player_id": player.get("id"),
                    "player_name": player.get("name"),
                    "nationality": player.get("nationality"),
                    "position": player.get("position"),
                    "date_of_birth": player.get("dateOfBirth"),
                    "team_id": team.get("id"),
                    "team_name": team.get("name"),
                    "played_matches": scorer.get("playedMatches"),
                    "goals": scorer.get("goals"),
                    "assists": scorer.get("assists"),
                    "penalties": scorer.get("penalties"),
                    "season_start": payload["season"].get("startDate"),
                    "matchday": payload["season"].get("currentMatchday"),
                    "raw_json": json.dumps(scorer),
                    "ingested_at": payload["extracted_at"],
                }
            )

        if rows:
            errors = client.insert_rows_json(table_id, rows)
            if errors:
                raise Exception(f"BigQuery insert errors: {errors}")

        print(f"Loaded {len(rows)} scorer rows to {table_id}")

    data = extract_scorers()
    load_to_bigquery(data)


ingest_player_stats()
