from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="live_poll_15m",
    start_date=datetime(2026, 2, 20),
    schedule="*/15 * * * *",
    catchup=False,
    tags=["live", "epl", "portfolio"],
) as dag:
    fetch_matches_live = BashOperator(
        task_id="fetch_matches_live",
        bash_command="cd /opt/airflow && python scripts/ingest_live_matches.py ",
    )

    fetch_standings_live = BashOperator(
        task_id="fetch_standings_live",
        bash_command="cd /opt/airflow && python scripts/ingest_live_standings.py ",
    )

    validate_raw_payloads = BashOperator(
        task_id="validate_raw_payloads",
        bash_command="cd /opt/airflow && python scripts/validate_live_payloads.py ",
    )

    run_dbt_live_silver = BashOperator(
        task_id="run_dbt_live_silver",
        bash_command="cd /opt/airflow/dbt && dbt run --select silver_live_match_state ",
    )

    run_monitoring_checks = BashOperator(
        task_id="run_monitoring_checks",
        bash_command="cd /opt/airflow && python scripts/check_live_freshness.py ",
    )

    export_live_json = BashOperator(
        task_id="export_live_json",
        bash_command="cd /opt/airflow && python scripts/export_live_json.py || true ",
    )

    fetch_matches_live >> fetch_standings_live >> validate_raw_payloads >> run_dbt_live_silver >> run_monitoring_checks >> export_live_json
