import { useState, useRef, useCallback } from "react"

interface PerformanceMetrics {
  analysisTimeMs: number | null
  renderTimeMs: number | null
}

export function usePerformance() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    analysisTimeMs: null,
    renderTimeMs: null,
  })
  const startRef = useRef<number>(0)

  const startTimer = useCallback(() => {
    startRef.current = performance.now()
  }, [])

  const endTimer = useCallback(() => {
    const elapsed = performance.now() - startRef.current
    setMetrics((prev) => ({ ...prev, analysisTimeMs: Math.round(elapsed) }))
    return elapsed
  }, [])

  const measureRender = useCallback((label: string, fn: () => void) => {
    const start = performance.now()
    fn()
    const elapsed = performance.now() - start
    setMetrics((prev) => ({ ...prev, renderTimeMs: Math.round(elapsed) }))
    if (elapsed > 16) {
      console.warn(`[Performance] ${label} took ${elapsed.toFixed(1)}ms (>16ms frame budget)`)
    }
  }, [])

  return { metrics, startTimer, endTimer, measureRender }
}
