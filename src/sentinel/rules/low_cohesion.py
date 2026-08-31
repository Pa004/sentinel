"""Low cohesion rule: flags files with many symbols but few internal references."""

from __future__ import annotations

from pathlib import Path

from sentinel.analyzers.cohesion import cohesion_score
from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Severity, Violation, ViolationKind
from sentinel.manifest.mapper import LayerMapper
from sentinel.rules.base import Rule


class LowCohesionRule(Rule):
    """Detect files with low internal cohesion (many unrelated symbols)."""

    def __init__(self, threshold: float = 0.3, min_symbols: int = 5) -> None:
        self._threshold = threshold
        self._min_symbols = min_symbols

    def check(
        self,
        graph: DependencyGraph,
        manifest: ArchitectureManifest,
        mapper: LayerMapper,
        root: Path,
    ) -> list[Violation]:
        from sentinel.analyzers.symbol_builder import build_symbol_graph
        from sentinel.parsers.registry import source_files

        files = source_files(root)
        symbol_graph = build_symbol_graph(files)
        violations: list[Violation] = []
        for file in symbol_graph.all_files():
            symbols = list(symbol_graph.symbols_in(file))
            if len(symbols) < self._min_symbols:
                continue
            score = cohesion_score(file, symbols, graph)
            if score < self._threshold:
                violations.append(
                    Violation(
                        rule="low_cohesion",
                        kind=ViolationKind.LOW_COHESION,
                        evidence=f"{file.name}: cohesion={score:.2f}, symbols={len(symbols)}",
                        components=(str(file),),
                        impact=(
                            f"File has {len(symbols)} symbols "
                            f"with only {score:.0%} internal references"
                        ),
                        recommendation=f"Split {file.name} into smaller, focused modules",
                        severity=Severity.WARNING,
                    )
                )
        return violations
