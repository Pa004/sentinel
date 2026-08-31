"""Boundary crossing rule: flags imports that cross architectural boundaries."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Severity, Violation, ViolationKind
from sentinel.manifest.mapper import LayerMapper
from sentinel.rules.base import Rule


class BoundaryCrossingRule(Rule):
    """Detect imports that cross declared architectural boundaries.

    Unlike LayerViolation (which checks layer-to-layer rules), this flags
    every individual import that crosses from one layer to another,
    providing granular evidence for boundary erosion.
    """

    def check(
        self,
        graph: DependencyGraph,
        manifest: ArchitectureManifest,
        mapper: LayerMapper,
        root: Path,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for source in graph.nodes():
            source_layer = mapper.layer_for(source, root)
            if source_layer == "default":
                continue
            for dep in graph.dependencies_of(source):
                target_layer = mapper.layer_for(dep.target, root)
                if target_layer == "default":
                    continue
                if source_layer == target_layer:
                    continue
                if not manifest.allows(source_layer, target_layer):
                    violations.append(
                        Violation(
                            rule="boundary_crossing",
                            kind=ViolationKind.BOUNDARY_CROSSING,
                            evidence=f"{dep.evidence} (line {dep.line})",
                            components=(str(source), str(dep.target)),
                            impact=f"{source_layer} -> {target_layer}: boundary violated",
                            recommendation=(
                                f"Move {dep.target.name} to {source_layer} or update manifest"
                            ),
                            severity=Severity.WARNING,
                        )
                    )
        return violations
