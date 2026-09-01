"""Tests for high-coupling detection and configurable rule thresholds."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.graph import Dependency, DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest, Layer
from sentinel.domain.violations import ViolationKind
from sentinel.rules.high_coupling import HighCouplingRule
from sentinel.violation_engine import analyze_repository

MANIFEST = ArchitectureManifest(
    {
        "pkg": Layer("pkg", frozenset({"pkg"})),
    }
)


# Package layout as a temp dir: hub.py imported by 6 consumers.
def _write_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "pkg").mkdir(parents=True)
    (repo / "pkg" / "hub.py").write_text("def hub(): pass\n", encoding="utf-8")
    for i in range(6):
        (repo / "pkg" / f"consumer{i}.py").write_text("from hub import hub\n", encoding="utf-8")
    return repo


def test_high_coupling_rule_flags_hot_module() -> None:
    graph = DependencyGraph()
    hub = Path("/repo/hub.py")
    for i in range(6):
        src = Path(f"/repo/consumer{i}.py")
        graph.add_dependency(Dependency(src, hub, "from hub import hub", 1))
    rule = HighCouplingRule(threshold=3)
    violations = rule.check(graph, MANIFEST, None, Path("/repo"))  # type: ignore[arg-type]
    kinds = [v.kind for v in violations]
    assert ViolationKind.HIGH_COUPLING in kinds
    assert any("fan-in=6" in v.evidence for v in violations)


def test_high_coupling_rule_respects_threshold() -> None:
    graph = DependencyGraph()
    hub = Path("/repo/hub.py")
    for i in range(4):
        src = Path(f"/repo/consumer{i}.py")
        graph.add_dependency(Dependency(src, hub, "import hub", 1))
    # threshold above fan-in -> no violation
    assert HighCouplingRule(threshold=10).check(graph, MANIFEST, None, Path("/repo")) == []  # type: ignore[arg-type]
    # threshold below fan-in -> violation
    assert HighCouplingRule(threshold=2).check(graph, MANIFEST, None, Path("/repo")) != []  # type: ignore[arg-type]


def test_analyze_uses_manifest_threshold(tmp_path: Path) -> None:
    repo = _write_repo(tmp_path)
    # low threshold -> high-coupling flagged
    tight = ArchitectureManifest(MANIFEST.layers, {"high-coupling": {"threshold": 2}})
    result = analyze_repository(repo, tight)
    kinds = {v.kind for v in result.violations}
    assert ViolationKind.HIGH_COUPLING in kinds
    # default threshold (8) -> not flagged for 6 dependents
    default = ArchitectureManifest(MANIFEST.layers)
    result_default = analyze_repository(repo, default)
    kinds_default = {v.kind for v in result_default.violations}
    assert ViolationKind.HIGH_COUPLING not in kinds_default
