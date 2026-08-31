"""Pure domain types for trend analysis."""

from __future__ import annotations

from dataclasses import dataclass, field

from sentinel.domain.violations import ViolationKind


@dataclass
class TrendPoint:
    """Snapshot of violation counts at a single point in history."""

    commit: str
    counts: dict[ViolationKind, int] = field(default_factory=dict)
    introduced: list[str] = field(default_factory=list)
    drift: float = 0.0

    def total(self) -> int:
        return sum(self.counts.values())
