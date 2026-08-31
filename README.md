# Sentinel

Architecture erosion detector. Compares intended vs observed architecture.

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

```bash
sentinel analyze <repo-path> --manifest <manifest.yaml>
sentinel graph <repo-path>
sentinel trend <repo-path> --from <sha> --to <sha>
```

## Development

```bash
ruff check .
pytest
```
