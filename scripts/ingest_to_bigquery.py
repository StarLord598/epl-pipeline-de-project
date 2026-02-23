#!/usr/bin/env python3
"""
EPL Pipeline - BigQuery Ingestion Script
=========================================
Loads EPL 2023-24 season data into BigQuery:
  - 380 matches from football-data.co.uk (free, no auth)
  - Real 2023-24 top scorers (known stats)
  - StatsBomb Arsenal 2003/04 events & lineups

Target: project=your-gcp-project-id, dataset=epl_raw

Usage:
    export GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-service-account.json
    python3 scripts/ingest_to_bigquery.py
"""

import os
import sys
import logging
import requests
import pandas as pd
from datetime import timezone
from io import StringIO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────────
PROJECT_ID       = "your-gcp-project-id"
DATASET_RAW      = "epl_raw"
SEASON_ID        = 2324
COMPETITION_ID   = 2021
COMPETITION_NAME = "Premier League"
SEASON_NAME      = "2023/2024"

FOOTBALL_DATA_CSV_URL    = "https://www.football-data.co.uk/mmz4281/2324/E0.csv"
STATSBOMB_COMPETITION_ID = 2
STATSBOMB_SEASON_ID      = 44

NOW = pd.Timestamp.now(tz="UTC")   # timezone-aware — pyarrow handles TIMESTAMP correctly


def get_bq_client():
    from google.cloud import bigquery
    return bigquery.Client(project=PROJECT_ID)


# ── Helpers ──────────────────────────────────────────────────────────────────────

def load_job(client, df, table_path, schema):
    from google.cloud import bigquery
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        time_partitioning=bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="ingested_at",
        ),
    )
    job = client.load_table_from_dataframe(
        df, f"{PROJECT_ID}.{table_path}", job_config=job_config
    )
    job.result()


# ── 1. Matches ───────────────────────────────────────────────────────────────────

