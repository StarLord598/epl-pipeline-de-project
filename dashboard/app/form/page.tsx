"use client";

import { useEffect, useState } from "react";
import DataSourceBadge from "@/components/DataSourceBadge";

interface FormRow {
  team_name: string;
  matchday: number;
  result: string;
  pts: number;
  gf: number;
  ga: number;
  rolling_5_ppg: number;
  rolling_5_goals_scored: number;
  rolling_5_goals_conceded: number;
  last_5_form: string;
  current_momentum: string | null;
  recency_rank: number;
}

interface SCD2Row {
  team_name: string;
  matchday: number;
  position: number;
  prev_position: number | null;
  movement: string;
  positions_moved: number;
  points: number;
}

const MOMENTUM_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  HOT: { bg: "bg-red-500/20", text: "text-red-400", label: "🔥 HOT" },
  STEADY: { bg: "bg-yellow-500/20", text: "text-yellow-400", label: "⚡ STEADY" },
  COOLING: { bg: "bg-blue-400/20", text: "text-blue-400", label: "❄️ COOLING" },
  COLD: { bg: "bg-blue-800/20", text: "text-blue-300", label: "🥶 COLD" },
};

function FormBadge({ char }: { char: string }) {
  const colors: Record<string, string> = {
    W: "bg-green-500",
    D: "bg-gray-500",
    L: "bg-red-500",
  };
  return (
    <span className={`inline-flex items-center justify-center w-6 h-6 rounded text-xs font-bold text-white ${colors[char] || "bg-gray-700"}`}>
      {char}
    </span>
  );
}

export default function FormPage() {
  const [form, setForm] = useState<FormRow[]>([]);
  const [scd2, setScd2] = useState<SCD2Row[]>([]);
  const [view, setView] = useState<"momentum" | "positions">("momentum");

  useEffect(() => {
    fetch("/data/rolling_form.json").then((r) => r.json()).then(setForm);
    fetch("/data/scd2_standings.json").then((r) => r.json()).then(setScd2);
  }, []);

  // Group by momentum
  const grouped = {
    HOT: form.filter((r) => r.current_momentum === "HOT"),
    STEADY: form.filter((r) => r.current_momentum === "STEADY"),
    COOLING: form.filter((r) => r.current_momentum === "COOLING"),
    COLD: form.filter((r) => r.current_momentum === "COLD"),
  };

  // SCD2: biggest movers this season
  const maxMD = scd2.length > 0 ? Math.max(...scd2.map((r) => r.matchday)) : 0;
  const latestPositions = scd2.filter((r) => r.matchday === maxMD);
  const firstPositions = scd2.filter((r) => r.matchday === 1);
  const movers = latestPositions.map((curr) => {
    const first = firstPositions.find((f) => f.team_name === curr.team_name);
    return {
      team: curr.team_name,
      current: curr.position,
      start: first?.position ?? curr.position,
      change: (first?.position ?? curr.position) - curr.position,
      points: curr.points,
    };
  }).sort((a, b) => b.change - a.change);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🔥</span>
          <div>
            <h1 className="text-2xl font-bold text-white">Form & Momentum</h1>
            <p className="text-gray-400 text-sm">
              Rolling 5-game form · SCD2 position tracking · 2025-26 Season
            </p>
          </div>
        </div>
        <DataSourceBadge
          pattern="Rolling Window"
          source="Gold: mart_rolling_form + mart_scd2_standings"
          explanation="Two patterns: (1) Rolling Window — AVG(points) OVER (ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) for 5-game PPG, classifying HOT/STEADY/COOLING/COLD. (2) SCD Type 2 — tracks every position change with valid_from/valid_to for point-in-time queries."
        />
        <div className="flex gap-2">
          <button
            onClick={() => setView("momentum")}
            className={`text-xs px-3 py-1.5 rounded-lg ${view === "momentum" ? "bg-[#00ff85] text-[#38003c]" : "bg-white/10 text-white"}`}
          >
            Momentum
          </button>
          <button
            onClick={() => setView("positions")}
            className={`text-xs px-3 py-1.5 rounded-lg ${view === "positions" ? "bg-[#00ff85] text-[#38003c]" : "bg-white/10 text-white"}`}
          >
            Position History
          </button>
        </div>
      </div>

      {view === "momentum" ? (
        <div className="space-y-6">
          {(["HOT", "STEADY", "COOLING", "COLD"] as const).map((tier) => {
            const style = MOMENTUM_STYLE[tier];
            const teams = grouped[tier];
            if (teams.length === 0) return null;
            return (
              <div key={tier} className={`glass rounded-xl overflow-hidden`}>
                <div className={`px-4 py-3 border-b border-white/10 ${style.bg}`}>
                  <h2 className={`text-sm font-bold ${style.text}`}>{style.label} — {teams.length} teams</h2>
                </div>
                <div className="divide-y divide-white/5">
                  {teams.map((t) => (
                    <div key={t.team_name} className="px-4 py-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <span className="font-medium text-white w-48">{t.team_name}</span>
                        <div className="flex gap-1">
                          {(t.last_5_form || "").split("").map((c, i) => (
                            <FormBadge key={i} char={c} />
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center gap-6 text-sm">
                        <div className="text-right">
                          <span className="text-gray-400 text-xs">PPG</span>
                          <p className={`font-bold ${t.rolling_5_ppg >= 2.0 ? "text-green-400" : t.rolling_5_ppg >= 1.0 ? "text-yellow-400" : "text-red-400"}`}>
                            {t.rolling_5_ppg.toFixed(1)}
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="text-gray-400 text-xs">GF/GA</span>
                          <p className="text-gray-300">
                            {t.rolling_5_goals_scored.toFixed(1)} / {t.rolling_5_goals_conceded.toFixed(1)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div>
          <div className="glass rounded-xl overflow-hidden">
            <div className="px-4 py-3 border-b border-white/10">
              <h2 className="text-sm text-gray-400 uppercase tracking-wider">
                Season Position Movement (GW1 → GW{maxMD})
              </h2>
            </div>
            <div className="divide-y divide-white/5">
              {movers.map((m) => (
                <div key={m.team} className="px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-white font-bold w-8 text-right">#{m.current}</span>
                    <span className="font-medium text-white w-48">{m.team}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-gray-400 text-sm">{m.points} pts</span>
                    <span className="text-gray-500 text-xs">started #{m.start}</span>
                    <span className={`font-bold text-sm min-w-[50px] text-right ${
                      m.change > 0 ? "text-green-400" :
                      m.change < 0 ? "text-red-400" : "text-gray-500"
                    }`}>
                      {m.change > 0 ? `▲ ${m.change}` : m.change < 0 ? `▼ ${Math.abs(m.change)}` : "—"}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
