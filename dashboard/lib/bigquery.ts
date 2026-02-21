/**
 * BigQuery client for the EPL Dashboard
 * =========================================
 * Server-side only — used in Next.js API routes & Server Components.
 * Authenticates via GOOGLE_APPLICATION_CREDENTIALS env var (SA key).
 *
 * Falls back to local JSON files if BQ is unavailable (dev / offline).
 */

import { BigQuery } from "@google-cloud/bigquery";
import path from "path";
import fs from "fs";

export const PROJECT_ID   = process.env.GCP_PROJECT_ID   ?? "cedar-style-487221-a3";
export const DATASET_RAW  = process.env.BQ_RAW_DATASET   ?? "epl_raw";
export const DATASET_MART = process.env.BQ_MART_DATASET  ?? "epl_mart";

let _client: BigQuery | null = null;

export function getBQClient(): BigQuery {
  if (_client) return _client;

  const keyFile = process.env.GOOGLE_APPLICATION_CREDENTIALS;
  _client = new BigQuery({
    projectId: PROJECT_ID,
    ...(keyFile ? { keyFilename: keyFile } : {}),
  });
  return _client;
}

/** Run a SQL query and return rows as plain objects. */
export async function query<T = Record<string, unknown>>(sql: string): Promise<T[]> {
  const bq = getBQClient();
  const [rows] = await bq.query({ query: sql, location: "US" });
  return rows as T[];
}

/** Read a local JSON fallback file. */
function readLocal<T>(filename: string): T[] {
  const p = path.join(process.cwd(), "public", "data", filename);
  if (fs.existsSync(p)) {
    return JSON.parse(fs.readFileSync(p, "utf-8")) as T[];
  }
  return [];
}

// ── Typed query helpers ─────────────────────────────────────────────────────────

export async function getLeagueTable() {
  try {
    return await query(`
      SELECT
        position, team_id, team_name,
        played, won, drawn, lost, points,
        goals_for, goals_against, goal_difference,
        ROUND(points_pct, 1)                AS points_pct,
        ROUND(win_rate, 1)                  AS win_rate,
        ROUND(goals_per_game, 2)            AS goals_per_game,
        ROUND(goals_conceded_per_game, 2)   AS goals_conceded_per_game,
        qualification_zone
      FROM \`${PROJECT_ID}.${DATASET_MART}.mart_league_table\`
      ORDER BY position
    `);
  } catch (e) {
    console.warn("[BQ] league_table fallback →", (e as Error).message);
    return readLocal("league_table.json");
  }
}

export async function getRecentResults(limit = 380) {
  try {
    return await query(`
      SELECT
        match_id, matchday, match_date,
        home_team_name, away_team_name,
        home_score, away_score, winner,
        home_result, away_result
      FROM \`${PROJECT_ID}.${DATASET_MART}.mart_recent_results\`
      ORDER BY match_date DESC
      LIMIT ${limit}
    `);
  } catch (e) {
    console.warn("[BQ] recent_results fallback →", (e as Error).message);
    return readLocal("recent_results.json");
  }
}

export async function getTopScorers(limit = 20) {
  try {
    return await query(`
      SELECT
        rank, player_id, player_name, team_name,
        goals, assists, goal_contributions,
        matches_played, goals_per_game, assists_per_game
      FROM \`${PROJECT_ID}.${DATASET_MART}.mart_top_scorers\`
      ORDER BY rank
      LIMIT ${limit}
    `);
  } catch (e) {
    console.warn("[BQ] top_scorers fallback →", (e as Error).message);
    return readLocal("top_scorers.json");
  }
}

export async function getMatches(limit = 380) {
  try {
    return await query(`
      SELECT
        match_id, matchday,
        FORMAT_DATE('%Y-%m-%d', match_date) AS match_date,
        home_team_name, away_team_name,
        home_score, away_score, match_status
      FROM \`${PROJECT_ID}.${DATASET_RAW}.matches\`
      WHERE season_id = 2324
      ORDER BY match_date DESC
      LIMIT ${limit}
    `);
  } catch (e) {
    console.warn("[BQ] matches fallback →", (e as Error).message);
    return readLocal("matches.json");
  }
}
