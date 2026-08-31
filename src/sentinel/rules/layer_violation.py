"""Layer violation rule: illegal dependency across architecture layers."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Severity, Violation, ViolationKind
from sentinel.manifest.mapper import LayerMapper
from sentinel.rules.base import Rule


class LayerViolationRule(Rule):
    """Emits a violation for every edge whose source layer may not depend
    on the target layer according to the manifest."""

    def check(
        self,
        graph: DependencyGraph,
        manifest: ArchitectureManifest,
        mapper: LayerMapper,
        root: Path,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for source in graph.nodes():
            src_layer = mapper.layer_of_module(source, root)
            for dep in graph.dependencies_of(source):
                dst_layer = mapper.layer_of_module(dep.target, root)
                if src_layer == dst_layer:
                    continue
                if not manifest.allows(src_layer, dst_layer):
                    violations.append(
                        Violation(
                            rule="layer-violation",
                            kind=ViolationKind.LAYER_VIOLATION,
                            evidence=f"{dep.source}:{dep.line} -> {dep.target} ({dep.evidence})",
                            components=(str(src_layer), str(dst_layer)),
                            impact=(
                                f"{src_layer} bypasses the allowed boundary to reach "
                                f"{dst_layer}; violates declared layering"
                            ),
                            recommendation=(
                                f"Route this dependency through an intermediate layer "
                                f"allowed to reach {dst_layer}"
                            ),
                            severity=Severity.ERROR,
                        )
                    )
        return violations
