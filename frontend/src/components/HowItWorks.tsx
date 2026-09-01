import { motion } from "framer-motion"
import { Search, Network, CheckCircle } from "lucide-react"

const steps = [
  { icon: Search, text: "Paste a GitHub repo URL" },
  { icon: Network, text: "Sentinel analyzes the dependency graph" },
  { icon: CheckCircle, text: "Get violations + remediation steps" },
]

export default function HowItWorks() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
      className="mt-8 rounded-md border border-border bg-surface-1 p-5"
    >
      <h3 className="mb-4 text-xs font-medium uppercase tracking-wider text-muted">
        How it works
      </h3>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {steps.map((step, i) => {
          const Icon = step.icon
          return (
            <div key={i} className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand/15 text-sm font-bold text-brand">
                {i + 1}
              </div>
              <Icon className="h-4 w-4 shrink-0 text-muted" />
              <span className="text-xs text-muted">{step.text}</span>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
