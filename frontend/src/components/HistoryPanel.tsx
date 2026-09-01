import { Clock } from "lucide-react"
import type { HistoryEntry } from "../hooks/useHistory"

interface HistoryPanelProps {
  history: HistoryEntry[]
  onSelect: (url: string, branch: string) => void
  onClear: () => void
  loading: boolean
}

export default function HistoryPanel({ history, onSelect, onClear, loading }: HistoryPanelProps) {
  if (history.length === 0) return null

  return (
    <div className="mt-6 rounded-md border border-border bg-surface-1 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted">
          <Clock className="h-3.5 w-3.5" />
          Recent Analyses
        </h3>
        <button
          onClick={onClear}
          className="text-xs text-muted hover:text-error transition-colors"
        >
          Clear
        </button>
      </div>
      <div className="space-y-1">
        {history.map((entry) => (
          <button
            key={`${entry.url}@${entry.branch}@${entry.timestamp}`}
            onClick={() => onSelect(entry.url, entry.branch)}
            disabled={loading}
            className="flex w-full items-center justify-between rounded px-3 py-2 text-left text-sm transition-colors hover:bg-surface-2 disabled:opacity-50"
          >
            <div className="min-w-0">
              <div className="truncate font-mono text-xs text-content">{entry.url}</div>
              <div className="text-xs text-muted">
                {entry.branch} · {entry.violations} violations · drift {entry.drift.toFixed(1)}
              </div>
            </div>
            <span className="ml-3 shrink-0 text-xs text-muted">
              {timeAgo(entry.timestamp)}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}

function timeAgo(ts: number): string {
  const diff = Date.now() - ts
  const mins = Math.floor(diff / 60_000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}
