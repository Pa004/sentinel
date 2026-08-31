"""Violation engine: runs all rules over the observed graph."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from sentinel.analyzers.dependency_extractor import build_dependency_graph
from sentinel.analyzers.drift import drift_score as compute_drift
from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Violation
from sentinel.git_origin import last_commit_sha, source_path_from_evidence
from sentinel.manifest.loader import load_manifest
from sentinel.manifest.mapper import LayerMapper, LayerRule
from sentinel.parsers.registry import source_files
from sentinel.rules.base import Rule
from sentinel.rules.boundary_crossing import BoundaryCrossingRule
from sentinel.rules.circular import CircularDependencyRule
from sentinel.rules.god_module import GodModuleRule
from sentinel.rules.high_coupling import HighCouplingRule
from sentinel.rules.layer_violation import LayerViolationRule
from sentinel.rules.low_cohesion import LowCohesionRule
from sentinel.rules.react_component import ReactComponentRule

GOD_MODULE_DEFAULT = 10
HIGH_COUPLING_DEFAULT = 8
LOW_COHESION_THRESHOLD = 0.3
LOW_COHESION_MIN_SYMBOLS = 5
REACT_MAX_LINES = 150
REACT_MAX_PROPS = 8


class AnalysisResult:
    """The result of running the violation engine over a repository."""

    def __init__(
        self,
        graph: DependencyGraph,
        violations: list[Violation],
        drift: float = 0.0,
    ) -> None:
        self.graph = graph
        self.violations = violations
        self.drift = drift

    def by_severity(self) -> dict[str, list[Violation]]:
        result: dict[str, list[Violation]] = {}
        for v in self.violations:
            result.setdefault(v.severity.value, []).append(v)
        return result


def _default_layer_rules(manifest: ArchitectureManifest) -> tuple[LayerRule, ...]:
    """Derive a rule per manifest layer mapping its directory (same name)."""
    return tuple(
        LayerRule(name, (f"{name}/",))
        for name in manifest.layer_names()
    )


def _default_rules(manifest: ArchitectureManifest) -> tuple[Rule, ...]:
    """Build the standard rule set, honoring per-rule thresholds from the manifest."""
    return (
        LayerViolationRule(),
        CircularDependencyRule(),
        GodModuleRule(manifest.rule_threshold("god_module", GOD_MODULE_DEFAULT)),
        HighCouplingRule(manifest.rule_threshold("high_coupling", HIGH_COUPLING_DEFAULT)),
        LowCohesionRule(
            threshold=manifest.rule_threshold(
                "low_cohesion", LOW_COHESION_THRESHOLD
            ),
            min_symbols=manifest.rule_threshold(
                "low_cohesion_min_symbols", LOW_COHESION_MIN_SYMBOLS
            ),
        ),
        BoundaryCrossingRule(),
        ReactComponentRule(
            max_lines=manifest.rule_threshold("react_max_lines", REACT_MAX_LINES),
            max_props=manifest.rule_threshold("react_max_props", REACT_MAX_PROPS),
        ),
    )


def _attach_commit_origins(
    violations: list[Violation], git_root: Path
) -> list[Violation]:
    """Fill in the commit where each violation's source file was last changed."""

    def with_commit(v: Violation) -> Violation:
        if v.commit is not None:
            return v
        source = source_path_from_evidence(v.evidence)
        if source is None:
            return v
        try:
            rel = source.relative_to(git_root)
        except ValueError:
            return v
        sha = last_commit_sha(git_root, rel)
        if sha is None:
            return v
        return replace(v, commit=sha)

    return [with_commit(v) for v in violations]


def analyze_repository(
    root: Path,
    manifest: ArchitectureManifest,
    rules: tuple[Rule, ...] | None = None,
    layer_rules: tuple[LayerRule, ...] | None = None,
    git_root: Path | None = None,
) -> AnalysisResult:
    """Run the full pipeline: parse files, build the graph, apply rules."""
    files = source_files(root)
    graph = build_dependency_graph(files)
    if rules is None:
        rules = _default_rules(manifest)
    if layer_rules is None:
        layer_rules = _default_layer_rules(manifest)
    mapper = LayerMapper(manifest, layer_rules)

    violations: list[Violation] = []
    for rule in rules:
        violations.extend(rule.check(graph, manifest, mapper, root))
    if git_root is not None:
        violations = _attach_commit_origins(violations, git_root)
    violations.sort(key=lambda v: (v.severity.value, v.rule, v.evidence))
    drift = compute_drift(graph, mapper, manifest, root)
    return AnalysisResult(graph, violations, drift=drift.score)


def analyze_repository_from_manifest(root: Path, manifest_path: Path) -> AnalysisResult:
    manifest = load_manifest(manifest_path)
    return analyze_repository(root, manifest)
