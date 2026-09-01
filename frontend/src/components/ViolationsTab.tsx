import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Search, CheckCircle, ChevronDown, ChevronUp, Copy, Check } from "lucide-react"
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

type SortKey = "severity" | "rule" | null
type SortDir = "asc" | "desc"

const severityOrder: Record<string, number> = { error: 0, warning: 1, info: 2 }

function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // fallback: do nothing
    }
  }, [text])

  return (
    <button
      onClick={handleCopy}
      className="inline-flex items-center gap-1 rounded bg-surface-2 px-1.5 py-0.5 text-[10px] text-muted transition-colors hover:text-content"
      aria-label={`Copy ${label}`}
      title={`Copy ${label}`}
    >
      {copied ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
      {copied ? "Copied" : text.slice(0, 7)}
    </button>
  )
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
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>(null)
  const [sortDir, setSortDir] = useState<SortDir>("asc")

  const sorted = [...filtered].sort((a, b) => {
    if (!sortKey) return 0
    let cmp = 0
    if (sortKey === "severity") {
      cmp = (severityOrder[a.severity] ?? 3) - (severityOrder[b.severity] ?? 3)
    } else if (sortKey === "rule") {
      cmp = a.rule.localeCompare(b.rule)
    }
    return sortDir === "asc" ? cmp : -cmp
  })

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"))
    } else {
      setSortKey(key)
      setSortDir("asc")
    }
  }

  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) return null
    return sortDir === "asc"
      ? <ChevronUp className="ml-1 inline h-3 w-3" />
      : <ChevronDown className="ml-1 inline h-3 w-3" />
  }

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        <label className="sr-only" htmlFor="severity-filter">Filter by severity</label>
        <select
          id="severity-filter"
          value={severityFilter}
          onChange={(e) => onSeverityChange(e.target.value)}
          className="rounded-md border border-border bg-surface-1 px-3 py-1.5 text-sm text-content"
        >
          <option value="">Severity: all</option>
          <option value="error">error</option>
          <option value="warning">warning</option>
          <option value="info">info</option>
        </select>
        <label className="sr-only" htmlFor="kind-filter">Filter by kind</label>
        <select
          id="kind-filter"
          value={kindFilter}
          onChange={(e) => onKindChange(e.target.value)}
          className="rounded-md border border-border bg-surface-1 px-3 py-1.5 text-sm text-content"
        >
          <option value="">Kind: all</option>
          {kinds.map((k) => (
            <option key={k} value={k}>{k}</option>
          ))}
        </select>
        <label className="sr-only" htmlFor="violation-search">Search violations</label>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted" />
          <input
            id="violation-search"
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
        <>
          {/* Desktop table */}
          <div className="hidden overflow-x-auto rounded-md border border-border sm:block">
            <table className="w-full text-left text-sm" aria-label="Violations">
              <thead>
                <tr className="border-b border-border bg-surface-1">
                  <th
                    className="cursor-pointer select-none px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted hover:text-content"
                    onClick={() => toggleSort("severity")}
                    scope="col"
                  >
                    Severity<SortIcon column="severity" />
                  </th>
                  <th
                    className="cursor-pointer select-none px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted hover:text-content"
                    onClick={() => toggleSort("rule")}
                    scope="col"
                  >
                    Rule<SortIcon column="rule" />
                  </th>
                  <th className="px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted" scope="col">Evidence</th>
                  <th className="px-3 py-2 text-xs font-medium uppercase tracking-wider text-muted" scope="col">Components</th>
                </tr>
              </thead>
              <tbody>
                {sorted.flatMap((v, i) => {
                  const idx = violations.indexOf(v)
                  const isExpanded = expandedIndex === idx
                  return [
                    <motion.tr
                      key={`${v.rule}-${idx}`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ delay: i * 0.02 }}
                      className={`cursor-pointer border-b border-border/50 last:border-0 transition-colors hover:bg-surface-1 ${isExpanded ? "bg-surface-1" : ""}`}
                      onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                    >
                      <td className="px-3 py-2">
                        <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-semibold ${severityBadge[v.severity] ?? "text-content"}`}>
                          {v.severity}
                        </span>
                      </td>
                      <td className="px-3 py-2 font-mono text-xs text-content">
                        <CopyButton text={v.rule} label="rule name" />
                      </td>
                      <td className="max-w-xs truncate px-3 py-2 text-xs text-muted" title={v.evidence}>
                        {v.evidence}
                      </td>
                      <td className="px-3 py-2 text-xs text-muted">{v.components.join(" → ")}</td>
                    </motion.tr>,
                    isExpanded && (
                      <tr key={`expanded-${v.rule}-${idx}`} className="border-b border-border/50 bg-surface-1">
                        <td colSpan={4} className="px-3 py-3">
                          <div className="space-y-3 pl-2">
                            {renderExpandedDetails(v)}
                          </div>
                        </td>
                      </tr>
                    ),
                  ].filter(Boolean)
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile card layout */}
          <div className="space-y-2 sm:hidden">
            <AnimatePresence>
              {sorted.map((v, i) => {
                const idx = violations.indexOf(v)
                const isExpanded = expandedIndex === idx
                return (
                  <motion.div
                    key={`card-${v.rule}-${idx}`}
                    initial={{ opacity: 0, y: 5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ delay: i * 0.02 }}
                    className="rounded-md border border-border bg-surface-1 p-3"
                  >
                    <button
                      className="flex w-full items-center justify-between text-left"
                      onClick={() => setExpandedIndex(isExpanded ? null : idx)}
                      aria-expanded={isExpanded}
                    >
                      <div className="flex items-center gap-2">
                        <span className={`inline-block rounded px-1.5 py-0.5 text-xs font-semibold ${severityBadge[v.severity] ?? "text-content"}`}>
                          {v.severity}
                        </span>
                        <span className="font-mono text-xs text-content">{v.rule}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted">{v.components.length} file(s)</span>
                        {isExpanded ? <ChevronUp className="h-4 w-4 text-muted" /> : <ChevronDown className="h-4 w-4 text-muted" />}
                      </div>
                    </button>
                    <p className="mt-1.5 text-xs text-muted line-clamp-2">{v.evidence}</p>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="truncate text-xs text-muted">{v.components[0]}</span>
                      {v.components.length > 1 && (
                        <span className="shrink-0 text-xs text-muted">+{v.components.length - 1} more</span>
                      )}
                    </div>
                    {isExpanded && (
                        <div className="mt-3 space-y-2 border-t border-border pt-3">
                          {renderExpandedDetails(v)}
                        </div>
                    )}
                  </motion.div>
                )
              })}
            </AnimatePresence>
          </div>
        </>
      )}

      <div className="mt-2 text-xs text-muted">
        Showing {filtered.length} of {violations.length} violations
      </div>
    </div>
  )
}

function renderExpandedDetails(v: Violation) {
  return (
    <>
      <div>
        <span className="text-[10px] font-medium uppercase tracking-wider text-muted">Impact</span>
        <p className="mt-0.5 text-xs text-content">{v.impact}</p>
      </div>
      <div>
        <span className="text-[10px] font-medium uppercase tracking-wider text-muted">Recommendation</span>
        <p className="mt-0.5 text-xs text-content">{v.recommendation}</p>
      </div>
      <div>
        <span className="text-[10px] font-medium uppercase tracking-wider text-muted">Components</span>
        <p className="mt-0.5 font-mono text-xs text-muted">{v.components.join(" → ")}</p>
      </div>
      {v.commit_sha && (
        <div>
          <span className="text-[10px] font-medium uppercase tracking-wider text-muted">Origin commit</span>
          <div className="mt-0.5">
            <CopyButton text={v.commit_sha} label="commit SHA" />
          </div>
        </div>
      )}
    </>
  )
}
