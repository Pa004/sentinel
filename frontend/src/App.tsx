import { useState, useEffect, useRef, useCallback } from "react"
import { Sun, Moon, X, RotateCcw } from "lucide-react"
import { motion } from "framer-motion"
import { analyze } from "./api"
import type { Violation, AnalysisResult } from "./api"
import AnalyzeForm from "./components/AnalyzeForm"
import SummaryCards from "./components/SummaryCards"
import MetricsBar from "./components/MetricsBar"
import ViolationsTab from "./components/ViolationsTab"
import RemediationTab from "./components/RemediationTab"
import SkeletonCards from "./components/SkeletonCards"
import SkeletonMetrics from "./components/SkeletonMetrics"
import SkeletonTable from "./components/SkeletonTable"
import FeatureCards from "./components/FeatureCards"
import HowItWorks from "./components/HowItWorks"
import ExampleRepos from "./components/ExampleRepos"
import { usePrefersReducedMotion } from "./hooks/usePrefersReducedMotion"
import { useToast } from "./components/Toast"

function useTheme() {
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem("sentinel-theme")
    return stored ? stored === "dark" : true
  })

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark)
    document.documentElement.classList.toggle("light", !dark)
    localStorage.setItem("sentinel-theme", dark ? "dark" : "light")
  }, [dark])

  return { dark, toggle: () => setDark((d) => !d) }
}

const TABS = ["violations", "remediation"] as const
type TabKey = (typeof TABS)[number]

