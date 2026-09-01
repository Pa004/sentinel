import { useState, useEffect } from "react"
import { Sun, Moon } from "lucide-react"
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

export default function App() {
  const { dark, toggle } = useTheme()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [activeTab, setActiveTab] = useState<"violations" | "remediation">("violations")
  const [severityFilter, setSeverityFilter] = useState("")
  const [kindFilter, setKindFilter] = useState("")
  const [search, setSearch] = useState("")

  const handleAnalyze = async (url: string, br: string) => {
    setLoading(true)
    setError("")
    setResult(null)
    try {
      const data = await analyze(url, br)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed")
    } finally {
      setLoading(false)
    }
  }

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

  return (
    <div className="min-h-screen bg-surface-0 text-content">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6">
        <div className="mb-6 flex items-center justify-between">
          <h1 className="text-xl font-bold tracking-tight">Sentinel</h1>
          <button
            onClick={toggle}
            className="rounded-md p-2 text-muted hover:bg-surface-2 hover:text-content transition-colors"
            aria-label="Toggle theme"
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
            className="mt-4 rounded-md border border-error/30 bg-error/10 p-4 text-sm text-error"
          >
            {error}
          </motion.div>
        )}

        {loading && (
          <div className="mt-6 space-y-5">
            <SkeletonCards />
            <SkeletonMetrics />
            <SkeletonTable />
          </div>
        )}

        {result && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 space-y-5"
          >
            <SummaryCards
              total={counts.total}
              errors={counts.errors}
              warnings={counts.warnings}
              info={counts.info}
              drift={result.drift_score}
            />

            {metrics && <MetricsBar metrics={metrics} />}

            <div className="flex gap-2">
              {(["violations", "remediation"] as const).map((tab) => (
                <button
                  key={tab}
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
          </motion.div>
        )}
      </div>
    </div>
  )
}
