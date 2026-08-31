"""Aggregated metrics for an architecture analysis run."""

from __future__ import annotations

from dataclasses import dataclass

from sentinel.domain.graph import DependencyGraph
from sentinel.domain.violations import Violation, ViolationKind


@dataclass(frozen=True)
class RunMetrics:
    """Aggregated metrics computed from a set of violations and the dependency graph.

    Matches the spec metrics: violations, cycle count, layer violations,
    coupling, drift.
    """

    total_violations: int
    error_count: int
    warning_count: int
    info_count: int
    cycle_count: int
    layer_violation_count: int
    god_module_count: int
    high_coupling_count: int
    low_cohesion_count: int
    boundary_crossing_count: int
    database_leakage_count: int
    drift_score: float
    node_count: int
    edge_count: int
    avg_coupling: float

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return {
            "total_violations": self.total_violations,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "cycle_count": self.cycle_count,
            "layer_violation_count": self.layer_violation_count,
            "god_module_count": self.god_module_count,
            "high_coupling_count": self.high_coupling_count,
            "low_cohesion_count": self.low_cohesion_count,
            "boundary_crossing_count": self.boundary_crossing_count,
            "database_leakage_count": self.database_leakage_count,
            "drift_score": self.drift_score,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "avg_coupling": self.avg_coupling,
        }

    @classmethod
    def from_dict(cls, d: dict) -> RunMetrics:
        """Deserialize from a dict (e.g. from SQLite JSON column)."""
        return cls(**{k: d[k] for k in cls.__dataclass_fields__})


def compute_metrics(
    violations: list[Violation],
    graph: DependencyGraph,
    drift: float,
) -> RunMetrics:
    """Compute aggregated metrics from violations and the dependency graph."""
    kind_counts: dict[str, int] = {}
    for v in violations:
        kind_counts[v.kind.value] = kind_counts.get(v.kind.value, 0) + 1

    nodes = graph.nodes()
    node_count = len(nodes)
    total_edges = sum(len(graph.dependencies_of(n)) for n in nodes)

    avg_coupling = total_edges / node_count if node_count > 0 else 0.0

    return RunMetrics(
        total_violations=len(violations),
        error_count=sum(1 for v in violations if v.severity.value == "error"),
        warning_count=sum(1 for v in violations if v.severity.value == "warning"),
        info_count=sum(1 for v in violations if v.severity.value == "info"),
        cycle_count=kind_counts.get(ViolationKind.CIRCULAR_DEPENDENCY, 0),
        layer_violation_count=kind_counts.get(ViolationKind.LAYER_VIOLATION, 0),
        god_module_count=kind_counts.get(ViolationKind.GOD_MODULE, 0),
        high_coupling_count=kind_counts.get(ViolationKind.HIGH_COUPLING, 0),
        low_cohesion_count=kind_counts.get(ViolationKind.LOW_COHESION, 0),
        boundary_crossing_count=kind_counts.get(ViolationKind.BOUNDARY_CROSSING, 0),
        database_leakage_count=kind_counts.get(ViolationKind.DATABASE_LEAKAGE, 0),
        drift_score=drift,
        node_count=node_count,
        edge_count=total_edges,
        avg_coupling=round(avg_coupling, 2),
    )
