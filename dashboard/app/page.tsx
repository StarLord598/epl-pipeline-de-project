import Link from "next/link";
import { getLeagueTable } from "@/lib/bigquery";
import { getQualificationZone } from "@/lib/data";
import FormBadges from "@/components/FormBadges";
import TeamBadge from "@/components/TeamBadge";

export const revalidate = 300; // ISR: re-fetch from BigQuery every 5 min

const ZONE_LABELS: Record<string, { label: string; color: string }> = {
  "champions_league":  { label: "Champions League", color: "#00c8ff" },
  "europa_league":     { label: "Europa League",    color: "#f97316" },
  "conference_league": { label: "Conference League",color: "#84cc16" },
  "relegation":        { label: "Relegation",       color: "#ef4444" },
};

export default async function LeagueTablePage() {
  // ← Direct BigQuery call (with JSON fallback built-in)
  const table = await getLeagueTable() as Array<Record<string, unknown>>;

  // Derive extra stats from the live data
  const topGoalTeam  = [...table].sort((a, b) => (b.goals_for as number) - (a.goals_for as number))[0];
  const bestDefence  = [...table].sort((a, b) => (a.goals_against as number) - (b.goals_against as number))[0];
  const mostWins     = [...table].sort((a, b) => (b.won as number) - (a.won as number))[0];
  const relegated    = table.filter(t => (t.position as number) >= 18).map(t => t.team_name as string);

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🏆</span>
          <div>
            <h1 className="text-2xl font-bold text-white">Premier League Table</h1>
            <p className="text-gray-400 text-sm">2023-24 Season · Final Standings · Live from BigQuery</p>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <div className="flex flex-wrap gap-3">
          {Object.entries(ZONE_LABELS).map(([key, val]) => (
            <div key={key} className="flex items-center gap-1.5 text-xs">
              <div className="w-3 h-3 rounded-sm" style={{ background: val.color }} />
              <span className="text-gray-400">{val.label}</span>
            </div>
          ))}
        </div>

        <Link
          href="/health"
          className="text-xs text-emerald-300 hover:underline whitespace-nowrap"
        >
          View Pipeline Health →
        </Link>
      </div>

      {/* Table */}
      <div className="glass rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-gray-400 text-xs uppercase tracking-wider border-b border-white/10">
                <th className="text-left py-3 px-4 w-8">#</th>
                <th className="text-left py-3 px-4">Club</th>
                <th className="text-center py-3 px-2">MP</th>
                <th className="text-center py-3 px-2">W</th>
                <th className="text-center py-3 px-2">D</th>
                <th className="text-center py-3 px-2">L</th>
                <th className="text-center py-3 px-2">GF</th>
                <th className="text-center py-3 px-2">GA</th>
                <th className="text-center py-3 px-2">GD</th>
                <th className="text-center py-3 px-2 font-bold text-white">Pts</th>
                <th className="text-center py-3 px-2 hidden md:table-cell">Win%</th>
                <th className="text-center py-3 px-2 hidden lg:table-cell">Form</th>
              </tr>
            </thead>
            <tbody>
              {table.map((team) => {
                const pos  = team.position as number;
                const zone = (team.qualification_zone as string) || getQualificationZone(pos) || "";
                const zoneClass = zone ? `zone-${zone.replace(/_/g, "-")}` : "";
                const isChampion = pos === 1;

                return (
                  <tr
                    key={team.team_id as number}
                    className={`border-b border-white/5 card-hover ${zoneClass} ${isChampion ? "bg-yellow-500/5" : ""}`}
                  >
                    <td className="py-3 px-4">
                      <span className={`font-bold text-sm ${isChampion ? "text-yellow-400" : "text-gray-400"}`}>
                        {isChampion ? "🏆" : pos}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <Link
                        href={`/teams/${team.team_id}`}
                        className="flex items-center gap-2 hover:text-[#00ff85] transition-colors"
                      >
                        <TeamBadge teamName={team.team_name as string} size="sm" />
                        <span className="font-medium">{team.team_name as string}</span>
                      </Link>
                    </td>
                    <td className="text-center py-3 px-2 text-gray-300">{team.played as number}</td>
                    <td className="text-center py-3 px-2 text-green-400">{team.won as number}</td>
                    <td className="text-center py-3 px-2 text-gray-400">{team.drawn as number}</td>
                    <td className="text-center py-3 px-2 text-red-400">{team.lost as number}</td>
                    <td className="text-center py-3 px-2 text-gray-300">{team.goals_for as number}</td>
                    <td className="text-center py-3 px-2 text-gray-300">{team.goals_against as number}</td>
                    <td className="text-center py-3 px-2">
                      <span className={(team.goal_difference as number) > 0 ? "text-green-400" : (team.goal_difference as number) < 0 ? "text-red-400" : "text-gray-400"}>
                        {(team.goal_difference as number) > 0 ? `+${team.goal_difference}` : team.goal_difference as number}
                      </span>
                    </td>
                    <td className="text-center py-3 px-2">
                      <span className="font-bold text-white text-base">{team.points as number}</span>
                    </td>
                    <td className="text-center py-3 px-2 text-gray-400 hidden md:table-cell">
                      {team.win_rate as number}%
                    </td>
                    <td className="text-center py-3 px-2 hidden lg:table-cell">
                      <FormBadges form={team.form as string | undefined} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Dynamic stats summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <StatCard
          label="Most Goals"
          value={topGoalTeam?.team_name as string ?? "—"}
          sub={`${topGoalTeam?.goals_for} scored`}
          icon="⚡"
          color="#6CABDD"
        />
        <StatCard
          label="Best Defence"
          value={bestDefence?.team_name as string ?? "—"}
          sub={`${bestDefence?.goals_against} conceded`}
          icon="🛡️"
          color="#EF0107"
        />
        <StatCard
          label="Most Wins"
          value={mostWins?.team_name as string ?? "—"}
          sub={`${mostWins?.won} wins`}
          icon="🏆"
          color="#6CABDD"
        />
        <StatCard
          label="Relegated"
          value={relegated.join(" · ")}
          sub="Bottom 3"
          icon="⬇️"
          color="#ef4444"
        />
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, icon, color }: {
  label: string; value: string; sub: string | undefined; icon: string; color: string;
}) {
  return (
    <div className="glass rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">{icon}</span>
        <span className="text-xs text-gray-400 uppercase tracking-wider">{label}</span>
      </div>
      <p className="font-bold text-white text-sm" style={{ color }}>{value}</p>
      <p className="text-gray-400 text-xs mt-1">{sub}</p>
    </div>
  );
}
