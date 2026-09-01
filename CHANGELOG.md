# Changelog

All notable changes to Sentinel are documented here.

## [0.2.0] - 2026-09-01

### Added

#### Frontend Features
- **Toast notifications** — success/error/info toasts with 4s auto-dismiss (`Toast.tsx`)
- **Keyboard shortcuts** — `1`/`2` switch tabs, `Escape` dismisses panels (`useKeyboardShortcuts.ts`)
- **History panel** — last 10 analyses stored in localStorage (`HistoryPanel.tsx`, `useHistory.ts`)
- **Share button** — copy analysis URL to clipboard (`ShareButton.tsx`)
- **Export** — download results as JSON or CSV (`ExportButton.tsx`)
- **Caching** — 5-minute client-side cache for repeated analyses (`api.ts`)
- **Performance tracking** — shows "Analyzed in X.Xs" (`usePerformance.ts`)
- **Analytics** — localStorage-based event tracking, max 50 events (`useAnalytics.ts`)
- **Responsive mobile cards** — improved violation cards with file count, line-clamp, component overflow (`ViolationsTab.tsx`)
- **Error boundary** — React class component with retry (`ErrorBoundary.tsx`)
- **Meta tags** — Open Graph + Twitter Card for social sharing (`index.html`)

#### Backend Improvements
- **Concurrency limiter** — `asyncio.Semaphore(3)` prevents resource exhaustion, returns 429 on limit
- **Input validation** — Pydantic validators for GitHub URL regex + branch sanitization
- **Git clone timeout** — 60s timeout on `git clone --depth=1`
- **FQN resolution** — Java and C# parsers return full FQN (`com.example.model.User` instead of `User`)

#### Infrastructure
- **CI pipeline** — GitHub Actions: lint (ruff), test matrix (Python 3.12 + 3.13, Ubuntu + Windows), frontend build
- **Pre-deploy script** — `scripts/deploy_check.py` validates lint, format, tests, build, security
- **Code splitting** — Manual Vite chunks: vendor (~182KB), motion (~133KB), index (~42KB)
- **Test isolation** — `afterEach(cleanup)` in test-setup.ts, `clearCache()` in api tests

### Fixed
- **Desktop expand bug** — nested `<button>` violation (aria-expanded on parent), `sm:hidden` on expanded details
- **Manifest rule keys** — `VALID_RULE_KEYS` expanded from 2 to 9 identifiers (hyphen style matching actual rules)
- **Float thresholds** — `rule_threshold()` returns `int | float` instead of truncating to `int`
- **AnimatePresence jsdom** — removed from mobile expanded content (animations don't resolve in jsdom)
- **API test pollution** — cache clearing between tests prevents cross-test state leakage

### Removed
- **LoadingState.tsx** — dead code, replaced by skeleton components

## [0.1.0] - 2026-08-30

### Added
- Initial release
- 8 architecture detection rules (layer violation, circular dependency, god module, high coupling, low cohesion, boundary crossing, React component, database leakage)
- tree-sitter parsers for TypeScript, JavaScript, Python, Java, C#
- Architecture manifest YAML format
- Drift score computation
- Git blame integration for origin commits
- CLI with 6 commands: analyze, graph, trend, history, report, serve
- HTML report generator with Chart.js
- FastAPI stateless backend
- React dashboard with Tailwind CSS v4
- Vitest + testing-library frontend tests
- 126 Python backend tests
