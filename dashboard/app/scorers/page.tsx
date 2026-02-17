"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { TopScorer, TEAM_COLORS } from "@/lib/data";
import TeamBadge from "@/components/TeamBadge";

export default function ScorersPage() {
  const [scorers, setScorers] = useState<TopScorer[]>([]);
  const [view, setView] = useState<"goals" | "assists" | "contributions">("goals");

  useEffect(() => {
    fetch("/data/top_scorers.json")
      .then((r) => r.json())
      .then(setScorers);
  }, []);

  const top10 = scorers.slice(0, 10);

  const chartData = top10.map((s) => ({
    name: s.player_name.split(" ").slice(-1)[0], // Last name
    fullName: s.player_name,
    goals: s.goals,
    assists: s.assists,
    contributions: s.goal_contributions,
    team: s.team_name,
  }));


  const getColor = (team: string) => TEAM_COLORS[team]?.primary || "#6b7280";

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">🎯</span>
          <div>
            <h1 className="text-2xl font-bold text-white">Top Scorers</h1>
            <p className="text-gray-400 text-sm">2023-24 Golden Boot Race</p>
          </div>
        </div>
      </div>

      {/* View toggle */}
      <div className="flex gap-2 mb-6">
        {(["goals", "assists", "contributions"] as const).map((v) => (
          <button
            key={v}
            onClick={() => setView(v)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
              view === v
                ? "bg-[#00ff85] text-[#38003c]"
                : "glass text-gray-400 hover:text-white"
            }`}
          >
            {v === "goals" ? "⚽ Goals" : v === "assists" ? "🎯 Assists" : "🌟 G+A"}
          </button>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Bar chart */}
        <div className="glass rounded-xl p-4">
          <h2 className="text-sm text-gray-400 uppercase tracking-wider mb-4">
            {view === "goals" ? "Goals Scored" : view === "assists" ? "Assists" : "Goal Contributions"} — Top 10
          </h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} layout="vertical">
              <XAxis type="number" tick={{ fill: "#9ca3af", fontSize: 11 }} />
              <YAxis
                type="category"
                dataKey="name"
                tick={{ fill: "#e5e7eb", fontSize: 11 }}
                width={80}
              />
              <Tooltip
                formatter={(v, _, props) => [v, props.payload?.fullName]}
                contentStyle={{ background: "#1a1a2e", border: "1px solid rgba(255,255,255,0.1)", color: "#fff" }}
              />
              <Bar dataKey={view} radius={[0, 4, 4, 0]}>
                {chartData.map((entry, i) => (
                  <Cell key={i} fill={getColor(entry.team)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Leaderboard */}
        <div className="glass rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 text-xs uppercase border-b border-white/10">
                  <th className="text-left py-3 px-4 w-8">#</th>
                  <th className="text-left py-3 px-4">Player</th>
                  <th className="text-center py-3 px-2">⚽</th>
                  <th className="text-center py-3 px-2">🎯</th>
                  <th className="text-center py-3 px-2 hidden sm:table-cell">G/G</th>
                  <th className="text-center py-3 px-2 hidden sm:table-cell">MP</th>
                </tr>
              </thead>
              <tbody>
                {scorers.slice(0, 15).map((scorer) => (
                  <tr key={scorer.player_id} className="border-b border-white/5 card-hover">
                    <td className="py-2.5 px-4">
                      <span className={`font-bold text-sm ${
                        scorer.rank === 1 ? "text-yellow-400" :
                        scorer.rank <= 3 ? "text-gray-300" : "text-gray-500"
                      }`}>
                        {scorer.rank === 1 ? "🥇" : scorer.rank === 2 ? "🥈" : scorer.rank === 3 ? "🥉" : scorer.rank}
                      </span>
                    </td>
                    <td className="py-2.5 px-4">
                      <div className="flex items-center gap-2">
                        <TeamBadge teamName={scorer.team_name} size="sm" />
                        <div>
                          <p className="font-medium text-white text-sm">{scorer.player_name}</p>
                          <p className="text-gray-500 text-xs">{scorer.team_name}</p>
                        </div>
                      </div>
                    </td>
                    <td className="text-center py-2.5 px-2">
                      <span className="font-bold text-white">{scorer.goals}</span>
                    </td>
                    <td className="text-center py-2.5 px-2 text-gray-400">{scorer.assists}</td>
                    <td className="text-center py-2.5 px-2 text-gray-400 hidden sm:table-cell">
                      {scorer.goals_per_game}
                    </td>
                    <td className="text-center py-2.5 px-2 text-gray-400 hidden sm:table-cell">
                      {scorer.matches_played}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Golden boot podium */}
      {scorers.length > 0 && (
        <div className="mt-6">
          <h2 className="text-sm text-gray-400 uppercase tracking-wider mb-4">Golden Boot Podium</h2>
          <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto">
            {/* 2nd */}
            <div className="flex flex-col items-center glass rounded-xl p-4 mt-8">
              <span className="text-2xl mb-2">🥈</span>
              <div className="text-center">
                <p className="font-bold text-white">{scorers[1]?.player_name}</p>
                <p className="text-gray-400 text-xs">{scorers[1]?.team_name}</p>
                <p className="text-3xl font-black text-gray-300 mt-2">{scorers[1]?.goals}</p>
                <p className="text-gray-500 text-xs">goals</p>
              </div>
            </div>
            {/* 1st */}
            <div className="flex flex-col items-center glass rounded-xl p-4 border border-yellow-500/30" style={{ background: "rgba(234,179,8,0.05)" }}>
              <span className="text-2xl mb-2">🥇</span>
              <div className="text-center">
                <p className="font-bold text-yellow-400">{scorers[0]?.player_name}</p>
                <p className="text-gray-400 text-xs">{scorers[0]?.team_name}</p>
                <p className="text-4xl font-black text-yellow-400 mt-2">{scorers[0]?.goals}</p>
                <p className="text-gray-500 text-xs">goals</p>
              </div>
            </div>
            {/* 3rd */}
            <div className="flex flex-col items-center glass rounded-xl p-4 mt-12">
              <span className="text-2xl mb-2">🥉</span>
              <div className="text-center">
                <p className="font-bold text-white">{scorers[2]?.player_name}</p>
                <p className="text-gray-400 text-xs">{scorers[2]?.team_name}</p>
                <p className="text-3xl font-black text-orange-300 mt-2">{scorers[2]?.goals}</p>
                <p className="text-gray-500 text-xs">goals</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
