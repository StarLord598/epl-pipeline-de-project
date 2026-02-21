import { NextResponse } from "next/server";
import { getLeagueTable } from "@/lib/bigquery";

export const dynamic = "force-dynamic";   // always re-fetch, never cache statically
export const revalidate = 300;            // ISR: refresh every 5 minutes

export async function GET() {
  try {
    const data = await getLeagueTable();
    return NextResponse.json(data, {
      headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=60" },
    });
  } catch (error) {
    console.error("[/api/league-table]", error);
    return NextResponse.json({ error: "Failed to fetch league table" }, { status: 500 });
  }
}
