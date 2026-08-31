"""Tests for the rule engine rules."""

from __future__ import annotations

from pathlib import Path

from sentinel.analyzers.dependency_extractor import build_dependency_graph
from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest, Layer
from sentinel.domain.violations import ViolationKind
from sentinel.manifest.mapper import LayerMapper, LayerRule
from sentinel.rules.boundary_crossing import BoundaryCrossingRule
from sentinel.rules.circular import CircularDependencyRule
from sentinel.rules.god_module import GodModuleRule
from sentinel.rules.layer_violation import LayerViolationRule
from sentinel.rules.low_cohesion import LowCohesionRule

MANIFEST = ArchitectureManifest(
    {
        "presentation": Layer("presentation", frozenset({"application"})),
        "application": Layer("application", frozenset({"domain"})),
        "domain": Layer("domain", frozenset()),
    }
)

RULES = (
    LayerRule("presentation", ("ui/",)),
    LayerRule("application", ("app/",)),
    LayerRule("domain", ("domain/", "model/")),
)


def _write(root: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _setup(root: Path) -> tuple[DependencyGraph, LayerMapper]:
    files = tuple(p for p in root.rglob("*") if p.is_file() and p.suffix in {".ts", ".py"})
    graph = build_dependency_graph(files)
    mapper = LayerMapper(MANIFEST, RULES)
    return graph, mapper


def test_good_architecture_has_no_layer_violations(tmp_path: Path) -> None:
    _write(
        tmp_path / "src",
        {
            "ui/App.ts": "import { svc } from '../app/service';\n",
            "app/service.ts": "import { model } from '../domain/model';\n",
            "domain/model.ts": "export const model = {};\n",
        },
    )
    graph, mapper = _setup(tmp_path / "src")
    violations = LayerViolationRule().check(graph, MANIFEST, mapper, tmp_path / "src")
    assert violations == []


def test_cross_layer_dependency_detected(tmp_path: Path) -> None:
    _write(
        tmp_path / "src",
        {
            "ui/App.ts": "import { db } from '../model/db';\n",
            "model/db.ts": "export const db = {};\n",
        },
    )
    graph, mapper = _setup(tmp_path / "src")
    violations = LayerViolationRule().check(graph, MANIFEST, mapper, tmp_path / "src")
    kinds = {v.kind for v in violations}
    assert ViolationKind.LAYER_VIOLATION in kinds
    assert any("presentation" in v.components for v in violations)


def test_circular_dependency_detected(tmp_path: Path) -> None:
    _write(
        tmp_path / "src",
        {
            "a.ts": "import './b';\n",
            "b.ts": "import './a';\n",
        },
    )
    graph, mapper = _setup(tmp_path / "src")
    violations = CircularDependencyRule().check(graph, MANIFEST, mapper, tmp_path / "src")
    assert any(v.kind is ViolationKind.CIRCULAR_DEPENDENCY for v in violations)


def test_god_module_detected_when_over_threshold(tmp_path: Path) -> None:
    root = tmp_path / "src"
    content = {}
    content["hub.py"] = "\n".join(f"import mod{i}" for i in range(12))
    for i in range(12):
        content[f"mod{i}.py"] = ""
    _write(root, content)
    graph, mapper = _setup(root)
    violations = GodModuleRule(threshold=10).check(graph, MANIFEST, mapper, root)
    assert any(v.kind is ViolationKind.GOD_MODULE for v in violations)


def test_no_god_module_under_threshold(tmp_path: Path) -> None:
    root = tmp_path / "src"
    content = {"a.py": "import b\n", "b.py": ""}
    _write(root, content)
    graph, mapper = _setup(root)
    violations = GodModuleRule(threshold=10).check(graph, MANIFEST, mapper, root)
    assert violations == []


def test_self_import_skipped(tmp_path: Path) -> None:
    _write(tmp_path / "src", {"a.py": "import a\n"})
    graph, mapper = _setup(tmp_path / "src")
    violations = CircularDependencyRule().check(graph, MANIFEST, mapper, tmp_path / "src")
    assert violations == []


def test_dag_no_circular_dependencies(tmp_path: Path) -> None:
    _write(
        tmp_path / "src",
        {
            "a.ts": "import './b';\nimport './c';\n",
            "b.ts": "import './c';\n",
            "c.ts": "export const c = {};\n",
        },
    )
    graph, mapper = _setup(tmp_path / "src")
    violations = CircularDependencyRule().check(graph, MANIFEST, mapper, tmp_path / "src")
    assert violations == []


def test_boundary_crossing_detected(tmp_path: Path) -> None:
    _write(
        tmp_path / "src",
        {
            "ui/App.ts": "import { db } from '../domain/db';\n",
            "domain/db.ts": "export const db = {};\n",
        },
    )
    graph, mapper = _setup(tmp_path / "src")
    violations = BoundaryCrossingRule().check(graph, MANIFEST, mapper, tmp_path / "src")
    kinds = {v.kind for v in violations}
    assert ViolationKind.BOUNDARY_CROSSING in kinds


def test_boundary_crossing_within_layer_not_flagged(tmp_path: Path) -> None:
    _write(
        tmp_path / "src",
        {
            "ui/App.ts": "import { btn } from '../ui/button';\n",
            "ui/button.ts": "export const btn = {};\n",
        },
    )
    graph, mapper = _setup(tmp_path / "src")
    violations = BoundaryCrossingRule().check(graph, MANIFEST, mapper, tmp_path / "src")
    assert violations == []


def test_low_cohesion_detected(tmp_path: Path) -> None:
    root = tmp_path / "src"
    root.mkdir()
    lines_with_imports = []
    for i in range(6):
        lines_with_imports.append(f"import dep_{i}\ndef func_{i}(): pass\n")
    (root / "multi.py").write_text("".join(lines_with_imports), encoding="utf-8")
    for i in range(6):
        (root / f"dep_{i}.py").write_text("", encoding="utf-8")
    graph, mapper = _setup(root)
    violations = LowCohesionRule(threshold=0.5, min_symbols=3).check(
        graph, MANIFEST, mapper, root
    )
    assert any(v.kind is ViolationKind.LOW_COHESION for v in violations)


def test_low_cohesion_not_flagged_for_few_symbols(tmp_path: Path) -> None:
    root = tmp_path / "src"
    root.mkdir()
    (root / "small.py").write_text("def a(): pass\ndef b(): pass\n", encoding="utf-8")
    graph, mapper = _setup(root)
    violations = LowCohesionRule(threshold=0.5, min_symbols=5).check(
        graph, MANIFEST, mapper, root
    )
    assert violations == []
