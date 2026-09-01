import { motion, AnimatePresence } from "framer-motion"
import { Search, CheckCircle } from "lucide-react"
import type { Violation } from "../api"

interface ViolationsTabProps {
  violations: Violation[]
  filtered: Violation[]
  severityFilter: string
  kindFilter: string
  search: string
  onSeverityChange: (v: string) => void
  onKindChange: (v: string) => void
  onSearchChange: (v: string) => void
}

const severityBadge: Record<string, string> = {
  error: "bg-error/15 text-error",
  warning: "bg-warning/15 text-warning",
  info: "bg-info/15 text-info",
}

export default function ViolationsTab({
  violations,
  filtered,
  severityFilter,
  kindFilter,
  search,
  onSeverityChange,
  onKindChange,
  onSearchChange,
}: ViolationsTabProps) {
  const kinds = [...new Set(violations.map((v) => v.kind))].sort()

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        <select
          value={severityFilter}
          onChange={(e) => onSeverityChange(e.target.value)}
          className="rounded-md border border-border bg-surface-1 px-3 py-1.5 text-sm text-content"
        >
          <option value="">Severity: all</option>
          <option value="error">error</option>
          <option value="warning">warning</option>
          <option value="info">info</option>
        </select>
        <select
          value={kindFilter}
          onChange={(e) => onKindChange(e.target.value)}
          className="rounded-md border border-border bg-surface-1 px-3 py-1.5 text-sm text-content"
        >
          <option value="">Kind: all</option>
          {kinds.map((k) => (
            <option key={k} value={k}>
              {k}
            </option>
          ))}
        </select>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Search..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full rounded-md border border-border bg-surface-1 py-1.5 pl-8 pr-3 text-sm text-content placeholder:text-muted sm:w-52"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-md border border-border bg-surface-1 py-12 text-success">
          <CheckCircle className="h-8 w-8" />
          <span className="text-sm font-medium">No violations found — architecture is clean.</span>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-md border border-border">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-border bg-surface-1">
                <th className="px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted">Severity</th>
                <th className="px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted">Rule</th>
                <th className="px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted">Evidence</th>
                <th className="px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted">Components</th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence>
                {filtered.map((v, i) => (
                  <motion.tr
                    key={`${v.rule}-${i}`}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="border-b border-border/50 last:border-0"
                  >
                    <td className="px-3 py-2">
                      <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-semibold ${severityBadge[v.severity] ?? "text-content"}`}>
                        {v.severity}
                      </span>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs text-content">{v.rule}</td>
                    <td className="max-w-xs truncate px-3 py-2 text-xs text-muted" title={v.evidence}>
                      {v.evidence}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted">{v.components.join(" → ")}</td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      )}

      <div className="mt-2 text-xs text-muted">
        Showing {filtered.length} of {violations.length} violations
      </div>
    </div>
  )
}
