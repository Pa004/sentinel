const sampleRows = [
  { severity: "error", badge: "bg-error/15 text-error", rule: "no-ui-into-db", evidence: "packages/ui/Table.tsx -> db/query.ts" },
  { severity: "error", badge: "bg-error/15 text-error", rule: "import-cycle", evidence: "core/router <-> core/middleware" },
  { severity: "warning", badge: "bg-warning/15 text-warning", rule: "god-module", evidence: "lib/utils.ts: 47 exports, 31 importers" },
]

const microStats = [
  { value: "8", label: "Rules" },
  { value: "5", label: "Languages" },
  { value: "120s", label: "Timeout" },
  { value: "5-min", label: "Cache" },
]

export function SampleOutput() {
  return (
    <div className="rounded-xl border border-border bg-surface-1 p-4">
      <div className="mb-2 flex items-center justify-between">
        <span className="text-[10px] font-bold uppercase tracking-wider text-muted">Sample output</span>
        <span className="font-mono text-[10px] text-muted">vercel/next.js@main</span>
      </div>
      <div className="mb-2 font-mono text-[11px] text-muted">
        <b className="text-content">10</b> total · <b className="text-error">3 errors</b> ·{" "}
        <b className="text-warning">5 warnings</b> · Δ <b className="text-content">0.42</b>
      </div>
      <div className="divide-y divide-border/50">
        {sampleRows.map((row) => (
          <div key={row.rule} className="flex items-center gap-2 py-1.5">
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase ${row.badge}`}>
              {row.severity}
            </span>
            <span className="font-mono text-[11px] font-semibold text-content">{row.rule}</span>
            <span className="truncate font-mono text-[10px] text-muted">{row.evidence}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

export function MicroStats() {
  return (
    <div className="grid grid-cols-4 divide-x divide-border rounded-xl border border-border bg-surface-1">
      {microStats.map((s) => (
        <div key={s.label} className="px-2 py-2.5 text-center">
          <div className="font-mono text-xs font-bold text-content">{s.value}</div>
          <div className="text-[9px] uppercase tracking-wider text-muted">{s.label}</div>
        </div>
      ))}
    </div>
  )
}
