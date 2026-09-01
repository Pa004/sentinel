import { motion } from "framer-motion"

function SkeletonPulse({ className }: { className?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0.6 }}
      animate={{ opacity: [0.6, 1, 0.6] }}
      transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
      className={`rounded bg-surface-2 ${className}`}
    />
  )
}

export default function SkeletonMetrics() {
  return (
    <div className="rounded-md border border-border bg-surface-1 p-4">
      <SkeletonPulse className="mb-3 h-3 w-32" />
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center gap-2">
            <SkeletonPulse className="h-4 w-4 rounded-full" />
            <div className="flex flex-col gap-1">
              <SkeletonPulse className="h-5 w-10" />
              <SkeletonPulse className="h-2.5 w-14" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
