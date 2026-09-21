import { Clock } from "lucide-react"
import type { HistoryEntry } from "../hooks/useHistory"

interface HistoryRailProps {
  history: HistoryEntry[]
  onSelect: (url: string, branch: string) => void
  onClear: () => void
  loading: boolean
  open: boolean
}

function timeAgo(ts: number): string {
  const mins = Math.floor((Date.now() - ts) / 60_000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

export default function HistoryRail({ history, onSelect, onClear, loading, open }: HistoryRailProps) {
  return (
    <aside
      aria-label="Analysis history"
      className={`history-rail flex-col border-r border-border bg-surface-1 ${open ? "open" : ""} hidden min-h-0 md:flex`}
    >
      <h2 className="flex items-center justify-between px-3 pb-1.5 pt-2.5 text-[10px] uppercase tracking-wider text-muted">
        <span className="flex items-center gap-1.5">
          <Clock className="h-3 w-3" />
          History
        </span>
        {history.length > 0 && (
          <button onClick={onClear} className="rounded px-1.5 py-0.5 transition-colors hover:bg-error/15 hover:text-error">
            Clear
          </button>
        )}
      </h2>
      <div className="flex flex-col gap-1 overflow-y-auto px-2 pb-3">
        {history.length === 0 ? (
          <p className="px-2 py-1 text-[11px] text-muted">No runs yet. Analyze a repo to start.</p>
        ) : (
          history.map((entry) => (
            <button
              key={`${entry.url}@${entry.branch}@${entry.timestamp}`}
              onClick={() => onSelect(entry.url, entry.branch)}
              disabled={loading}
              className="flex w-full flex-col gap-0.5 rounded-md border border-transparent px-2 py-1.5 text-left transition-colors hover:bg-surface-2 disabled:opacity-50"
            >
              <span className="truncate font-mono text-[11px] font-semibold text-content">
                {entry.url}
              </span>
              <span className="font-mono text-[10px] text-muted">
                {entry.branch} · <b className="text-success">{entry.violations} viol</b> · Δ{" "}
                {entry.drift.toFixed(2)} · {timeAgo(entry.timestamp)}
              </span>
            </button>
          ))
        )}
      </div>
      <div className="mt-auto border-t border-border px-3 py-2 font-mono text-[10px] text-muted">
        cache TTL 5:00
      </div>
    </aside>
  )
}
