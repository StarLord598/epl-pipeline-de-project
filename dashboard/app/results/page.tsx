import { promises as fs } from "fs";
import path from "path";
import Link from "next/link";
import { MatchResult } from "@/lib/data";
import TeamBadge from "@/components/TeamBadge";

async function getResults(): Promise<MatchResult[]> {
  const filePath = path.join(process.cwd(), "public", "data", "recent_results.json");
  const raw = await fs.readFile(filePath, "utf-8");
  return JSON.parse(raw);
}

function groupByMatchday(matches: MatchResult[]): Record<number, MatchResult[]> {
  const groups: Record<number, MatchResult[]> = {};
  for (const m of matches) {
    if (!groups[m.matchday]) groups[m.matchday] = [];
    groups[m.matchday].push(m);
  }
  return groups;
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
}

function ResultBadge({ result }: { result?: string }) {
  if (!result) return null;
  const classes = {
    W: "bg-green-500/20 text-green-400 border border-green-500/30",
    D: "bg-gray-500/20 text-gray-400 border border-gray-500/30",
    L: "bg-red-500/20 text-red-400 border border-red-500/30",
  };
  return (
    <span className={`inline-block w-5 h-5 rounded text-xs font-bold flex items-center justify-center ${classes[result as keyof typeof classes]}`}>
      {result}
    </span>
  );
}

export default async function ResultsPage() {
  const results = await getResults();
  const groups = groupByMatchday(results);
  const matchdays = Object.keys(groups).map(Number).sort((a, b) => b - a);

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">⚽</span>
          <div>
            <h1 className="text-2xl font-bold text-white">Results</h1>
            <p className="text-gray-400 text-sm">2023-24 Season · All 380 Matches</p>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {matchdays.slice(0, 15).map((day) => (
          <div key={day}>
            {/* Matchday header */}
            <div className="flex items-center gap-3 mb-3">
              <div className="bg-[#38003c] text-[#00ff85] text-xs font-bold px-3 py-1 rounded-full">
                Matchday {day}
              </div>
              <div className="flex-1 h-px bg-white/10" />
            </div>

            {/* Matches grid */}
            <div className="grid gap-2">
              {groups[day].map((match) => (
                <Link
                  key={match.match_id}
                  href={`/matches/${match.match_id}`}
                  className="glass rounded-lg p-3 card-hover"
                >
                  <div className="flex items-center justify-between">
                    {/* Home team */}
                    <div className="flex items-center gap-2 flex-1 justify-end">
                      <span className="text-sm font-medium text-white text-right hidden sm:block">
                        {match.home_team_name}
                      </span>
                      <span className="text-xs text-gray-400 text-right sm:hidden">
                        {match.home_team_name.split(" ")[0]}
                      </span>
                      <TeamBadge teamName={match.home_team_name} size="sm" />
                      <ResultBadge result={match.home_result} />
                    </div>

                    {/* Score */}
                    <div className="mx-4 text-center min-w-[80px]">
                      <div className="flex items-center justify-center gap-2">
                        <span className="text-xl font-black text-white">{match.home_score}</span>
                        <span className="text-gray-500 text-sm">–</span>
                        <span className="text-xl font-black text-white">{match.away_score}</span>
                      </div>
                      <div className="text-gray-500 text-xs">{formatDate(match.match_date)}</div>
                    </div>

                    {/* Away team */}
                    <div className="flex items-center gap-2 flex-1">
                      <ResultBadge result={match.away_result} />
                      <TeamBadge teamName={match.away_team_name} size="sm" />
                      <span className="text-sm font-medium text-white hidden sm:block">
                        {match.away_team_name}
                      </span>
                      <span className="text-xs text-gray-400 sm:hidden">
                        {match.away_team_name.split(" ")[0]}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        ))}

        {matchdays.length > 15 && (
          <p className="text-gray-500 text-sm text-center">
            Showing last 15 matchdays of {matchdays.length} total
          </p>
        )}
      </div>
    </div>
  );
}