export default function App() {
  const { dark, toggle } = useTheme()
  const reducedMotion = usePrefersReducedMotion()
  const { addToast } = useToast()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [lastAnalyzed, setLastAnalyzed] = useState<{ url: string; branch: string } | null>(null)
  const [activeTab, setActiveTab] = useState<TabKey>("violations")
  const [severityFilter, setSeverityFilter] = useState("")
  const [kindFilter, setKindFilter] = useState("")
  const [search, setSearch] = useState("")

  const resultsRef = useRef<HTMLDivElement>(null)
  const tabRefs = useRef<Record<TabKey, HTMLButtonElement | null>>({
    violations: null,
    remediation: null,
  })

  const handleAnalyze = async (url: string, br: string) => {
    setLoading(true)
    setError("")
    setResult(null)
    setLastAnalyzed({ url, branch: br })
    try {
      const data = await analyze(url, br)
      setResult(data)
      if (data.total_violations === 0) {
        addToast("No violations found — architecture looks clean!", "success")
      } else {
        addToast(`Found ${data.total_violations} violation(s)`, "info")
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Analysis failed"
      setError(msg)
      addToast(msg, "error")
    } finally {
      setLoading(false)
    }
  }

  const handleRetry = () => {
    if (lastAnalyzed) {
      handleAnalyze(lastAnalyzed.url, lastAnalyzed.branch)
    }
  }

  // Focus management: move focus to results after analysis completes
  useEffect(() => {
    if (result && !loading && resultsRef.current) {
      resultsRef.current.focus()
    }
  }, [result, loading])

  // Keyboard navigation for tabs
  const handleTabKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      const currentIndex = TABS.indexOf(activeTab)
      let nextIndex: number | null = null

      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault()
        nextIndex = (currentIndex + 1) % TABS.length
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault()
        nextIndex = (currentIndex - 1 + TABS.length) % TABS.length
      } else if (e.key === "Home") {
        e.preventDefault()
        nextIndex = 0
      } else if (e.key === "End") {
        e.preventDefault()
        nextIndex = TABS.length - 1
      }

      if (nextIndex !== null) {
        const nextTab = TABS[nextIndex]
        setActiveTab(nextTab)
        tabRefs.current[nextTab]?.focus()
      }
    },
    [activeTab]
  )

  const violations: Violation[] = result?.violations ?? []
  const metrics = result?.metrics ?? null

  const filtered = violations.filter((v) => {
    if (severityFilter && v.severity !== severityFilter) return false
    if (kindFilter && v.kind !== kindFilter) return false
    if (search) {
      const q = search.toLowerCase()
      return (
        v.evidence.toLowerCase().includes(q) ||
        v.impact.toLowerCase().includes(q) ||
        v.rule.toLowerCase().includes(q)
      )
    }
    return true
  })

  const showHero = !result && !loading && !error

  const counts = {
    total: violations.length,
    errors: violations.filter((v) => v.severity === "error").length,
    warnings: violations.filter((v) => v.severity === "warning").length,
    info: violations.filter((v) => v.severity === "info").length,
  }

  const MotionOrDiv = reducedMotion ? "div" : motion.div
  const animProps = reducedMotion
    ? {}
    : { initial: { opacity: 0 }, animate: { opacity: 1 } }

  return (
    <div className="min-h-screen bg-surface-0 text-content">
      <a
        href="#results-panel"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-brand focus:px-4 focus:py-2 focus:text-sm focus:text-white focus:outline-none"
      >
        Skip to results
      </a>

      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">Sentinel</h1>
          <button
            onClick={toggle}
            className="rounded-md p-2 text-muted hover:bg-surface-2 hover:text-content transition-colors"
            aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
          >
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </div>

        <AnalyzeForm onAnalyze={handleAnalyze} loading={loading} />

        {showHero && (
          <>
            <ExampleRepos onSelect={(repo) => handleAnalyze(repo, "main")} loading={loading} />
            <FeatureCards />
            <HowItWorks />
          </>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            role="alert"
            className="mt-4 rounded-md border border-error/30 bg-error/10 p-4 text-sm text-error"
          >
            <div className="flex items-start justify-between gap-3">
              <span>{error}</span>
              <div className="flex shrink-0 gap-2">
                {lastAnalyzed && (
                  <button
                    onClick={handleRetry}
                    className="inline-flex items-center gap-1 rounded bg-error/15 px-2 py-1 text-xs font-medium transition-colors hover:bg-error/25"
                  >
                    <RotateCcw className="h-3 w-3" />
                    Retry
                  </button>
                )}
                <button
                  onClick={() => setError("")}
                  className="rounded p-1 transition-colors hover:bg-error/15"
                  aria-label="Dismiss error"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {loading && (
          <div className="mt-6 space-y-5" aria-label="Loading analysis" role="status">
            <SkeletonCards />
            <SkeletonMetrics />
            <SkeletonTable />
          </div>
        )}

        {result && !loading && (
          <div
            ref={resultsRef}
            id="results-panel"
            tabIndex={-1}
            className="mt-6 space-y-5 outline-none"
          >
            <div aria-live="polite" aria-atomic="true" className="sr-only">
              Analysis complete. {counts.total} violations found: {counts.errors} errors, {counts.warnings} warnings, {counts.info} info.
            </div>

            <SummaryCards
              total={counts.total}
              errors={counts.errors}
              warnings={counts.warnings}
              info={counts.info}
              drift={result.drift_score}
            />

            {metrics && <MetricsBar metrics={metrics} />}

            <div
              role="tablist"
              aria-label="Analysis results"
              className="flex gap-2"
              onKeyDown={handleTabKeyDown}
            >
              {TABS.map((tab) => (
                <button
                  key={tab}
                  ref={(el) => { tabRefs.current[tab] = el }}
                  role="tab"
                  id={`tab-${tab}`}
                  aria-selected={activeTab === tab}
                  aria-controls={`panel-${tab}`}
                  tabIndex={activeTab === tab ? 0 : -1}
                  onClick={() => setActiveTab(tab)}
                  className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                    activeTab === tab
                      ? "bg-surface-2 text-content border border-border"
                      : "text-muted hover:text-content"
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </div>

            <MotionOrDiv
              {...animProps}
              role="tabpanel"
              id={`panel-${activeTab}`}
              aria-labelledby={`tab-${activeTab}`}
              className="outline-none"
            >
              {activeTab === "violations" ? (
                <ViolationsTab
                  violations={violations}
                  filtered={filtered}
                  severityFilter={severityFilter}
                  kindFilter={kindFilter}
                  search={search}
                  onSeverityChange={setSeverityFilter}
                  onKindChange={setKindFilter}
                  onSearchChange={setSearch}
                />
              ) : (
                <RemediationTab violations={violations} />
              )}
            </MotionOrDiv>
          </div>
        )}
      </div>
    </div>
  )
}
