"""Pure domain types for violations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    """Severity ranking of a violation."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ViolationKind(StrEnum):
    """Kinds of architectural violations the rule engine can emit."""

    LAYER_VIOLATION = "layer_violation"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    GOD_MODULE = "god_module"
    HIGH_COUPLING = "high_coupling"
    LOW_COHESION = "low_cohesion"
    BOUNDARY_CROSSING = "boundary_crossing"


@dataclass(frozen=True)
class Violation:
    """A detected architectural violation.

    Mirror of the product spec (#174-181):
    - rule: which rule fired
    - evidence: where it was observed
    - components: the modules/layers involved
    - impact: textual consequence
    - commit: origin commit (filled by trend analysis)
    - recommendation: remediation hint
    """

    rule: str
    kind: ViolationKind
    evidence: str
    components: tuple[str, ...]
    impact: str
    recommendation: str
    severity: Severity = Severity.WARNING
    commit: str | None = None
