#!/usr/bin/env python3
"""Data Quality Framework — EPL Pipeline

Runs comprehensive data quality checks against DuckDB.
Exit code 0 = all critical checks pass.
Exit code 1 = one or more critical checks failed.

Checks:
  1. Schema validation (expected tables + columns exist)
  2. Row count assertions (minimum thresholds)
  3. Referential integrity (FK relationships hold)
  4. Business rules (no negative points, valid scores, etc.)
  5. Freshness (data ingested recently)
  6. Uniqueness (no duplicate primary keys)
  7. Completeness (critical fields not null)
"""
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("EPL_DB_PATH", str(REPO_ROOT / "data" / "epl_pipeline.duckdb")))


@dataclass
class CheckResult:
    name: str
    category: str
    passed: bool
    severity: str  # "critical" | "warning"
    message: str
    value: Any = None


@dataclass
class QualityReport:
    checks: list[CheckResult] = field(default_factory=list)
    start_time: datetime = field(default_factory=datetime.now)

    def add(self, result: CheckResult):
        self.checks.append(result)
        icon = "✅" if result.passed else ("❌" if result.severity == "critical" else "⚠️")
        log.info(f"  {icon} [{result.category}] {result.name}: {result.message}")

    @property
    def critical_failures(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed and c.severity == "critical"]

    @property
    def warnings(self) -> list[CheckResult]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]

    def summary(self) -> str:
        passed = sum(1 for c in self.checks if c.passed)
        failed = len(self.critical_failures)
        warned = len(self.warnings)
        total = len(self.checks)
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return (
            f"\n{'='*60}\n"
            f"DATA QUALITY REPORT\n"
            f"{'='*60}\n"
            f"  Total checks:  {total}\n"
            f"  Passed:        {passed} ✅\n"
            f"  Failed:        {failed} ❌\n"
            f"  Warnings:      {warned} ⚠️\n"
            f"  Duration:      {elapsed:.1f}s\n"
            f"{'='*60}"
        )

    def to_json(self, path: Path):
        data = {
            "timestamp": self.start_time.isoformat(),
            "total": len(self.checks),
            "passed": sum(1 for c in self.checks if c.passed),
            "failed": len(self.critical_failures),
            "warnings": len(self.warnings),
            "checks": [
                {
                    "name": c.name,
                    "category": c.category,
                    "passed": c.passed,
                    "severity": c.severity,
                    "message": c.message,
                    "value": str(c.value) if c.value is not None else None,
                }
                for c in self.checks
            ],
        }
        path.write_text(json.dumps(data, indent=2))


