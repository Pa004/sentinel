import { motion } from "framer-motion"
import { CheckCircle } from "lucide-react"
import type { Violation } from "../api"

interface RemediationTabProps {
  violations: Violation[]
}

const severityMeta: Record<string, { color: string; bg: string; border: string }> = {
  error: { color: "text-error", bg: "bg-error/15", border: "border-l-error" },
  warning: { color: "text-warning", bg: "bg-warning/15", border: "border-l-warning" },
  info: { color: "text-info", bg: "bg-info/15", border: "border-l-info" },
}

export default function RemediationTab({ violations }: RemediationTabProps) {
  if (violations.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-md border border-border bg-surface-1 py-12 text-success">
        <CheckCircle className="h-8 w-8" />
        <span className="text-sm font-medium">No violations to remediate — architecture is clean.</span>
      </div>
    )
  }

  const grouped = ["error", "warning", "info"]
    .map((sev) => ({
      sev,
      items: violations
        .filter((v) => v.severity === sev)
        .sort((a, b) => a.rule.localeCompare(b.rule)),
    }))
    .filter((g) => g.items.length > 0)

  return (
    <div className="space-y-6">
      {grouped.map(({ sev, items }) => {
        const meta = severityMeta[sev]
        return (
          <div key={sev}>
            <h3 className={`mb-3 flex items-center gap-2 text-sm font-semibold ${meta.color}`}>
              <span className={`h-2 w-2 rounded-full ${meta.bg}`} />
              {sev.charAt(0).toUpperCase() + sev.slice(1)}s — {items.length}
            </h3>
            <div className="space-y-2">
              {items.map((v, i) => (
                <motion.div
                  key={`${v.rule}-${i}`}
                  initial={{ opacity: 0, x: -5 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.03 }}
                  className={`rounded-md border border-border bg-surface-1 p-4 border-l-3 ${meta.border}`}
                >
                  <div className="mb-1 text-sm font-semibold text-content">{v.rule}</div>
                  <div className="mb-2 text-xs text-muted">{v.evidence}</div>
                  <div className="mb-2 text-sm text-content">
                    <span className="text-muted">Impact: </span>
                    {v.impact}
                  </div>
                  <div className="rounded-md bg-surface-2 p-3 text-sm border-l-2 border-success">
                    <span className="font-semibold text-success">Recommendation: </span>
                    <span className="text-content">{v.recommendation}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
