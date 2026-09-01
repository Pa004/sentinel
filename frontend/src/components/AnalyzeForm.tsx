import { useState, useMemo } from "react"
import { Search, CheckCircle, AlertCircle } from "lucide-react"
import { motion } from "framer-motion"

interface AnalyzeFormProps {
  onAnalyze: (url: string, branch: string) => void
  loading: boolean
}

function parseGithubInput(raw: string): { normalized: string; valid: boolean } {
  const trimmed = raw.trim()
  if (!trimmed) return { normalized: "", valid: false }

  // Full URL: https://github.com/owner/repo or github.com/owner/repo
  const urlMatch = trimmed.match(/(?:https?:\/\/)?(?:www\.)?github\.com\/([a-zA-Z0-9._-]+)\/([a-zA-Z0-9._-]+?)(?:\/.*)?$/)
  if (urlMatch) {
    return { normalized: `${urlMatch[1]}/${urlMatch[2]}`, valid: true }
  }

  // owner/repo format
  const orMatch = trimmed.match(/^([a-zA-Z0-9._-]+)\/([a-zA-Z0-9._-]+)$/)
  if (orMatch) {
    return { normalized: trimmed, valid: true }
  }

  return { normalized: trimmed, valid: false }
}

export default function AnalyzeForm({ onAnalyze, loading }: AnalyzeFormProps) {
  const [url, setUrl] = useState("")
  const [branch, setBranch] = useState("main")

  const validation = useMemo(() => parseGithubInput(url), [url])

  const handleSubmit = () => {
    if (validation.valid && !loading) {
      onAnalyze(validation.normalized, branch)
    }
  }

  const handleUrlChange = (value: string) => {
    setUrl(value)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-2"
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="sr-only" htmlFor="repo-url">
          GitHub repository URL or owner/name
        </label>
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            id="repo-url"
            type="text"
            placeholder="GitHub repo URL or owner/name"
            value={url}
            onChange={(e) => handleUrlChange(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            aria-describedby="repo-url-hint"
            aria-invalid={url.trim().length > 0 && !validation.valid}
            className="w-full rounded-md border border-border bg-surface-1 py-2.5 pl-9 pr-3 text-sm text-content placeholder:text-muted focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
          />
        </div>
        <label className="sr-only" htmlFor="branch-input">
          Branch name
        </label>
        <input
          id="branch-input"
          type="text"
          placeholder="Branch"
          value={branch}
          onChange={(e) => setBranch(e.target.value)}
          className="w-full rounded-md border border-border bg-surface-1 px-3 py-2.5 text-sm text-content placeholder:text-muted focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand sm:w-28"
        />
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSubmit}
          disabled={!validation.valid || loading}
          className="cursor-pointer rounded-md bg-brand px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-muted"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </motion.button>
      </div>

      {url.trim().length > 0 && (
        <div id="repo-url-hint" className="flex items-center gap-1.5 px-1" aria-live="polite">
          {validation.valid ? (
            <>
              <CheckCircle className="h-3.5 w-3.5 text-success" />
              <span className="text-xs text-success">
                {validation.normalized}
              </span>
            </>
          ) : (
            <>
              <AlertCircle className="h-3.5 w-3.5 text-warning" />
              <span className="text-xs text-warning">
                Enter owner/repo or a full GitHub URL
              </span>
            </>
          )}
        </div>
      )}
    </motion.div>
  )
}

export { parseGithubInput }
