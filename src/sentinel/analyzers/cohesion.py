"""Cohesion analysis: measures how related symbols are within a file."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.graph import DependencyGraph
from sentinel.domain.symbols import Symbol


def cohesion_score(
    file: Path,
    symbols: list[Symbol],
    graph: DependencyGraph,
) -> float:
    """Return a cohesion score between 0.0 (no internal references) and 1.0 (fully cohesive).

    A file is cohesive if its symbols reference each other.
    Score = (internal references) / (total possible references).
    """
    if len(symbols) < 2:
        return 1.0
    internal = 0
    deps = graph.dependencies_of(file)
    dep_targets = {d.target.name for d in deps}
    for sym in symbols:
        if sym.name in dep_targets:
            internal += 1
    total = len(symbols)
    return internal / total if total > 0 else 1.0
