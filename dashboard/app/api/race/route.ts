import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import path from "path";
import fs from "fs";

export const dynamic = "force-dynamic";

/**
 * GET /api/race?teams=Arsenal,Chelsea&from=5&to=20
 * Cumulative points race data
 * Query params:
 *   - teams: comma-separated team names (optional, defaults to all)
 *   - from: start matchday (optional)
 *   - to: end matchday (optional)
 */
export async function GET(request: NextRequest) {
  try {
    const filePath = path.join(process.cwd(), "public", "data", "points_race.json");
    if (!fs.existsSync(filePath)) {
      return NextResponse.json({ error: "Points race data not available" }, { status: 404 });
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let data: any[] = JSON.parse(fs.readFileSync(filePath, "utf-8"));
    const { searchParams } = new URL(request.url);

    const teams = searchParams.get("teams");
    if (teams) {
      const teamList = teams.split(",").map((t) => t.trim().toLowerCase());
      data = data.filter((r) => teamList.includes(r.team_name.toLowerCase()));
    }

    const from = searchParams.get("from");
    if (from) data = data.filter((r) => r.matchday >= parseInt(from));

    const to = searchParams.get("to");
    if (to) data = data.filter((r) => r.matchday <= parseInt(to));

    return NextResponse.json({
      count: data.length,
      data,
    }, {
      headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=60" },
    });
  } catch (error) {
    console.error("[/api/race]", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
