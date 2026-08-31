# Sentinel

Architecture erosion detector. Compares the **intended** architecture (declared in a YAML manifest)
against the **observed** architecture (extracted from the real dependency graph), then reports
violations and tracks regression across git history.

Built as a lightweight MVP: pure Python + tree-sitter, no Rust toolchain required.

## Flow

```
Repository → Parser → Symbol Graph → Dependency Graph → Architecture Manifest
           → Rule Engine → Violation Engine → Trend Analysis
```

## Installation

```bash
python -m venv .venv
.\.venv\Scripts\pip install -e ".[dev]"
```

## Usage

```bash
# Analyze a repository against an architecture manifest
sentinel analyze <repo-path> --manifest <manifest.yaml> [--json]

# Print the dependency graph
sentinel graph <repo-path>

# Detect architectural regression across a commit range
sentinel trend <repo-path> --manifest <manifest.yaml> [--from <sha>] [--to <sha>]
```

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

## Rules

- **Layer violation** — a dependency crosses a layer boundary that the manifest forbids.
- **Circular dependency** — a strongly-connected cycle across modules (Tarjan SCC).
- **God module** — a module with an excessive fan-in (too many dependents).

## Development

```bash
ruff check src tests
pytest
```

Views are verified against synthetic repos of known architecture (`GOOD`, `BAD`, `EVOLVING`)
so each violation is provably detected.
