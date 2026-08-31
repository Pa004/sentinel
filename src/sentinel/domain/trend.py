"""Pure domain types for trend analysis."""

from __future__ import annotations

from dataclasses import dataclass, field

from sentinel.domain.violations import ViolationKind


@dataclass(frozen=True)
class TrendPoint:
    """Snapshot of violation counts at a single point in history."""

    commit: str
    counts: dict[ViolationKind, int] = field(default_factory=dict)

    def total(self) -> int:
        return sum(self.counts.values())
