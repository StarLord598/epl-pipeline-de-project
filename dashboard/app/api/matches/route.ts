import { NextResponse } from "next/server";
import { getMatches } from "@/lib/bigquery";

export const dynamic = "force-dynamic";
export const revalidate = 300;

export async function GET(request: Request) {
  const url   = new URL(request.url);
  const limit = parseInt(url.searchParams.get("limit") ?? "380", 10);

  try {
    const data = await getMatches(limit);
    return NextResponse.json(data, {
      headers: { "Cache-Control": "public, s-maxage=300, stale-while-revalidate=60" },
    });
  } catch (error) {
    console.error("[/api/matches]", error);
    return NextResponse.json({ error: "Failed to fetch matches" }, { status: 500 });
  }
}
