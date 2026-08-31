"""Unit tests for the symbol and dependency graph analyzers."""

from __future__ import annotations

from pathlib import Path

from sentinel.analyzers.coupling import coupling_scores, fan_in, fan_out
from sentinel.analyzers.dependency_extractor import DependencyExtractor, build_dependency_graph
from sentinel.analyzers.symbol_builder import build_symbol_graph

GOOD_TS = {
    "app.ts": "import { handler } from './api';\n",
    "api.ts": "import { repo } from './service';\nexport function handler() {}\n",
    "service.ts": "import { db } from './db';\nexport function repo() {}\n",
    "db.ts": "export const db = {};\n",
}


def _write_files(base: Path, files: dict[str, str]) -> tuple[Path, ...]:
    paths: list[Path] = []
    for name, content in files.items():
        p = base / name
        p.write_text(content, encoding="utf-8")
        paths.append(p)
    return tuple(paths)


def test_symbol_graph_indexes_classes_and_functions(tmp_path: Path) -> None:
    files = (tmp_path / "api.ts",)
    files[0].write_text("export class Service {}\nexport function handler() {}\n", encoding="utf-8")
    graph = build_symbol_graph(files)
    names = {s.name for s in graph.symbols_in(files[0])}
    assert names == {"Service", "handler"}


def test_dependency_graph_resolves_relative_imports(tmp_path: Path) -> None:
    files = _write_files(tmp_path, GOOD_TS)
    graph = build_dependency_graph(files)
    app = tmp_path / "app.ts"
    deps = graph.dependencies_of(app)
    assert any(d.target == tmp_path / "api.ts" for d in deps)


def test_dependency_graph_ignores_external_libs(tmp_path: Path) -> None:
    x = tmp_path / "x.ts"
    x.write_text(
        "import os from 'os';\nimport react from 'react';\n",
        encoding="utf-8",
    )
    files = (x,)
    graph = build_dependency_graph(files)
    assert graph.dependencies_of(x) == ()


def test_resolve_bare_module_by_stem(tmp_path: Path) -> None:
    db = tmp_path / "db.py"
    db.write_text("", encoding="utf-8")
    extractor = DependencyExtractor((db,))
    assert extractor.resolve("db", tmp_path / "x.py") == db


def test_coupling_scores_count_fan_in_and_fan_out(tmp_path: Path) -> None:
    files = _write_files(tmp_path, GOOD_TS)
    graph = build_dependency_graph(files)
    scores = coupling_scores(graph)
    assert scores[tmp_path / "db.ts"] == 1
    assert fan_out(graph, tmp_path / "app.ts") == 1
    assert fan_in(graph, tmp_path / "db.ts") == 1
