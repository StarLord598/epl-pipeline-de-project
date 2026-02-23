"""
EPL Analytics Pipeline — BigQuery DAG
======================================
Runs on schedule (daily at 06:00 UTC), orchestrates:
  1. Ingest raw data → BigQuery epl_raw
  2. dbt run → transforms to epl_staging + epl_mart
  3. dbt test → data quality checks
  4. Export JSON → Next.js dashboard static files

Can also be run standalone (no Airflow needed):
    python3 airflow/dags/epl_bigquery_pipeline.py
"""

import os
import sys
import json
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path

log = logging.getLogger(__name__)

REPO_ROOT   = Path(__file__).resolve().parents[2]
DBT_DIR     = REPO_ROOT / "dbt"
SCRIPTS_DIR = REPO_ROOT / "scripts"
DASH_DATA   = REPO_ROOT / "dashboard" / "public" / "data"
SA_KEY      = REPO_ROOT / "keys" / "epl-pipeline-sa.json"

ENV = {
    **os.environ,
    "GOOGLE_APPLICATION_CREDENTIALS": str(SA_KEY),
    "GOOGLE_CLOUD_PROJECT": "your-gcp-project-id",
}

# ── Try to import Airflow (optional) ────────────────────────────────────────────
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.bash import BashOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False


# ── Pipeline Steps ───────────────────────────────────────────────────────────────

def step_ingest(**ctx):
    """Step 1: Ingest data into BigQuery raw layer."""
    log.info("▶ Step 1: Ingesting data into BigQuery…")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "ingest_to_bigquery.py")],
        env=ENV,
        capture_output=False,
        check=True,
        cwd=str(REPO_ROOT),
    )
    log.info("✓ Ingestion complete")


def step_dbt_run(**ctx):
    """Step 2: Run dbt transformations."""
    log.info("▶ Step 2: Running dbt models…")
    result = subprocess.run(
        ["python3", "-m", "dbt", "run", "--profiles-dir", "."],
        env={**ENV, "GOOGLE_APPLICATION_CREDENTIALS": str(SA_KEY)},
        capture_output=False,
        check=True,
        cwd=str(DBT_DIR),
    )
    log.info("✓ dbt run complete")


def step_dbt_test(**ctx):
    """Step 3: Run dbt tests."""
    log.info("▶ Step 3: Running dbt tests…")
    subprocess.run(
        ["python3", "-m", "dbt", "test", "--profiles-dir", "."],
        env={**ENV, "GOOGLE_APPLICATION_CREDENTIALS": str(SA_KEY)},
        capture_output=False,
        check=True,
        cwd=str(DBT_DIR),
    )
    log.info("✓ dbt tests passed")


def step_export_json(**ctx):
    """Step 4: Export BigQuery mart tables to JSON for the Next.js dashboard."""
    log.info("▶ Step 4: Exporting mart data to JSON…")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / "export_to_json.py")],
        env=ENV,
        capture_output=False,
        check=True,
        cwd=str(REPO_ROOT),
    )
    log.info("✓ JSON export complete")


# ── Airflow DAG definition ───────────────────────────────────────────────────────

if AIRFLOW_AVAILABLE:
    default_args = {
        "owner":            "epl-pipeline",
        "depends_on_past":  False,
        "start_date":       datetime(2024, 8, 1),
        "email_on_failure": False,
        "email_on_retry":   False,
        "retries":          1,
        "retry_delay":      timedelta(minutes=5),
    }

    with DAG(
        dag_id="epl_bigquery_pipeline",
        description="EPL Analytics Pipeline — BigQuery Medallion Architecture",
        default_args=default_args,
        schedule_interval="0 6 * * *",      # 06:00 UTC daily
        catchup=False,
        tags=["epl", "bigquery", "dbt", "production"],
        doc_md=__doc__,
    ) as dag:

        t_ingest = PythonOperator(
            task_id="ingest_raw_data",
            python_callable=step_ingest,
        )

        t_dbt_run = PythonOperator(
            task_id="dbt_run",
            python_callable=step_dbt_run,
        )

        t_dbt_test = PythonOperator(
            task_id="dbt_test",
            python_callable=step_dbt_test,
        )

        t_export = PythonOperator(
            task_id="export_json",
            python_callable=step_export_json,
        )

        t_ingest >> t_dbt_run >> t_dbt_test >> t_export


# ── Standalone runner ────────────────────────────────────────────────────────────

def run_standalone():
    """Run the full pipeline without Airflow."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)s  %(message)s",
        datefmt="%H:%M:%S",
    )

    print("=" * 60)
    print("EPL Pipeline — Standalone Mode (no Airflow)")
    print("=" * 60)

    steps = [
        ("Ingest raw data",    step_ingest),
        ("dbt run",            step_dbt_run),
        ("dbt test",           step_dbt_test),
        ("Export JSON",        step_export_json),
    ]

    for name, fn in steps:
        print(f"\n── {name} ──")
        try:
            fn()
            print(f"  ✓ {name} complete")
        except Exception as e:
            print(f"  ✗ {name} FAILED: {e}")
            raise

    print("\n" + "=" * 60)
    print("✅ Full pipeline complete!")
    print("=" * 60)


if __name__ == "__main__":
    run_standalone()
