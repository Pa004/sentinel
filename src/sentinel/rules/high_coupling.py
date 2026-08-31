"""High coupling rule: modules with an excessive number of dependents."""

from __future__ import annotations

from pathlib import Path

from sentinel.analyzers.coupling import fan_in
from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Severity, Violation, ViolationKind
from sentinel.manifest.mapper import LayerMapper
from sentinel.rules.base import Rule


class HighCouplingRule(Rule):
    """Flags modules whose fan-in (number of dependents) exceeds a threshold.

    A module with many dependents is a hot spot: changes ripple widely and it
    is hard to modify in isolation — distinct from a god module (total coupling).
    """

    def __init__(self, threshold: int = 8) -> None:
        self._threshold = threshold

    def check(
        self,
        graph: DependencyGraph,
        manifest: ArchitectureManifest,
        mapper: LayerMapper,
        root: Path,
    ) -> list[Violation]:
        violations: list[Violation] = []
        files = set(graph.nodes())
        for source in graph.nodes():
            for dep in graph.dependencies_of(source):
                files.add(dep.target)
        for file in files:
            incoming = fan_in(graph, file)
            if incoming > self._threshold:
                violations.append(
                    Violation(
                        rule="high-coupling",
                        kind=ViolationKind.HIGH_COUPLING,
                        evidence=f"{file} fan-in={incoming}",
                        components=(str(file),),
                        impact=(
                            f"module has {incoming} dependents; changes here "
                            "ripple across the codebase"
                        ),
                        recommendation=(
                            "reduce dependents by extracting narrow interfaces "
                            "or splitting responsibilities"
                        ),
                        severity=Severity.WARNING,
                    )
                )
        return violations
