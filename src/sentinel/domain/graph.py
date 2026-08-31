"""Pure domain types for the dependency graph between modules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Dependency:
    """A directed dependency edge from one module (file) to another.

    `evidence` points at the exact source location where the reference was
    declared (import/require statement), used to trace lineage.
    """

    source: Path
    target: Path
    evidence: str
    line: int

    @property
    def module(self) -> Path:
        return self.source


@dataclass
class DependencyGraph:
    """Directed graph over repository modules (files), keyed by source file."""

    outgoing: dict[Path, list[Dependency]] = field(default_factory=dict)

    def nodes(self) -> tuple[Path, ...]:
        return tuple(sorted(self.outgoing.keys()))

    def add_dependency(self, dep: Dependency) -> None:
        self.outgoing.setdefault(dep.source, [])
        if dep not in self.outgoing[dep.source]:
            self.outgoing[dep.source].append(dep)

    def mentions(self, file: Path) -> bool:
        """Whether a file appears as a node in the graph."""
        return file in self.outgoing

    def dependencies_of(self, file: Path) -> tuple[Dependency, ...]:
        return tuple(self.outgoing.get(file, ()))

    def merge(self, other: DependencyGraph) -> None:
        for deps in other.outgoing.values():
            for dep in deps:
                self.add_dependency(dep)
