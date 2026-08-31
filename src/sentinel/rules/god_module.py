"""God module rule: modules whose coupling exceeds a threshold."""

from __future__ import annotations

from pathlib import Path

from sentinel.analyzers.coupling import coupling_scores
from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Severity, Violation, ViolationKind
from sentinel.manifest.mapper import LayerMapper
from sentinel.rules.base import Rule


class GodModuleRule(Rule):
    """Flags modules whose total coupling (fan-in + fan-out) exceeds a
    configurable threshold — a signal of a god module."""

    def __init__(self, threshold: int = 10) -> None:
        self._threshold = threshold

    def check(
        self,
        graph: DependencyGraph,
        manifest: ArchitectureManifest,
        mapper: LayerMapper,
        root: Path,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for file, score in coupling_scores(graph).items():
            if score > self._threshold:
                violations.append(
                    Violation(
                        rule="god-module",
                        kind=ViolationKind.GOD_MODULE,
                        evidence=f"{file} coupling={score}",
                        components=(str(file),),
                        impact=f"module is a hub with {score} connections; hard to test and change",
                        recommendation="split the module along cohesive responsibilities",
                        severity=Severity.WARNING,
                    )
                )
        return violations
