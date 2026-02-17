import { promises as fs } from "fs";
import path from "path";
import Link from "next/link";
import { TeamStanding, getQualificationZone } from "@/lib/data";
import FormBadges from "@/components/FormBadges";
import TeamBadge from "@/components/TeamBadge";

async function getLeagueTable(): Promise<TeamStanding[]> {
  const filePath = path.join(process.cwd(), "public", "data", "league_table.json");
  const raw = await fs.readFile(filePath, "utf-8");
  return JSON.parse(raw);
}

const ZONE_LABELS: Record<string, { label: string; color: string; bg: string }> = {
  "champions-league":  { label: "Champions League", color: "#00c8ff", bg: "rgba(0,200,255,0.1)" },
  "europa-league":     { label: "Europa League",    color: "#f97316", bg: "rgba(249,115,22,0.1)" },
  "conference-league": { label: "Conference League",color: "#84cc16", bg: "rgba(132,204,22,0.1)" },
  "relegation":        { label: "Relegation",       color: "#ef4444", bg: "rgba(239,68,68,0.1)" },
};

export default async function LeagueTablePage() {
  const table = await getLeagueTable();

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🏆</span>
          <div>
            <h1 className="text-2xl font-bold text-white">Premier League Table</h1>
            <p className="text-gray-400 text-sm">2023-24 Season · Final Standings</p>
          </div>
        </div>
      </div>

      {/* Zone legend */}
      <div className="flex flex-wrap gap-3 mb-4">
        {Object.entries(ZONE_LABELS).map(([key, val]) => (
          <div key={key} className="flex items-center gap-1.5 text-xs">
            <div className="w-3 h-3 rounded-sm" style={{ background: val.color }} />
            <span className="text-gray-400">{val.label}</span>
          </div>
        ))}
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
                const zone = getQualificationZone(team.position);
                const zoneClass = zone ? `zone-${zone}` : "";
                const isChampion = team.position === 1;

                return (
                  <tr
                    key={team.team_id}
                    className={`border-b border-white/5 card-hover ${zoneClass} ${isChampion ? "bg-yellow-500/5" : ""}`}
                  >
                    <td className="py-3 px-4">
                      <span className={`font-bold text-sm ${isChampion ? "text-yellow-400" : "text-gray-400"}`}>
                        {isChampion ? "🏆" : team.position}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <Link
                        href={`/teams/${team.team_id}`}
                        className="flex items-center gap-2 hover:text-[#00ff85] transition-colors"
                      >
                        <TeamBadge teamName={team.team_name} size="sm" />
                        <span className="font-medium">{team.team_name}</span>
                      </Link>
                    </td>
                    <td className="text-center py-3 px-2 text-gray-300">{team.played}</td>
                    <td className="text-center py-3 px-2 text-green-400">{team.won}</td>
                    <td className="text-center py-3 px-2 text-gray-400">{team.drawn}</td>
                    <td className="text-center py-3 px-2 text-red-400">{team.lost}</td>
                    <td className="text-center py-3 px-2 text-gray-300">{team.goals_for}</td>
                    <td className="text-center py-3 px-2 text-gray-300">{team.goals_against}</td>
                    <td className="text-center py-3 px-2">
                      <span className={team.goal_difference > 0 ? "text-green-400" : team.goal_difference < 0 ? "text-red-400" : "text-gray-400"}>
                        {team.goal_difference > 0 ? `+${team.goal_difference}` : team.goal_difference}
                      </span>
                    </td>
                    <td className="text-center py-3 px-2">
                      <span className="font-bold text-white text-base">{team.points}</span>
                    </td>
                    <td className="text-center py-3 px-2 text-gray-400 hidden md:table-cell">
                      {team.win_rate}%
                    </td>
                    <td className="text-center py-3 px-2 hidden lg:table-cell">
                      <FormBadges form={team.form} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Stats summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
        <StatCard
          label="Most Goals"
          value="Manchester City"
          sub="96 scored"
          icon="⚡"
          color="#6CABDD"
        />
        <StatCard
          label="Best Defence"
          value="Arsenal"
          sub="29 conceded"
          icon="🛡️"
          color="#EF0107"
        />
        <StatCard
          label="Most Wins"
          value="Man City"
          sub="28 wins"
          icon="🏆"
          color="#6CABDD"
        />
        <StatCard
          label="Relegated"
          value="Luton · Burnley · Sheffield"
          sub="Bottom 3"
          icon="⬇️"
          color="#ef4444"
        />
      </div>
    </div>
  );
}

function StatCard({ label, value, sub, icon, color }: {
  label: string; value: string; sub: string; icon: string; color: string;
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
