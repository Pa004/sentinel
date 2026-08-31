"""Unit tests for the domain types."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.graph import Dependency, DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest, Layer
from sentinel.domain.symbols import Language, SourceLocation, Symbol, SymbolGraph, SymbolKind
from sentinel.domain.trend import TrendPoint
from sentinel.domain.violations import Severity, Violation, ViolationKind


def test_symbol_qualified_name_uses_file_stem() -> None:
    loc = SourceLocation(Path("src/ui/App.ts"), 1, 0)
    sym = Symbol("App", SymbolKind.CLASS, loc, Language.TYPESCRIPT)
    assert sym.qualified_name == "App.App"


def test_symbol_graph_adds_dedup() -> None:
    loc = SourceLocation(Path("a.ts"), 1, 0)
    graph = SymbolGraph()
    first = Symbol("A", SymbolKind.FUNCTION, loc, Language.TYPESCRIPT)
    graph.add(first)
    graph.add(first)
    assert len(graph.symbols_in(Path("a.ts"))) == 1


def test_dependency_graph_tracks_outgoing() -> None:
    graph = DependencyGraph()
    dep = Dependency(Path("ui.ts"), Path("db.ts"), "import db from './db'", 2)
    graph.add_dependency(dep)
    graph.add_dependency(dep)
    assert graph.mentions(Path("ui.ts"))
    assert graph.dependencies_of(Path("ui.ts")) == (dep,)
    assert len(graph.dependencies_of(Path("ui.ts"))) == 1


def test_manifest_allows_legal_dependency() -> None:
    manifest = ArchitectureManifest(
        {
            "presentation": Layer("presentation", frozenset({"application"})),
            "application": Layer("application", frozenset({"domain"})),
            "domain": Layer("domain", frozenset()),
        }
    )
    assert manifest.allows("presentation", "application")
    assert not manifest.allows("presentation", "domain")
    assert manifest.allows("application", "domain")


def test_manifest_allows_unknown_target_layer() -> None:
    manifest = ArchitectureManifest({"a": Layer("a", frozenset())})
    assert manifest.allows("a", "unknown")


def test_violation_carries_full_spec_fields() -> None:
    v = Violation(
        rule="layer-violation",
        kind=ViolationKind.LAYER_VIOLATION,
        evidence="ui.ts:5: import db",
        components=("presentation", "domain"),
        impact="UI bypasses application layer",
        recommendation="Route UI -> database through application",
        severity=Severity.ERROR,
        commit="abc123",
    )
    assert v.commit == "abc123"
    assert v.severity is Severity.ERROR


def test_trend_point_total() -> None:
    tp = TrendPoint("sha", {ViolationKind.GOD_MODULE: 2, ViolationKind.CIRCULAR_DEPENDENCY: 3})
    assert tp.total() == 5
