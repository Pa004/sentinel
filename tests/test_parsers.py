"""Unit tests for tree-sitter parsers (TypeScript + Python)."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.symbols import Language, SymbolKind
from sentinel.parsers.python_lang import PythonParser
from sentinel.parsers.registry import language_for, parser_for, source_files
from sentinel.parsers.typescript import TypeScriptParser

TS_SAMPLE = """
import { foo } from './app';
import db from './db';
export function helper() {}
export class Service {}
const legacy = require('./util');
"""

PY_SAMPLE = """
import os
from collections import defaultdict
import db
class Service:
    def helper(self):
        pass
def top():
    pass
"""


def test_typescript_extracts_imports() -> None:
    parser = TypeScriptParser()
    tree = parser.parse(TS_SAMPLE, Path("x.ts"))
    imports = parser.extract_imports(tree, Path("x.ts"))
    paths = [p for p, _ in imports]
    assert "./app" in paths
    assert "./db" in paths
    assert "./util" in paths


def test_typescript_extracts_symbols() -> None:
    parser = TypeScriptParser()
    tree = parser.parse(TS_SAMPLE, Path("x.ts"))
    symbols = parser.extract_symbols(tree, Path("x.ts"))
    kinds = {s.name: s.kind for s in symbols}
    assert kinds["Service"] is SymbolKind.CLASS
    assert kinds["helper"] is SymbolKind.FUNCTION


def test_typescript_line_numbers_are_one_based() -> None:
    parser = TypeScriptParser()
    tree = parser.parse(TS_SAMPLE, Path("x.ts"))
    imports = parser.extract_imports(tree, Path("x.ts"))
    assert imports[0][1] == 2


def test_python_extracts_imports() -> None:
    parser = PythonParser()
    tree = parser.parse(PY_SAMPLE, Path("x.py"))
    imports = parser.extract_imports(tree, Path("x.py"))
    paths = [p for p, _ in imports]
    assert "os" in paths
    assert "collections" in paths
    assert "db" in paths


def test_python_extracts_symbols() -> None:
    parser = PythonParser()
    tree = parser.parse(PY_SAMPLE, Path("x.py"))
    symbols = parser.extract_symbols(tree, Path("x.py"))
    kinds = {s.name: s.kind for s in symbols}
    assert kinds["Service"] is SymbolKind.CLASS
    assert kinds["top"] is SymbolKind.FUNCTION


def test_registry_language_and_parser() -> None:
    assert language_for(Path("a.ts")) is Language.TYPESCRIPT
    assert language_for(Path("b.py")) is Language.PYTHON
    assert language_for(Path("c.unknown")) is None
    assert parser_for(Path("a.tsx")) is not None
    assert parser_for(Path("c.unknown")) is None


def test_registry_source_files_ignores_ignored_dirs(tmp_path: Path) -> None:
    (tmp_path / "app.ts").write_text("")
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "dep.ts").write_text("")
    files = source_files(tmp_path)
    assert any(f == tmp_path / "app.ts" for f in files)
    assert not any("dep.ts" in str(f) for f in files)
