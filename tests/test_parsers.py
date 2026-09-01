"""Unit tests for tree-sitter parsers (TypeScript, Python, Java, C#)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from sentinel.domain.symbols import Language, SymbolKind
from sentinel.parsers.csharp import CSharpParser
from sentinel.parsers.java import JavaParser
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


JAVA_SAMPLE = """
package com.example.app;

import java.util.List;
import com.example.model.User;
import com.example.dao.UserDao;

public class App {
    public void run() {
        List<User> users;
        UserDao dao;
    }
}
"""

CSHARP_SAMPLE = """
using System;
using MyApp.Domain;
using MyApp.Data;

namespace MyApp {
    public class Program {
        public void Main() {
            var entity = new Entity();
            var repo = new Repository();
        }
    }
}
"""


def test_java_extracts_imports() -> None:
    parser = JavaParser()
    tree = parser.parse(JAVA_SAMPLE, Path("App.java"))
    imports = parser.extract_imports(tree, Path("App.java"))
    refs = [p for p, _ in imports]
    # full FQN is returned for multi-level imports
    assert "com.example.model.User" in refs
    assert "com.example.dao.UserDao" in refs
    assert "java.util.List" in refs


def test_java_skips_star_imports() -> None:
    parser = JavaParser()
    tree = parser.parse("import com.example.model.*;\n", Path("X.java"))
    imports = parser.extract_imports(tree, Path("X.java"))
    assert imports == []


def test_python_skips_star_imports() -> None:
    parser = PythonParser()
    tree = parser.parse("from os import *\n", Path("main.py"))
    imports = parser.extract_imports(tree, Path("main.py"))
    assert imports == []


def test_java_extracts_symbols() -> None:
    parser = JavaParser()
    tree = parser.parse(JAVA_SAMPLE, Path("App.java"))
    symbols = parser.extract_symbols(tree, Path("App.java"))
    kinds = {s.name: s.kind for s in symbols}
    assert kinds["App"] is SymbolKind.CLASS
    assert kinds["run"] is SymbolKind.FUNCTION


def test_csharp_extracts_imports() -> None:
    parser = CSharpParser()
    tree = parser.parse(CSHARP_SAMPLE, Path("Program.cs"))
    imports = parser.extract_imports(tree, Path("Program.cs"))
    refs = [p for p, _ in imports]
    # full FQN is returned for multi-level imports
    assert "MyApp.Domain" in refs
    assert "MyApp.Data" in refs


def test_csharp_extracts_symbols() -> None:
    parser = CSharpParser()
    tree = parser.parse(CSHARP_SAMPLE, Path("Program.cs"))
    symbols = parser.extract_symbols(tree, Path("Program.cs"))
    kinds = {s.name: s.kind for s in symbols}
    assert kinds["Program"] is SymbolKind.CLASS
    assert kinds["Main"] is SymbolKind.FUNCTION
    # full FQNs are returned for multi-level imports
    parser_imports = parser.extract_imports(tree, Path("Program.cs"))
    assert {p for p, _ in parser_imports} >= {"MyApp.Domain", "MyApp.Data"}


def test_registry_java_csharp() -> None:
    assert language_for(Path("a.java")) is Language.JAVA
    assert language_for(Path("b.cs")) is Language.CSHARP
    assert parser_for(Path("a.java")) is not None
    assert parser_for(Path("b.cs")) is not None


def test_registry_source_files_ignores_ignored_dirs(tmp_path: Path) -> None:
    (tmp_path / "app.ts").write_text("")
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "dep.ts").write_text("")
    files = source_files(tmp_path)
    assert any(f == tmp_path / "app.ts" for f in files)
    assert not any("dep.ts" in str(f) for f in files)


@pytest.mark.skipif(
    sys.platform == "win32" and not os.environ.get("SENTINEL_TEST_SYMLINKS"),
    reason="Creating symlinks on Windows requires elevated privileges",
)
def test_registry_source_files_skips_symlinks(tmp_path: Path) -> None:
    inside = tmp_path / "src"
    inside.mkdir()
    (inside / "app.ts").write_text("export const x = 1;\n", encoding="utf-8")
    outside = tmp_path / "outside_repo"
    outside.mkdir()
    (outside / "secret.ts").write_text("export const y = 2;\n", encoding="utf-8")
    symlink = inside / "link.ts"
    symlink.symlink_to(outside / "secret.ts")
    files = source_files(tmp_path)
    assert any(f.name == "app.ts" for f in files)
    assert not any(f.name == "link.ts" for f in files)
