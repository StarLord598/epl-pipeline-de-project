import Link from "next/link";

export const dynamic = "force-dynamic";

async function getHealth() {
  const res = await fetch("/data/live_monitor.json", { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export default async function HealthPage() {
  const health = await getHealth();

  return (
    <main className="min-h-screen bg-[#0d0f14] text-white p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Pipeline Health</h1>
          <Link href="/" className="text-sm text-emerald-300 hover:underline">
            ← Back
          </Link>
        </div>

        <p className="text-slate-300 mt-2">
          This page is fed by the local live pipeline writing to DuckDB → exported to
          <code className="ml-2 px-2 py-1 bg-slate-800 rounded">dashboard/public/data/live_monitor.json</code>.
        </p>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
            <div className="text-slate-400 text-xs">Freshness (minutes)</div>
            <div className="text-3xl font-semibold mt-1">{health?.freshness_minutes ?? "—"}</div>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
            <div className="text-slate-400 text-xs">SLA Status</div>
            <div className="text-xl font-semibold mt-2">
              {health?.freshness_status ?? "—"}
            </div>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
            <div className="text-slate-400 text-xs">Active matches tracked</div>
            <div className="text-3xl font-semibold mt-1">{health?.active_match_count ?? "—"}</div>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
            <div className="text-slate-400 text-xs">Last ingest timestamp</div>
            <div className="text-sm font-mono mt-2 text-slate-200 break-all">
              {health?.last_ingested_at ?? "—"}
            </div>
          </div>
        </div>

        <div className="mt-6 text-xs text-slate-400">
          Tip: run <code className="px-2 py-1 bg-slate-800 rounded">./scripts/run_live_pipeline.sh</code> and refresh.
        </div>
      </div>
    </main>
  );
}
