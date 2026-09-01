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

export default function SkeletonTable() {
  return (
    <div className="overflow-x-auto rounded-md border border-border">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-border bg-surface-1">
            <th className="px-3 py-2"><SkeletonPulse className="h-3 w-14" /></th>
            <th className="px-3 py-2"><SkeletonPulse className="h-3 w-16" /></th>
            <th className="px-3 py-2"><SkeletonPulse className="h-3 w-20" /></th>
            <th className="px-3 py-2"><SkeletonPulse className="h-3 w-24" /></th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 6 }).map((_, i) => (
            <tr key={i} className="border-b border-border/50 last:border-0">
              <td className="px-3 py-2.5"><SkeletonPulse className="h-5 w-14 rounded" /></td>
              <td className="px-3 py-2.5"><SkeletonPulse className="h-3 w-24" /></td>
              <td className="px-3 py-2.5"><SkeletonPulse className="h-3 w-40" /></td>
              <td className="px-3 py-2.5"><SkeletonPulse className="h-3 w-20" /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
