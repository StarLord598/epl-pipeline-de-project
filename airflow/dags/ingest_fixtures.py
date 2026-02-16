"""
DAG: ingest_fixtures
Ingests EPL fixtures, scores, and match results from football-data.org
Schedule: Every 5 minutes on matchdays, hourly otherwise
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import requests
from airflow.decorators import dag, task
from google.cloud import bigquery

API_BASE = "https://api.football-data.org/v4"
COMPETITION = "PL"  # Premier League
API_KEY = os.environ.get("FOOTBALL_DATA_API_KEY", "")
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
RAW_DATASET = os.environ.get("BQ_RAW_DATASET", "epl_raw")


def _headers() -> dict:
    return {"X-Auth-Token": API_KEY}


@dag(
    dag_id="ingest_fixtures",
    description="Ingest EPL fixtures and results from football-data.org",
    schedule="0 * * * *",  # Hourly default; override to */5 on matchdays
    start_date=datetime(2024, 8, 1),
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "epl-pipeline",
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
    },
    tags=["ingest", "football-data", "fixtures"],
)
def ingest_fixtures():

    @task()
    def extract_fixtures(**context) -> dict:
        """Pull current season fixtures from football-data.org"""
        url = f"{API_BASE}/competitions/{COMPETITION}/matches"
        params = {"season": datetime.now().year}

        response = requests.get(url, headers=_headers(), params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        return {
            "matches": data.get("matches", []),
            "count": data.get("resultSet", {}).get("count", 0),
            "competition": data.get("competition", {}),
            "extracted_at": datetime.utcnow().isoformat(),
        }

    @task()
    def load_to_bigquery(payload: dict, **context):
        """Load raw fixtures JSON into BigQuery bronze layer"""
        client = bigquery.Client(project=PROJECT_ID)
        table_id = f"{PROJECT_ID}.{RAW_DATASET}.fixtures"

        rows = []
        for match in payload["matches"]:
            rows.append(
                {
                    "match_id": match["id"],
                    "matchday": match.get("matchday"),
                    "status": match.get("status"),
                    "utc_date": match.get("utcDate"),
                    "home_team_id": match.get("homeTeam", {}).get("id"),
                    "home_team_name": match.get("homeTeam", {}).get("name"),
                    "away_team_id": match.get("awayTeam", {}).get("id"),
                    "away_team_name": match.get("awayTeam", {}).get("name"),
                    "home_score": match.get("score", {}).get("fullTime", {}).get("home"),
                    "away_score": match.get("score", {}).get("fullTime", {}).get("away"),
                    "winner": match.get("score", {}).get("winner"),
                    "raw_json": json.dumps(match),
                    "ingested_at": payload["extracted_at"],
                }
            )

        if rows:
            errors = client.insert_rows_json(table_id, rows)
            if errors:
                raise Exception(f"BigQuery insert errors: {errors}")

        print(f"Loaded {len(rows)} fixtures to {table_id}")

    data = extract_fixtures()
    load_to_bigquery(data)


ingest_fixtures()
