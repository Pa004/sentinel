"""JSON serialization of an analysis result."""

from __future__ import annotations

import json
from typing import Any

from sentinel.violation_engine import AnalysisResult


def _violation_to_dict(v: Any) -> dict[str, Any]:
    return {
        "rule": v.rule,
        "kind": v.kind.value,
        "severity": v.severity.value,
        "evidence": v.evidence,
        "components": list(v.components),
        "impact": v.impact,
        "recommendation": v.recommendation,
        "commit": v.commit,
    }


def serialize(result: AnalysisResult) -> str:
    """Serialize an AnalysisResult to a JSON string."""
    payload = {
        "violations": [_violation_to_dict(v) for v in result.violations],
        "total": len(result.violations),
        "nodes": len(result.graph.nodes()),
    }
    return json.dumps(payload, indent=2)