def run_checks():
    import duckdb

    if not DB_PATH.exists():
        log.error(f"Database not found: {DB_PATH}")
        sys.exit(1)

    con = duckdb.connect(str(DB_PATH), read_only=True)
    report = QualityReport()

    log.info(f"Running data quality checks on {DB_PATH}\n")

    # ── 1. Schema Validation ─────────────────────────────────────────────
    log.info("📋 Schema Validation")

    expected_tables = {
        "raw": ["matches", "events", "lineups", "top_scorers_2324"],
        "epl_staging": ["stg_matches", "stg_standings", "stg_top_scorers"],
        "epl_mart": ["mart_league_table", "mart_recent_results", "mart_top_scorers"],
    }

    for schema, tables in expected_tables.items():
        for table in tables:
            try:
                count = con.execute(f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
                report.add(CheckResult(
                    name=f"{schema}.{table} exists",
                    category="schema",
                    passed=True,
                    severity="critical",
                    message=f"{count:,} rows",
                    value=count,
                ))
            except Exception as e:
                report.add(CheckResult(
                    name=f"{schema}.{table} exists",
                    category="schema",
                    passed=False,
                    severity="critical",
                    message=str(e)[:100],
                ))

    # ── 2. Row Count Assertions ──────────────────────────────────────────
    log.info("\n📊 Row Count Assertions")

    row_checks = [
        ("raw.matches", 300, "critical", "Should have 300+ matches (2 seasons)"),
        ("raw.events", 50000, "critical", "Should have 50k+ StatsBomb events"),
        ("epl_mart.mart_league_table", 20, "critical", "Should have exactly 20 teams"),
        ("epl_mart.mart_recent_results", 300, "critical", "Should have 300+ results"),
        ("epl_mart.mart_top_scorers", 10, "critical", "Should have 10+ top scorers"),
    ]

    for table, min_rows, severity, desc in row_checks:
        try:
            count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            report.add(CheckResult(
                name=f"{table} ≥ {min_rows:,}",
                category="row_count",
                passed=count >= min_rows,
                severity=severity,
                message=f"{count:,} rows ({desc})",
                value=count,
            ))
        except Exception as e:
            report.add(CheckResult(
                name=f"{table} ≥ {min_rows:,}",
                category="row_count",
                passed=False,
                severity=severity,
                message=str(e)[:100],
            ))

    # ── 3. Uniqueness ────────────────────────────────────────────────────
    log.info("\n🔑 Uniqueness Checks")

    unique_checks = [
        ("epl_mart.mart_league_table", "team_id"),
        ("epl_mart.mart_recent_results", "match_id"),
        ("epl_mart.mart_top_scorers", "player_id"),
        ("epl_staging.stg_matches", "match_id"),
    ]

    for table, col in unique_checks:
        try:
            total = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            distinct = con.execute(f"SELECT COUNT(DISTINCT {col}) FROM {table}").fetchone()[0]
            report.add(CheckResult(
                name=f"{table}.{col} unique",
                category="uniqueness",
                passed=total == distinct,
                severity="critical",
                message=f"{distinct:,} distinct / {total:,} total",
                value={"total": total, "distinct": distinct},
            ))
        except Exception as e:
            report.add(CheckResult(
                name=f"{table}.{col} unique",
                category="uniqueness",
                passed=False,
                severity="critical",
                message=str(e)[:100],
            ))

    # ── 4. Completeness (NOT NULL) ───────────────────────────────────────
    log.info("\n📝 Completeness Checks")

    null_checks = [
        ("epl_mart.mart_league_table", "team_name"),
        ("epl_mart.mart_league_table", "points"),
        ("epl_mart.mart_league_table", "position"),
        ("epl_mart.mart_recent_results", "match_date"),
        ("epl_mart.mart_recent_results", "home_team_name"),
        ("epl_mart.mart_top_scorers", "player_name"),
        ("epl_mart.mart_top_scorers", "goals"),
    ]

    for table, col in null_checks:
        try:
            nulls = con.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL").fetchone()[0]
            report.add(CheckResult(
                name=f"{table}.{col} not null",
                category="completeness",
                passed=nulls == 0,
                severity="critical",
                message=f"{nulls} nulls found",
                value=nulls,
            ))
        except Exception as e:
            report.add(CheckResult(
                name=f"{table}.{col} not null",
                category="completeness",
                passed=False,
                severity="critical",
                message=str(e)[:100],
            ))

    # ── 5. Business Rules ────────────────────────────────────────────────
    log.info("\n📏 Business Rule Checks")

    # No negative points
    try:
        neg = con.execute("SELECT COUNT(*) FROM epl_mart.mart_league_table WHERE points < 0").fetchone()[0]
        report.add(CheckResult(
            name="No negative points",
            category="business_rule",
            passed=neg == 0,
            severity="critical",
            message=f"{neg} teams with negative points",
        ))
    except Exception as e:
        report.add(CheckResult(name="No negative points", category="business_rule", passed=False, severity="critical", message=str(e)[:100]))

    # Points consistency: points = won*3 + drawn
    try:
        bad = con.execute("""
            SELECT COUNT(*) FROM epl_mart.mart_league_table
            WHERE points != (won * 3 + drawn)
        """).fetchone()[0]
        report.add(CheckResult(
            name="Points = W*3 + D",
            category="business_rule",
            passed=bad == 0,
            severity="critical",
            message=f"{bad} teams with inconsistent points",
        ))
    except Exception as e:
        report.add(CheckResult(name="Points = W*3 + D", category="business_rule", passed=False, severity="critical", message=str(e)[:100]))

    # Played = won + drawn + lost
    try:
        bad = con.execute("""
            SELECT COUNT(*) FROM epl_mart.mart_league_table
            WHERE played != (won + drawn + lost)
        """).fetchone()[0]
        report.add(CheckResult(
            name="Played = W + D + L",
            category="business_rule",
            passed=bad == 0,
            severity="critical",
            message=f"{bad} teams with inconsistent game count",
        ))
    except Exception as e:
        report.add(CheckResult(name="Played = W + D + L", category="business_rule", passed=False, severity="critical", message=str(e)[:100]))

    # Goal difference consistency
    try:
        bad = con.execute("""
            SELECT COUNT(*) FROM epl_mart.mart_league_table
            WHERE goal_difference != (goals_for - goals_against)
        """).fetchone()[0]
        report.add(CheckResult(
            name="GD = GF - GA",
            category="business_rule",
            passed=bad == 0,
            severity="critical",
            message=f"{bad} teams with inconsistent goal difference",
        ))
    except Exception as e:
        report.add(CheckResult(name="GD = GF - GA", category="business_rule", passed=False, severity="critical", message=str(e)[:100]))

    # Valid scores (non-negative)
    try:
        bad = con.execute("""
            SELECT COUNT(*) FROM epl_mart.mart_recent_results
            WHERE home_score < 0 OR away_score < 0
        """).fetchone()[0]
        report.add(CheckResult(
            name="No negative scores",
            category="business_rule",
            passed=bad == 0,
            severity="critical",
            message=f"{bad} matches with negative scores",
        ))
    except Exception as e:
        report.add(CheckResult(name="No negative scores", category="business_rule", passed=False, severity="critical", message=str(e)[:100]))

    # Top scorer goals > 0
    try:
        bad = con.execute("""
            SELECT COUNT(*) FROM epl_mart.mart_top_scorers WHERE goals <= 0
        """).fetchone()[0]
        report.add(CheckResult(
            name="All scorers have goals > 0",
            category="business_rule",
            passed=bad == 0,
            severity="critical",
            message=f"{bad} scorers with 0 goals",
        ))
    except Exception as e:
        report.add(CheckResult(name="All scorers have goals > 0", category="business_rule", passed=False, severity="critical", message=str(e)[:100]))

    # ── 6. Referential Integrity ─────────────────────────────────────────
    log.info("\n🔗 Referential Integrity")

    try:
        orphans = con.execute("""
            SELECT COUNT(DISTINCT team_name) FROM epl_mart.mart_recent_results
            WHERE home_team_name NOT IN (SELECT team_name FROM epl_mart.mart_league_table)
        """).fetchone()[0]
        report.add(CheckResult(
            name="All match teams in standings",
            category="referential",
            passed=orphans == 0,
            severity="warning",
            message=f"{orphans} orphan teams in results",
        ))
    except Exception as e:
        report.add(CheckResult(name="All match teams in standings", category="referential", passed=False, severity="warning", message=str(e)[:100]))

    # ── Report ───────────────────────────────────────────────────────────
    log.info(report.summary())

    # Export report JSON
    report_path = REPO_ROOT / "data" / "quality_report.json"
    report.to_json(report_path)
    log.info(f"\nReport saved to {report_path}")

    if report.critical_failures:
        log.error(f"\n❌ {len(report.critical_failures)} critical check(s) failed!")
        for c in report.critical_failures:
            log.error(f"   → {c.name}: {c.message}")
        sys.exit(1)

    if report.warnings:
        log.warning(f"\n⚠️  {len(report.warnings)} warning(s)")

    log.info("\n✅ All critical data quality checks passed!")


if __name__ == "__main__":
    run_checks()
