import { motion } from "framer-motion"
import { ExternalLink } from "lucide-react"

interface ExampleReposProps {
  onSelect: (url: string) => void
  loading: boolean
}

const examples = [
  { repo: "Pa004/sentinel", label: "Sentinel" },
  { repo: "facebook/react", label: "React" },
  { repo: "microsoft/vscode", label: "VS Code" },
  { repo: "expressjs/express", label: "Express" },
]

export default function ExampleRepos({ onSelect, loading }: ExampleReposProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
      className="mt-3 flex flex-wrap items-center gap-2"
    >
      <span className="text-xs text-muted">Try:</span>
      {examples.map((ex) => (
        <button
          key={ex.repo}
          onClick={() => onSelect(ex.repo)}
          disabled={loading}
          className="group flex items-center gap-1 rounded-md border border-border bg-surface-1 px-2.5 py-1 text-xs text-muted transition-colors hover:border-brand/40 hover:text-content disabled:opacity-50"
        >
          {ex.label}
          <ExternalLink className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
        </button>
      ))}
    </motion.div>
  )
}
