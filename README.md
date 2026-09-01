<div align="center">

# Sentinel

**Architecture erosion detector for modern codebases**

Compares the **intended** architecture against the **observed** architecture,
reports violations, and tracks regression across git history.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-138%20passed-brightgreen.svg)]()
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
| Drift score | Violations introduced or resolved between commits | info |

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
```

**No manifest?** Sentinel still runs 6 of 8 rules (all except layer violation and database leakage).

## Supported Languages

TypeScript, JavaScript, Python, Java, and C#. Imports are resolved to files by matching module references against project file stems.

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
├── src/sentinel/              # Core library
│   ├── parsers/               # tree-sitter language parsers
│   ├── analyzers/             # coupling, cohesion analysis
│   ├── rules/                 # 8 detection rules
│   ├── domain/                # Manifest, Violation types
│   ├── manifest/              # YAML loader
│   ├── persistence/           # SQLite run storage
│   ├── reports/               # HTML report generator
│   ├── violation_engine.py
│   ├── trend.py               # Regression detection
│   ├── cli.py                 # Typer CLI
│   └── server.py              # HTTP server
├── backend/                   # SaaS API (FastAPI, stateless)
├── frontend/                  # React dashboard
│   ├── src/
│   │   ├── components/        # UI components
│   │   │   ├── AnalyzeForm.tsx
│   │   │   ├── SummaryCards.tsx
│   │   │   ├── MetricsBar.tsx
│   │   │   ├── ViolationsTab.tsx
│   │   │   ├── RemediationTab.tsx
│   │   │   └── LoadingState.tsx
│   │   ├── __tests__/         # Vitest + testing-library
│   │   ├── api.ts             # Backend client
│   │   ├── App.tsx            # Root component
│   │   └── index.css          # Tailwind v4 theme
│   └── package.json
├── tests/                     # 126 Python tests
└── sentinel.yaml              # Example manifest
```

### Frontend Stack

- **Tailwind CSS v4** — CSS-first config, no `tailwind.config.js`
- **Geist Sans + Mono** — typography
- **lucide-react** — icons
- **framer-motion** — animations (shimmer, blur-fade, number-ticker)
- **Vitest + testing-library** — 12 frontend tests
- **Dark/Light mode** — toggle with `localStorage` persistence

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Make changes with tests
4. Run `ruff check src tests && ruff format src tests && python -m pytest tests/`
5. Open a PR against `main`

## License

MIT
