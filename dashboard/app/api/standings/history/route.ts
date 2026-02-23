import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import path from "path";
import fs from "fs";

export const dynamic = "force-dynamic";

/**
 * GET /api/standings/history?team=Arsenal&matchday=15
 * SCD2 position history — tracks when teams changed position
 * Query params:
 *   - team: filter by team name (optional)
 *   - matchday: filter by specific matchday (optional)
 *   - changes_only: if "true", only return rows where position changed
 */
export async function GET(request: NextRequest) {
  try {
    const filePath = path.join(process.cwd(), "public", "data", "scd2_standings.json");
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: "SCD2 data not available" }, { status: 404 });
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let data: any[] = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    const { searchParams } = new URL(request.url);

    const team = searchParams.get("team");
    if (team) {
      data = data.filter((r) => r.team_name.toLowerCase() === team.toLowerCase());
    }

    const matchday = searchParams.get("matchday");
    if (matchday) {
      data = data.filter((r) => r.matchday === parseInt(matchday));
    }

    const changesOnly = searchParams.get("changes_only");
    if (changesOnly === "true") {
      data = data.filter((r) => r.position_changed);
    }

    return NextResponse.json({
      count: data.length,
      data,
    }, {
      headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=60" },
    });
  } catch (error) {
    console.error("[/api/standings/history]", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
