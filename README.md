# Sentinel

Architecture erosion detector. Compares the **intended** architecture (declared in a YAML manifest)
against the **observed** architecture (extracted from the real dependency graph), then reports
violations and tracks regression across git history.

Built as a lightweight MVP: pure Python + tree-sitter, no Rust toolchain required.

## Supported languages

TypeScript/JavaScript, Python, Java, and C#. Imports/`using` directives are resolved
to files by matching the referenced module (or last FQN segment) against project file stems.

## Flow

```
Repository -> Parser -> Symbol Graph -> Dependency Graph -> Architecture Manifest
           -> Rule Engine -> Violation Engine -> Trend Analysis
```

## Installation

```bash
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

## Usage

```bash
# Analyze a repository against an architecture manifest
sentinel analyze <repo-path> --manifest <manifest.yaml> [--json] [--save]

# Print the dependency graph
sentinel graph <repo-path>

# Detect architectural regression across a commit range
sentinel trend <repo-path> --manifest <manifest.yaml> [--from <sha>] [--to <sha>]

# Show stored analysis runs
sentinel history <repo-path>

# Generate an HTML report with charts
sentinel report <repo-path> --manifest <manifest.yaml> [-o report.html]

# Serve the interactive report and REST API
sentinel serve <repo-path> --manifest <manifest.yaml> [--port 8000] [--db <path>]
```

### REST API

`sentinel serve` exposes a lightweight stdlib HTTP server (no dependencies beyond Python) with:

| Endpoint            | Description                                           |
|---------------------|-------------------------------------------------------|
| `GET /`             | Interactive HTML report generated on the fly           |
| `GET /api/runs`     | List of all stored analysis runs (JSON)                |
| `GET /api/runs/{id}`| Single run with full violations (JSON)                 |
| `GET /api/report.json` | Current analysis result (live from violation engine) |

The HTML report is interactive: filter by severity and kind, search, sort columns,
export to CSV, copy commit SHAs, and switch between stored runs (when served by `sentinel serve`).
Opened as a static file (`report.html` in `file://`), the report works exactly the same
but omits the run selector since no API is available.

## Architecture manifest

A manifest declares the layers and which other layers each one may depend on.
Directories are mapped to layers by their top-level name.

```yaml
layers:
  presentation:
    may_depend_on: [application]
  application:
    may_depend_on: [domain]
  domain: {}
```

Optional `rules` block tunes coupling thresholds:

```yaml
rules:
  god_module: { threshold: 12 }    # total coupling (fan-in + fan-out)
  high_coupling: { threshold: 5 }  # fan-in (number of dependents)
```

## Rules

Sentinel runs **eight** architectural detection rules:

- **Layer violation** -- a dependency crosses a layer boundary that the manifest forbids.
  This covers **database leakage** (e.g. domain layer importing from a persistence/database
  layer) when the manifest disallows the cross-layer dependency.
- **Circular dependency** -- a strongly-connected cycle across modules (Tarjan SCC).
- **God module** -- total coupling (fan-in + fan-out) exceeds the threshold.
- **High coupling** -- a module's fan-in (dependents) exceeds the threshold.
- **Low cohesion** -- intra-module cohesion drops below the threshold (LCOM heuristic
  over public symbols per file).
- **Boundary crossing** -- a file outside the dedicated layer imports a sentinel/marker
  file (e.g. `__sentinel__.py`).
- **React component** -- a file outside the UI layer imports a React component
  (heuristic: files containing JSX/React patterns imported from non-presentation layers).
- **Drift score** -- measures how the violation set changes between commits,
  flagging introduced and resolved violations (regression detection).

Every violation reports the **origin commit** (the last commit that touched the source
file carrying the offending dependency) when the analyzed path lives inside a git repo.

## Known limitations

- **Symlinks on Windows** -- the symlink-aware test is skipped on Windows unless
  `SENTINEL_TEST_SYMLINKS=1` is set (requires elevated privileges).
- **Multirun API availability** -- the run selector in the interactive HTML report only
  appears when served by `sentinel serve`. Opened as a static `file://` page, the report
  shows inline data only.
- **Cohesion analysis is heuristic** -- low cohesion detection uses a public-symbol
  LCOM heuristic at the file level, not full method/field body analysis. Accurate LCOM
  metrics would require deeper AST integration.

## Development

```bash
ruff check src tests
pytest
```

Views are verified against synthetic repos of known architecture (`GOOD`, `BAD`, `EVOLVING`)
so each violation is provably detected.
