#!/usr/bin/env python3
"""Validate that live ingestion produced usable payloads recently."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from live_common import ensure_live_tables, get_conn, log_run


def main() -> None:
    conn = get_conn()
    ensure_live_tables(conn)

    cutoff = datetime.now(UTC) - timedelta(hours=2)
    live_matches = conn.execute(
        "SELECT COUNT(*) FROM raw.live_matches WHERE ingested_at >= ?", [cutoff]
    ).fetchone()[0]
    live_standings = conn.execute(
        "SELECT COUNT(*) FROM raw.live_standings WHERE ingested_at >= ?", [cutoff]
    ).fetchone()[0]

    if live_matches <= 0:
        log_run(conn, "validate_live_payloads", "failed", "No live_matches in last 2h", 0)
        raise SystemExit("Validation failed: no live match rows in last 2h")

    if live_standings <= 0:
        log_run(conn, "validate_live_payloads", "failed", "No live_standings in last 2h", 0)
        raise SystemExit("Validation failed: no live standings rows in last 2h")

    log_run(
        conn,
        "validate_live_payloads",
        "success",
        f"matches={live_matches}, standings={live_standings}",
        live_matches + live_standings,
    )
    print(f"[VALIDATE] matches={live_matches} standings={live_standings} (last 2h)")
    conn.close()


if __name__ == "__main__":
    main()
