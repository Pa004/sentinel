import { motion } from "framer-motion"
import { Loader2 } from "lucide-react"

export default function LoadingState() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center gap-3 rounded-md border border-border bg-surface-1 py-12"
    >
      <Loader2 className="h-8 w-8 animate-spin text-brand" />
      <div>
        <div className="text-sm font-medium text-content">Analyzing repository...</div>
        <div className="mt-1 text-xs text-muted">Cloning, parsing, and running detection rules.</div>
      </div>
    </motion.div>
  )
}
