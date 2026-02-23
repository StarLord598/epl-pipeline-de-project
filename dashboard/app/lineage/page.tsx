"use client";

export default function LineagePage() {
  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <span className="text-3xl">🔗</span>
        <div>
          <h1 className="text-2xl font-bold text-white">Data Lineage</h1>
          <p className="text-gray-400 text-sm">
            Interactive dependency graph — powered by dbt docs
          </p>
        </div>
      </div>
      <div className="glass rounded-xl overflow-hidden" style={{ height: "calc(100vh - 200px)" }}>
        <iframe
          src="/lineage/index.html"
          className="w-full h-full border-0"
          title="dbt Data Lineage"
        />
      </div>
    </div>
  );
}
