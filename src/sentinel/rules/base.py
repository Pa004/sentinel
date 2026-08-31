"""Rule interface for the rule engine."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Violation
from sentinel.manifest.mapper import LayerMapper


class Rule(ABC):
    """A rule inspects the observed graph and emits violations."""

    @abstractmethod
    def check(
        self,
        graph: DependencyGraph,
        manifest: ArchitectureManifest,
        mapper: LayerMapper,
        root: Path,
    ) -> list[Violation]: ...
