"""React component rules: flags oversized components and prop drilling."""

from __future__ import annotations

from pathlib import Path

from sentinel.analyzers.react_analyzer import detect_react_component
from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Severity, Violation, ViolationKind
from sentinel.manifest.mapper import LayerMapper
from sentinel.parsers.registry import source_files
from sentinel.rules.base import Rule


class ReactComponentRule(Rule):
    """Detect React component issues: oversized components, too many props."""

    def __init__(
        self,
        max_lines: int = 150,
        max_props: int = 8,
    ) -> None:
        self._max_lines = max_lines
        self._max_props = max_props

    def check(
        self,
        graph: DependencyGraph,
        manifest: ArchitectureManifest,
        mapper: LayerMapper,
        root: Path,
    ) -> list[Violation]:
        violations: list[Violation] = []
        files = source_files(root)
        for source in files:
            if source.suffix not in {".tsx", ".jsx"}:
                continue
            component = detect_react_component(source)
            if component is None:
                continue
            if component.line_count > self._max_lines:
                violations.append(
                    Violation(
                        rule="react_oversized_component",
                        kind=ViolationKind.GOD_MODULE,
                        evidence=(
                            f"{component.name}: {component.line_count} lines"
                        ),
                        components=(str(source),),
                        impact=(
                            f"Component exceeds {self._max_lines} lines, "
                            "hard to maintain"
                        ),
                        recommendation=(
                            f"Split {component.name} into smaller components"
                        ),
                        severity=Severity.WARNING,
                    )
                )
            if component.prop_count > self._max_props:
                violations.append(
                    Violation(
                        rule="react_too_many_props",
                        kind=ViolationKind.HIGH_COUPLING,
                        evidence=(
                            f"{component.name}: {component.prop_count} props"
                        ),
                        components=(str(source),),
                        impact=(
                            f"Component accepts more than {self._max_props} props, "
                            "indicates tight coupling"
                        ),
                        recommendation=(
                            f"Reduce props for {component.name} using "
                            "composition or context"
                        ),
                        severity=Severity.WARNING,
                    )
                )
        return violations
