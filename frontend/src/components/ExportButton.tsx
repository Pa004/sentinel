import { useState } from "react"
import { Download, ChevronDown } from "lucide-react"
import type { AnalysisResult } from "../api"

interface ExportButtonProps {
  result: AnalysisResult
}

export default function ExportButton({ result }: ExportButtonProps) {
  const [open, setOpen] = useState(false)

  const exportJSON = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" })
    download(blob, `sentinel-${result.repo_owner}-${result.repo_name}.json`)
    setOpen(false)
  }

  const exportCSV = () => {
    const headers = ["rule", "kind", "severity", "evidence", "components", "impact", "recommendation", "commit_sha"]
    const rows = result.violations.map((v) =>
      headers.map((h) => {
        const val = v[h as keyof typeof v]
        if (Array.isArray(val)) return val.join("; ")
        return String(val ?? "")
      })
    )
    const csv = [headers.join(","), ...rows.map((r) => r.map(escapeCSV).join(","))].join("\n")
    const blob = new Blob([csv], { type: "text/csv" })
    download(blob, `sentinel-${result.repo_owner}-${result.repo_name}.csv`)
    setOpen(false)
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:bg-surface-2 hover:text-content"
        aria-label="Export results"
        aria-expanded={open}
      >
        <Download className="h-3.5 w-3.5" />
        Export
        <ChevronDown className="h-3 w-3" />
      </button>
      {open && (
        <div className="absolute right-0 z-10 mt-1 w-40 rounded-md border border-border bg-surface-1 shadow-lg">
          <button
            onClick={exportJSON}
            className="block w-full px-3 py-2 text-left text-sm text-muted hover:bg-surface-2 hover:text-content"
          >
            JSON
          </button>
          <button
            onClick={exportCSV}
            className="block w-full px-3 py-2 text-left text-sm text-muted hover:bg-surface-2 hover:text-content"
          >
            CSV
          </button>
        </div>
      )}
    </div>
  )
}

function escapeCSV(val: string): string {
  if (val.includes(",") || val.includes('"') || val.includes("\n")) {
    return `"${val.replace(/"/g, '""')}"`
  }
  return val
}

function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
