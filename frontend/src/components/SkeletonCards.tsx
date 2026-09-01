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

export default function SkeletonCards() {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="flex flex-col items-center gap-2 rounded-md border border-border bg-surface-1 p-4"
        >
          <SkeletonPulse className="h-4 w-4 rounded-full" />
          <SkeletonPulse className="h-7 w-12" />
          <SkeletonPulse className="h-3 w-10" />
        </div>
      ))}
    </div>
  )
}
