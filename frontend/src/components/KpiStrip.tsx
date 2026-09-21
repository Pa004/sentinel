import type { Metrics } from "../api"

interface KpiStripProps {
  total: number
  errors: number
  warnings: number
  info: number
  drift: number
  metrics: Metrics | null
  elapsedMs: number | null
}

function Kpi({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="flex items-center gap-2 whitespace-nowrap border-r border-border px-3.5">
      <span className="text-[10px] uppercase tracking-wider text-muted">{label}</span>
      <span className={`font-mono text-[13px] font-bold tabular-nums ${tone ?? "text-content"}`}>
        {value}
      </span>
    </div>
  )
}

export default function KpiStrip({
  total,
  errors,
  warnings,
  info,
  drift,
  metrics,
  elapsedMs,
}: KpiStripProps) {
  const fmt = (v: number | null, digits = 0) =>
    v == null ? "-" : digits > 0 ? v.toFixed(digits) : String(Math.round(v))

  return (
    <div
      className="kpi-strip flex items-stretch overflow-x-auto border-b border-border bg-surface-1"
      role="status"
      aria-label="Analysis summary"
    >
      <Kpi label="Total" value={String(total)} />
      <Kpi label="Errors" value={String(errors)} tone="text-error" />
      <Kpi label="Warnings" value={String(warnings)} tone="text-warning" />
      <Kpi label="Info" value={String(info)} tone="text-info" />
      <div className="flex items-center gap-2 whitespace-nowrap border-r border-border px-3.5">
        <span className="text-[10px] uppercase tracking-wider text-muted">Drift</span>
        <span className="font-mono text-[13px] font-bold tabular-nums text-content">
          {drift.toFixed(2)}
        </span>
        <span
          className="h-[5px] w-16 overflow-hidden rounded bg-surface-3"
          role="img"
          aria-label={`Drift score ${drift.toFixed(2)} out of 1`}
        >
          <span className="block h-full bg-warning" style={{ width: `${drift * 100}%` }} />
        </span>
      </div>
      <Kpi label="Nodes" value={fmt(metrics?.nodes ?? null)} />
      <Kpi label="Edges" value={fmt(metrics?.edges ?? null)} />
      <Kpi label="Cycles" value={fmt(metrics?.cycles ?? null)} />
      <Kpi label="Coupling" value={fmt(metrics?.avg_coupling ?? null, 2)} />
      <div className="ml-auto flex items-center whitespace-nowrap border-l border-border px-3 font-mono text-[11px] text-muted">
        {elapsedMs !== null ? `analyzed in ${(elapsedMs / 1000).toFixed(1)}s` : ""}
      </div>
    </div>
  )
}
