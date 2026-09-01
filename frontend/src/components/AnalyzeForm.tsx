import { useState } from "react"
import { Search } from "lucide-react"
import { motion } from "framer-motion"

interface AnalyzeFormProps {
  onAnalyze: (url: string, branch: string) => void
  loading: boolean
}

export default function AnalyzeForm({ onAnalyze, loading }: AnalyzeFormProps) {
  const [url, setUrl] = useState("")
  const [branch, setBranch] = useState("main")

  const handleSubmit = () => {
    if (url.trim() && !loading) onAnalyze(url.trim(), branch)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col gap-3 sm:flex-row sm:items-center"
    >
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        <input
          type="text"
          placeholder="GitHub repo URL or owner/name"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          className="w-full rounded-md border border-border bg-surface-1 py-2.5 pl-9 pr-3 text-sm text-content placeholder:text-muted focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
        />
      </div>
      <input
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
        disabled={!url.trim() || loading}
        className="cursor-pointer rounded-md bg-brand px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-hover disabled:cursor-not-allowed disabled:bg-surface-2 disabled:text-muted"
      >
        {loading ? "Analyzing..." : "Analyze"}
      </motion.button>
    </motion.div>
  )
}
