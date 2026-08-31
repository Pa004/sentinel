"""Tests for drift score analysis."""

from __future__ import annotations

from pathlib import Path

from sentinel.analyzers.dependency_extractor import build_dependency_graph
from sentinel.analyzers.drift import DriftScore, drift_score
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.manifest.loader import load_manifest
from sentinel.manifest.mapper import LayerMapper, LayerRule
from sentinel.parsers.registry import source_files

FIXTURES = Path(__file__).parent / "fixtures"


def _make_mapper(manifest: ArchitectureManifest, root: Path) -> LayerMapper:
    rules = tuple(
        LayerRule(name, (f"{name}/",)) for name in manifest.layer_names()
    )
    return LayerMapper(manifest, rules)


def test_good_fixture_zero_drift() -> None:
    manifest = load_manifest(FIXTURES / "manifest.yaml")
    good = FIXTURES / "GOOD"
    files = source_files(good)
    graph = build_dependency_graph(files)
    mapper = _make_mapper(manifest, good)
    result = drift_score(graph, mapper, manifest, good)
    assert result.score == 0.0
    assert result.illegal_count == 0
    assert result.total_count > 0


def test_bad_fixture_full_drift() -> None:
    manifest = load_manifest(FIXTURES / "manifest.yaml")
    bad = FIXTURES / "BAD"
    files = source_files(bad)
    graph = build_dependency_graph(files)
    mapper = _make_mapper(manifest, bad)
    result = drift_score(graph, mapper, manifest, bad)
    assert result.score == 1.0
    assert result.illegal_count > 0
    assert result.illegal_count == result.total_count


def test_empty_graph_zero_drift() -> None:
    manifest = load_manifest(FIXTURES / "manifest.yaml")
    root = FIXTURES / "GOOD"
    mapper = _make_mapper(manifest, root)
    graph = build_dependency_graph(())
    result = drift_score(graph, mapper, manifest, root)
    assert result == DriftScore(score=0.0, illegal_count=0, total_count=0)


def test_evolving_fixture_partial_drift() -> None:
    manifest = load_manifest(FIXTURES / "manifest.yaml")
    evolving = FIXTURES / "EVOLVING"
    files = source_files(evolving)
    graph = build_dependency_graph(files)
    mapper = _make_mapper(manifest, evolving)
    result = drift_score(graph, mapper, manifest, evolving)
    assert result.score == 0.0
    assert result.total_count == 2


def test_drift_score_in_analysis_result() -> None:
    manifest = load_manifest(FIXTURES / "manifest.yaml")
    good = FIXTURES / "GOOD"
    from sentinel.violation_engine import analyze_repository

    result = analyze_repository(good, manifest)
    assert isinstance(result.drift, float)
    assert 0.0 <= result.drift <= 1.0


def test_drift_json_serialization() -> None:
    import json

    from sentinel.domain.graph import DependencyGraph
    from sentinel.reports.json import serialize
    from sentinel.violation_engine import AnalysisResult

    graph = DependencyGraph()
    result = AnalysisResult(graph=graph, violations=[], drift=0.42)
    data = json.loads(serialize(result))
    assert "drift" in data
    assert abs(data["drift"] - 0.42) < 1e-9
