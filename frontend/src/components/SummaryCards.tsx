import { motion } from "framer-motion"
import { AlertTriangle, AlertCircle, Info, Activity, GitBranch } from "lucide-react"

interface SummaryCardsProps {
  total: number
  errors: number
  warnings: number
  info: number
  drift: number
}

const cards = [
  { key: "total", label: "Total", icon: GitBranch, colorClass: "text-content" },
  { key: "errors", label: "Errors", icon: AlertCircle, colorClass: "text-error" },
  { key: "warnings", label: "Warnings", icon: AlertTriangle, colorClass: "text-warning" },
  { key: "info", label: "Info", icon: Info, colorClass: "text-info" },
  { key: "drift", label: "Drift", icon: Activity, colorClass: "text-error" },
] as const

export default function SummaryCards({ total, errors, warnings, info, drift }: SummaryCardsProps) {
  const values = { total, errors, warnings, info, drift }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {cards.map((card, i) => {
        const Icon = card.icon
        const val = values[card.key]
        return (
          <motion.div
            key={card.key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="rounded-md border border-border bg-surface-1 p-4 text-center"
          >
            <Icon className={`mx-auto mb-1 h-4 w-4 ${card.colorClass}`} />
            <motion.div
              key={val}
              initial={{ scale: 1.2, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className={`text-2xl font-bold ${card.colorClass}`}
            >
              {card.key === "drift" ? val.toFixed(2) : val}
            </motion.div>
            <div className="mt-0.5 text-xs text-muted">{card.label}</div>
          </motion.div>
        )
      })}
    </div>
  )
}
