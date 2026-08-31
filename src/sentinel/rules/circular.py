"""Circular dependency rule using Tarjan's strongly connected components."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Severity, Violation, ViolationKind
from sentinel.manifest.mapper import LayerMapper
from sentinel.rules.base import Rule


class CircularDependencyRule(Rule):
    """Emits a violation for each strongly connected component (cycle) of
    size >= 2 in the observed dependency graph."""

    def check(
        self,
        graph: DependencyGraph,
        manifest: ArchitectureManifest,
        mapper: LayerMapper,
        root: Path,
    ) -> list[Violation]:
        components = _strongly_connected_components(graph)
        violations: list[Violation] = []
        for comp in components:
            if len(comp) < 2:
                continue
            members = ", ".join(str(p) for p in sorted(comp))
            violations.append(
                Violation(
                    rule="circular-dependency",
                    kind=ViolationKind.CIRCULAR_DEPENDENCY,
                    evidence=f"cycle among: {members}",
                    components=tuple(str(p) for p in sorted(comp)),
                    impact="mutual imports make modules hard to reason about, test and evolve",
                    recommendation=(
                        "break the cycle by extracting a shared dependency or inverting one edge"
                    ),
                    severity=Severity.WARNING,
                )
            )
        return violations


def _strongly_connected_components(graph: DependencyGraph) -> list[set[Path]]:
    index: dict[Path, int] = {}
    lowlink: dict[Path, int] = {}
    on_stack: set[Path] = set()
    stack: list[Path] = []
    components: list[set[Path]] = []
    counter = [0]

    def strongconnect(node: Path, deps: dict[Path, list[Path]]) -> None:
        index[node] = counter[0]
        lowlink[node] = counter[0]
        counter[0] += 1
        stack.append(node)
        on_stack.add(node)

        for dep in deps.get(node, ()):
            if dep == node:
                continue
            if dep not in index:
                strongconnect(dep, deps)
                lowlink[node] = min(lowlink[node], lowlink[dep])
            elif dep in on_stack:
                lowlink[node] = min(lowlink[node], index[dep])

        if lowlink[node] == index[node]:
            comp: set[Path] = set()
            while True:
                w = stack.pop()
                on_stack.remove(w)
                comp.add(w)
                if w == node:
                    break
            components.append(comp)

    adjacency: dict[Path, list[Path]] = {
        source: [dep.target for dep in graph.dependencies_of(source) if dep.target != source]
        for source in graph.nodes()
    }
    for node in graph.nodes():
        if node not in index:
            strongconnect(node, adjacency)
    return components
