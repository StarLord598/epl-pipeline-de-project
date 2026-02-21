import { NextResponse } from "next/server";
import { getTopScorers } from "@/lib/bigquery";

export const dynamic = "force-dynamic";
export const revalidate = 300;

export async function GET(request: Request) {
  const url  = new URL(request.url);
  const limit = parseInt(url.searchParams.get("limit") ?? "20", 10);

  try {
    const data = await getTopScorers(limit);
    return NextResponse.json(data, {
      headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=60" },
    });
  } catch (error) {
    console.error("[/api/scorers]", error);
    return NextResponse.json({ error: "Failed to fetch top scorers" }, { status: 500 });
  }
}