def load_matches(client):
    log.info("Downloading EPL 2023-24 CSV from football-data.co.uk…")
    r = requests.get(FOOTBALL_DATA_CSV_URL, timeout=30)
    r.raise_for_status()
    df_raw = pd.read_csv(StringIO(r.text))
    log.info(f"  {len(df_raw)} rows downloaded")

    # Consistent team_id map (alphabetical)
    all_teams = sorted(set(df_raw["HomeTeam"].tolist() + df_raw["AwayTeam"].tolist()))
    team_id_map = {t: i + 1 for i, t in enumerate(all_teams)}

    rows = []
    for idx, row in df_raw.iterrows():
        date_str = str(row.get("Date", "")).strip()
        try:
            match_date = pd.to_datetime(date_str, dayfirst=True).date()
        except Exception:
            match_date = None

        home_score = int(row["FTHG"]) if pd.notna(row.get("FTHG")) else None
        away_score = int(row["FTAG"]) if pd.notna(row.get("FTAG")) else None
        matchday   = (idx // 10) + 1

        rows.append({
            "match_id":         idx + 10000,
            "competition_id":   COMPETITION_ID,
            "competition_name": COMPETITION_NAME,
            "season_id":        SEASON_ID,
            "season_name":      SEASON_NAME,
            "match_date":       match_date,
            "kick_off":         str(row.get("Time", "15:00")).strip(),
            "home_team_id":     team_id_map[str(row["HomeTeam"]).strip()],
            "home_team_name":   str(row["HomeTeam"]).strip(),
            "away_team_id":     team_id_map[str(row["AwayTeam"]).strip()],
            "away_team_name":   str(row["AwayTeam"]).strip(),
            "home_score":       home_score,
            "away_score":       away_score,
            "match_status":     "available" if home_score is not None else "scheduled",
            "matchday":         matchday,
            "ingested_at":      NOW,
        })

    df = pd.DataFrame(rows)
    df["match_date"]  = pd.to_datetime(df["match_date"]).dt.date
    df["ingested_at"] = pd.to_datetime(df["ingested_at"], utc=True)
    # Ensure nullable integers (BigQuery accepts pd.Int64Dtype)
    for col in ["home_score", "away_score", "matchday"]:
        df[col] = df[col].astype(pd.Int64Dtype())

    from google.cloud import bigquery
    F = bigquery.SchemaField
    schema = [
        F("match_id",         "INTEGER", mode="REQUIRED"),
        F("competition_id",   "INTEGER"),
        F("competition_name", "STRING"),
        F("season_id",        "INTEGER"),
        F("season_name",      "STRING"),
        F("match_date",       "DATE"),
        F("kick_off",         "STRING"),
        F("home_team_id",     "INTEGER"),
        F("home_team_name",   "STRING"),
        F("away_team_id",     "INTEGER"),
        F("away_team_name",   "STRING"),
        F("home_score",       "INTEGER"),
        F("away_score",       "INTEGER"),
        F("match_status",     "STRING"),
        F("matchday",         "INTEGER"),
        F("ingested_at",      "TIMESTAMP", mode="REQUIRED"),
    ]

    log.info(f"  Loading {len(df)} rows → epl_raw.matches…")
    load_job(client, df, "epl_raw.matches", schema)
    log.info(f"  ✓ {len(df)} matches loaded  ({len(all_teams)} teams)")
    return df, team_id_map


# ── 2. Top Scorers ───────────────────────────────────────────────────────────────

def load_top_scorers(client):
    log.info("Loading 2023-24 top scorers…")

    data = [
        (1,  1001, "Erling Haaland",    "Manchester City",    27, 5,  31),
        (2,  1002, "Cole Palmer",       "Chelsea",            22, 11, 33),
        (3,  1003, "Alexander Isak",    "Newcastle United",   21, 2,  30),
        (4,  1004, "Jarrod Bowen",      "West Ham United",    20, 8,  38),
        (5,  1005, "Ollie Watkins",     "Aston Villa",        19, 13, 37),
        (6,  1006, "Son Heung-min",     "Tottenham Hotspur",  17, 10, 38),
        (7,  1007, "Dominic Solanke",   "Bournemouth",        19, 4,  38),
        (8,  1008, "Phil Foden",        "Manchester City",    19, 8,  35),
        (9,  1009, "Mohamed Salah",     "Liverpool",          18, 10, 32),
        (10, 1010, "Bukayo Saka",       "Arsenal",            16, 9,  35),
        (11, 1011, "Gabriel Martinelli","Arsenal",            11, 5,  35),
        (12, 1012, "Nicolas Jackson",   "Chelsea",            14, 4,  32),
        (13, 1013, "Brennan Johnson",   "Tottenham Hotspur",  13, 2,  37),
        (14, 1014, "Bryan Mbeumo",      "Brentford",          13, 5,  38),
        (15, 1015, "Yoane Wissa",       "Brentford",          13, 3,  34),
        (16, 1016, "Harvey Barnes",     "Newcastle United",   13, 5,  33),
        (17, 1017, "Darwin Nunez",      "Liverpool",          11, 8,  32),
        (18, 1018, "Callum Wilson",     "Newcastle United",   11, 1,  20),
        (19, 1019, "Leandro Trossard",  "Arsenal",            12, 6,  33),
        (20, 1020, "Marcus Rashford",   "Manchester United",  8,  5,  25),
    ]

    rows = [{
        "rank": r, "player_id": pid, "player_name": name, "team_name": team,
        "goals": g, "assists": a, "goal_contributions": g + a,
        "matches_played": mp,
        "goals_per_game":   round(g / mp, 3),
        "assists_per_game": round(a / mp, 3),
        "ingested_at": NOW,
    } for r, pid, name, team, g, a, mp in data]

    df = pd.DataFrame(rows)
    df["ingested_at"] = pd.to_datetime(df["ingested_at"], utc=True)

    from google.cloud import bigquery
    F = bigquery.SchemaField
    schema = [
        F("rank",               "INTEGER"),
        F("player_id",          "INTEGER", mode="REQUIRED"),
        F("player_name",        "STRING"),
        F("team_name",          "STRING"),
        F("goals",              "INTEGER"),
        F("assists",            "INTEGER"),
        F("goal_contributions", "INTEGER"),
        F("matches_played",     "INTEGER"),
        F("goals_per_game",     "FLOAT64"),
        F("assists_per_game",   "FLOAT64"),
        F("ingested_at",        "TIMESTAMP", mode="REQUIRED"),
    ]

    log.info(f"  Loading {len(df)} rows → epl_raw.top_scorers…")
    load_job(client, df, "epl_raw.top_scorers", schema)
    log.info(f"  ✓ {len(df)} top scorers loaded")


# ── 3. StatsBomb Events ──────────────────────────────────────────────────────────

def load_statsbomb_events(client):
    log.info("Loading StatsBomb events (Arsenal 2003/04)…")
    try:
        import statsbombpy.sb as sb
    except ImportError:
        log.warning("  statsbombpy not installed — skipping events")
        return

    from google.cloud import bigquery
    F = bigquery.SchemaField

    matches = sb.matches(competition_id=STATSBOMB_COMPETITION_ID, season_id=STATSBOMB_SEASON_ID)
    match_ids = matches["match_id"].tolist()
    log.info(f"  {len(match_ids)} matches found")

    all_rows = []
    for i, mid in enumerate(match_ids):
        if i % 5 == 0:
            log.info(f"  Fetching events {i+1}/{len(match_ids)}…")
        try:
            ev = sb.events(match_id=mid)
            for _, e in ev.iterrows():
                loc = e.get("location") or []
                team = e.get("team") or {}
                plyr = e.get("player") or {}
                pos  = e.get("position") or {}
                etype = e.get("type") or {}

                all_rows.append({
                    "event_id":      str(e.get("id", "")),
                    "match_id":      int(mid),
                    "index_num":     int(e["index"])    if pd.notna(e.get("index"))  else None,
                    "period":        int(e["period"])   if pd.notna(e.get("period")) else None,
                    "minute":        int(e["minute"])   if pd.notna(e.get("minute")) else None,
                    "second":        int(e["second"])   if pd.notna(e.get("second")) else None,
                    "event_type":    str(etype.get("name", "")) if isinstance(etype, dict) else str(etype or ""),
                    "team_id":       int(team["id"])    if isinstance(team, dict) and "id"   in team else None,
                    "team_name":     str(team["name"])  if isinstance(team, dict) and "name" in team else str(team or ""),
                    "player_id":     int(plyr["id"])    if isinstance(plyr, dict) and "id"   in plyr else None,
                    "player_name":   str(plyr["name"])  if isinstance(plyr, dict) and "name" in plyr else None,
                    "position_name": str(pos["name"])   if isinstance(pos, dict)  and "name" in pos  else None,
                    "location_x":   float(loc[0])       if isinstance(loc, list)  and len(loc) > 0   else None,
                    "location_y":   float(loc[1])       if isinstance(loc, list)  and len(loc) > 1   else None,
                    "sub_type":      None,
                    "outcome":       None,
                    "ingested_at":   NOW,
                })
        except Exception as ex:
            log.warning(f"  match {mid}: {ex}")

    if not all_rows:
        log.warning("  No events — skipping")
        return

    df = pd.DataFrame(all_rows)
    df["ingested_at"] = pd.to_datetime(df["ingested_at"], utc=True)
    for col in ["index_num", "period", "minute", "second", "team_id", "player_id"]:
        df[col] = df[col].astype(pd.Int64Dtype())

    schema = [
        F("event_id",      "STRING",  mode="REQUIRED"),
        F("match_id",      "INTEGER", mode="REQUIRED"),
        F("index_num",     "INTEGER"),
        F("period",        "INTEGER"),
        F("minute",        "INTEGER"),
        F("second",        "INTEGER"),
        F("event_type",    "STRING"),
        F("team_id",       "INTEGER"),
        F("team_name",     "STRING"),
        F("player_id",     "INTEGER"),
        F("player_name",   "STRING"),
        F("position_name", "STRING"),
        F("location_x",    "FLOAT64"),
        F("location_y",    "FLOAT64"),
        F("sub_type",      "STRING"),
        F("outcome",       "STRING"),
        F("ingested_at",   "TIMESTAMP", mode="REQUIRED"),
    ]

    log.info(f"  Loading {len(df):,} rows → epl_raw.events…")
    load_job(client, df, "epl_raw.events", schema)
    log.info(f"  ✓ {len(df):,} events loaded")


# ── 4. Quality Checks ────────────────────────────────────────────────────────────

def run_qc(client):
    log.info("Running quality checks…")
    checks = [
        ("Matches",         f"SELECT COUNT(*) FROM `{PROJECT_ID}.epl_raw.matches`"),
        ("Teams",           f"SELECT COUNT(DISTINCT home_team_name) FROM `{PROJECT_ID}.epl_raw.matches`"),
        ("Top scorers",     f"SELECT COUNT(*) FROM `{PROJECT_ID}.epl_raw.top_scorers`"),
        ("Max goals",       f"SELECT MAX(goals) FROM `{PROJECT_ID}.epl_raw.top_scorers`"),
        ("Events",          f"SELECT COUNT(*) FROM `{PROJECT_ID}.epl_raw.events`"),
    ]
    all_ok = True
    for label, sql in checks:
        try:
            val = list(client.query(sql).result())[0][0]
            log.info(f"  ✓ {label}: {val:,}" if isinstance(val, int) else f"  ✓ {label}: {val}")
        except Exception as e:
            log.error(f"  ✗ {label}: {e}")
            all_ok = False
    return all_ok


# ── Main ─────────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("EPL Pipeline → BigQuery Ingestion")
    log.info(f"Project: {PROJECT_ID}   Dataset: {DATASET_RAW}")
    log.info("=" * 60)

    client = get_bq_client()
    log.info("✓ BigQuery client initialized")

    load_matches(client)
    load_top_scorers(client)
    load_statsbomb_events(client)

    ok = run_qc(client)

    log.info("=" * 60)
    if ok:
        log.info("✅  All loads complete — BigQuery populated!")
    else:
        log.warning("⚠️  Some checks failed")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
