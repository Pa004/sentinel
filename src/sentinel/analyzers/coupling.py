"""Coupling metrics over a dependency graph."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.graph import DependencyGraph


def fan_out(graph: DependencyGraph, file: Path) -> int:
    """Number of distinct modules a file depends on."""
    return len(graph.dependencies_of(file))


def fan_in(graph: DependencyGraph, file: Path) -> int:
    """Number of modules that depend on a file."""
    count = 0
    for source in graph.nodes():
        for dep in graph.dependencies_of(source):
            if dep.target == file:
                count += 1
    return count


def coupling_scores(graph: DependencyGraph) -> dict[Path, int]:
    """Total coupling (fan-in + fan-out) per file, for god module detection."""
    scores: dict[Path, int] = {}
    for source in graph.nodes():
        scores[source] = scores.get(source, 0) + len(graph.dependencies_of(source))
    for source in graph.nodes():
        for dep in graph.dependencies_of(source):
            scores[dep.target] = scores.get(dep.target, 0) + 1
    return scores
