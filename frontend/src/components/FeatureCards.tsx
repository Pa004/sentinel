import { motion } from "framer-motion"
import { ShieldAlert, RotateCcw, Layers, Activity } from "lucide-react"

const features = [
  {
    icon: ShieldAlert,
    title: "Layer Violations",
    description: "Dependencies crossing forbidden layer boundaries",
    severity: "error",
  },
  {
    icon: RotateCcw,
    title: "Circular Dependencies",
    description: "Cycles across modules detected via Tarjan SCC",
    severity: "error",
  },
  {
    icon: Layers,
    title: "God Modules",
    description: "Module with too many connections (fan-in + fan-out)",
    severity: "warning",
  },
  {
    icon: Activity,
    title: "Drift Detection",
    description: "Architecture changes tracked between commits",
    severity: "info",
  },
] as const

const severityBadge: Record<string, string> = {
  error: "bg-error/15 text-error",
  warning: "bg-warning/15 text-warning",
  info: "bg-info/15 text-info",
}

export default function FeatureCards() {
  return (
    <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2">
      {features.map((feature, i) => {
        const Icon = feature.icon
        return (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 + i * 0.08 }}
            className="flex flex-col gap-2 rounded-md border border-border bg-surface-1 p-5"
          >
            <div className="flex items-center gap-2.5">
              <Icon className="h-4.5 w-4.5 text-brand" />
              <span className="text-sm font-semibold text-content">{feature.title}</span>
              <span className={`ml-auto rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${severityBadge[feature.severity]}`}>
                {feature.severity}
              </span>
            </div>
            <p className="text-xs leading-relaxed text-muted">{feature.description}</p>
          </motion.div>
        )
      })}
    </div>
  )
}
