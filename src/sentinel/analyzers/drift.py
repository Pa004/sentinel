"""Drift analysis: measures how far the observed architecture is from the intended."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.manifest.mapper import LayerMapper


@dataclass(frozen=True)
class DriftScore:
    """Result of architecture drift analysis."""

    score: float
    illegal_count: int
    total_count: int


def drift_score(
    graph: DependencyGraph,
    mapper: LayerMapper,
    manifest: ArchitectureManifest,
    root: Path,
) -> DriftScore:
    """Compute architecture drift as a ratio of illegal layer edges to total layer edges.

    `score` ranges from 0.0 (all edges legal) to 1.0 (all edges illegal).
    Edges whose source or target file maps to an unknown layer are ignored.
    """
    illegal = 0
    total = 0
    for source, deps in graph.outgoing.items():
        src_layer = mapper.layer_for(source, root)
        for dep in deps:
            tgt_layer = mapper.layer_for(dep.target, root)
            if src_layer == tgt_layer:
                continue
            if not manifest.has_layer(src_layer) or not manifest.has_layer(tgt_layer):
                continue
            total += 1
            if not manifest.allows(src_layer, tgt_layer):
                illegal += 1
    if total == 0:
        return DriftScore(score=0.0, illegal_count=0, total_count=0)
    return DriftScore(
        score=illegal / total,
        illegal_count=illegal,
        total_count=total,
    )
