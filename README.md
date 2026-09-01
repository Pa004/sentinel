<div align="center">

# Sentinel

**Architecture erosion detector for modern codebases**

Compares the **intended** architecture against the **observed** architecture,
reports violations, and tracks regression across git history.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-141%20passed-brightgreen.svg)]()
[![Live Demo](https://img.shields.io/badge/demo-live-ff69b4.svg)](https://sentinel-zxr.pages.dev)

[**Try it live**](https://sentinel-zxr.pages.dev) — no installation required

</div>

---

## What is Sentinel?

Sentinel analyzes your repository's dependency graph and compares it against a declared architecture manifest. When code crosses layer boundaries, creates circular dependencies, or violates structural rules, Sentinel catches it.

**8 detection rules:**

| Rule | What it catches | Severity |
|------|----------------|----------|
| Layer violation | Dependencies crossing forbidden layer boundaries | error |
| Circular dependency | Cycles across modules (Tarjan SCC) | error |
| God module | Module with too many connections (fan-in + fan-out) | warning |
| High coupling | Module depended on by too many others | warning |
| Low cohesion | Module with poor internal cohesion (LCOM heuristic) | warning |
| Boundary crossing | Non-layer code importing sentinel markers | warning |
| React component | Non-UI layer importing React components | warning |
| Database leakage | Direct dependencies to data-layer modules | warning |

Every violation includes the **origin commit** — the last commit that touched the offending file.

## Quick Start

### Option 1: Web (recommended)

Go to **[sentinel-zxr.pages.dev](https://sentinel-zxr.pages.dev)**, paste a GitHub repo URL, and click Analyze.

### Option 2: CLI

```bash
git clone https://github.com/Pa004/sentinel.git
cd sentinel

python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

pip install -e ".[dev]"

# Analyze a repo
sentinel analyze /path/to/repo --manifest sentinel.yaml

# Generate HTML report
sentinel report /path/to/repo --manifest sentinel.yaml -o report.html

# Detect regression across commits
sentinel trend /path/to/repo --manifest sentinel.yaml --from abc123 --to def456
```

### Option 3: Docker

```bash
docker build -t sentinel .
docker run --rm -v /path/to/repo:/repo sentinel analyze /repo --manifest /repo/sentinel.yaml
```

## Architecture Manifest

Declare your intended architecture in `sentinel.yaml`:

```yaml
layers:
  presentation:
    may_depend_on: [application]
  application:
    may_depend_on: [domain]
  domain: {}
```

Optional tuning:

```yaml
rules:
  god_module: { threshold: 12 }    # total coupling (fan-in + fan-out)
  high_coupling: { threshold: 5 }  # fan-in (number of dependents)
  low_cohesion: { threshold: 0.3 } # cohesion score (0.0-1.0)
  boundary_crossing: { threshold: 3 }
  react_component: { max_lines: 150, max_props: 8 }
  database_leakage: { threshold: 2 }
```

**No manifest?** Sentinel still runs 6 of 8 rules (all except layer violation and database leakage).

## Supported Languages

TypeScript, JavaScript, Python, Java, and C#. Imports are resolved to files by matching module references against project file stems. Full FQN resolution for Java (`com.example.model.User`) and C# (`Namespace.Class`).

## How It Works

```
Repository
  → Parser (tree-sitter)
    → Symbol Graph
      → Dependency Graph
        → Architecture Manifest comparison
          → Rule Engine (8 rules)
            → Violation Engine
              → Trend Analysis (regression detection)
```

### vs SonarQube

| | Sentinel | SonarQube |
|---|---|---|
| Focus | Architecture erosion | Code quality / bugs |
| Setup | `pip install` or web | Java server + DB + plugins |
| Architecture rules | 8 built-in, YAML-configurable | Via custom plugins |
| Cost | Free (SaaS + CLI) | Free tier limited, paid for teams |
| Languages | TS, JS, Python, Java, C# | 20+ via plugins |

## Deployment

Sentinel runs as a stateless SaaS:

- **Backend**: FastAPI on SnapDeploy (auto-sleep, Docker)
- **Frontend**: React on Cloudflare Pages (free tier)

The backend has no database or auth — a single `POST /api/analyze` endpoint clones the repo, runs analysis, and returns results.

## Frontend Features

- **Toast notifications** — success/error/info with auto-dismiss
- **Keyboard shortcuts** — `1`/`2` switch tabs, `Escape` dismisses
- **History panel** — last 10 analyses stored in localStorage
- **Share button** — copy analysis URL to clipboard
- **Export** — download results as JSON or CSV
- **Caching** — 5-minute client-side cache for repeated analyses
- **Performance tracking** — shows analysis duration
- **Responsive design** — mobile-optimized violation cards
- **Dark/Light mode** — toggle with localStorage persistence
- **Error boundary** — graceful recovery from rendering errors

## CI/CD

GitHub Actions runs on every push to `main` and every PR:

| Job | What it runs |
|-----|-------------|
| `lint` | `ruff check` + `ruff format --check` on backend |
| `test` | `pytest` on Python 3.12 + 3.13 (Ubuntu + Windows matrix) |
| `dashboard` | `npm run test` + `npm run build` on frontend |

Pre-deploy validation:

```bash
python scripts/deploy_check.py
```

Runs lint, format, tests, frontend build, and security checks before deployment.

## Development

```bash
# Backend
ruff check src tests
ruff format src tests
python -m pytest tests/ -v

# Frontend
cd frontend
npm install
npm run dev      # local dev server
npm run build    # production build
npm run test     # frontend tests (Vitest)
npm run lint     # oxlint
```

Tests use synthetic repos of known architecture (`GOOD`, `BAD`, `EVOLVING`) so every violation is provably detected.

### Project Structure

```
sentinel/
├── src/sentinel/                  # Core library
│   ├── parsers/                   # tree-sitter language parsers
│   │   ├── base.py                # Parser ABC
│   │   ├── registry.py            # Extension-to-parser mapping
│   │   ├── typescript.py          # TS/JS parser
│   │   ├── python_lang.py         # Python parser
│   │   ├── java.py                # Java parser (full FQN)
│   │   └── csharp.py              # C# parser (full FQN)
│   ├── analyzers/                 # coupling, cohesion, drift analysis
│   ├── rules/                     # 8 detection rules
│   ├── domain/                    # Manifest, Violation, Graph types
│   ├── manifest/                  # YAML loader + layer mapper
│   ├── persistence/               # SQLite run storage
│   ├── reports/                   # HTML report generator
│   ├── violation_engine.py        # Orchestrates analysis pipeline
│   ├── trend.py                   # Regression detection
│   ├── git_origin.py              # Git blame integration
│   ├── cli.py                     # Typer CLI (6 commands)
│   └── server.py                  # stdlib HTTP server
├── backend/                       # SaaS API (FastAPI, stateless)
│   ├── main.py                    # FastAPI app + CORS
│   ├── config.py                  # Pydantic settings
│   ├── routers/analyses.py        # POST /api/analyze
│   └── services/analysis.py       # Clone + analyze + cleanup
├── frontend/                      # React dashboard
│   ├── src/
│   │   ├── components/            # 16 UI components
│   │   │   ├── AnalyzeForm.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── ExportButton.tsx
│   │   │   ├── HistoryPanel.tsx
│   │   │   ├── ShareButton.tsx
│   │   │   ├── Toast.tsx
│   │   │   ├── ViolationsTab.tsx
│   │   │   └── ...
│   │   ├── hooks/                 # 5 custom hooks
│   │   │   ├── useAnalytics.ts
│   │   │   ├── useHistory.ts
│   │   │   ├── useKeyboardShortcuts.ts
│   │   │   ├── usePerformance.ts
│   │   │   └── usePrefersReducedMotion.ts
│   │   ├── __tests__/             # Vitest + testing-library
│   │   ├── api.ts                 # Backend client + cache
│   │   └── App.tsx                # Root component
│   └── package.json
├── tests/                         # 126 Python tests
├── scripts/deploy_check.py        # Pre-deploy validation
├── .github/workflows/ci.yml       # CI pipeline
├── Dockerfile                     # Multi-stage build
├── fly.toml                       # Fly.io config
├── .env.example                   # Environment variables
└── pyproject.toml                 # Package config
```

### Frontend Stack

- **React 19** — UI framework
- **TypeScript 6.0** — type safety
- **Vite 8.2** — build tool with manual chunks
- **Tailwind CSS v4** — CSS-first config, no `tailwind.config.js`
- **Geist Sans + Mono** — typography
- **lucide-react** — icons
- **framer-motion** — animations
- **Vitest 4.1 + testing-library** — 15 frontend tests

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make changes with tests
4. Run backend checks: `ruff check src tests && ruff format src tests && python -m pytest tests/`
5. Run frontend checks: `cd frontend && npm run test && npm run build`
6. Open a PR against `main`

## License

[MIT](LICENSE)
