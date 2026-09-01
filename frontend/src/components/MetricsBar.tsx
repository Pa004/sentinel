import { motion } from "framer-motion"
import { Network, ArrowRightLeft, RotateCcw, Link2 } from "lucide-react"
import type { Metrics } from "../api"

interface MetricsBarProps {
  metrics: Metrics
}

const items = [
  { key: "nodes", label: "Nodes", icon: Network },
  { key: "edges", label: "Edges", icon: ArrowRightLeft },
  { key: "cycles", label: "Cycles", icon: RotateCcw },
  { key: "avg_coupling", label: "Avg Coupling", icon: Link2 },
] as const

export default function MetricsBar({ metrics }: MetricsBarProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="rounded-md border border-border bg-surface-1 p-4"
    >
      <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-muted">
        Architecture Metrics
      </h3>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {items.map((item) => {
          const Icon = item.icon
          const raw = metrics[item.key as keyof Metrics]
          const val = raw != null ? (item.key === "avg_coupling" ? raw.toFixed(1) : raw) : "-"
          const isBad = item.key === "cycles" && typeof raw === "number" && raw > 0
          return (
            <div key={item.key} className="flex items-center gap-2 text-center">
              <Icon className="h-4 w-4 text-muted" />
              <div>
                <div className={`text-lg font-bold ${isBad ? "text-error" : "text-content"}`}>
                  {val}
                </div>
                <div className="text-xs text-muted">{item.label}</div>
              </div>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}
