"""Registry mapping file extensions and directories to parsers."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.symbols import Language
from sentinel.parsers.base import ParserBase
from sentinel.parsers.python_lang import PythonParser
from sentinel.parsers.typescript import TypeScriptParser

# Directories whose contents are never part of the analyzed architecture.
IGNORED_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "dist",
    "build",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
}

_EXTENSION_TO_PARSER: dict[str, ParserBase] = {
    ".ts": TypeScriptParser(),
    ".tsx": TypeScriptParser(),
    ".js": TypeScriptParser(),
    ".jsx": TypeScriptParser(),
    ".py": PythonParser(),
}

_EXTENSION_TO_LANGUAGE: dict[str, Language] = {
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".js": Language.TYPESCRIPT,
    ".jsx": Language.TYPESCRIPT,
    ".py": Language.PYTHON,
}


def parser_for(path: Path) -> ParserBase | None:
    return _EXTENSION_TO_PARSER.get(path.suffix.lower())


def language_for(path: Path) -> Language | None:
    return _EXTENSION_TO_LANGUAGE.get(path.suffix.lower())


def is_ignored_directory(name: str) -> bool:
    return name in IGNORED_DIRS


def source_files(root: Path) -> tuple[Path, ...]:
    """Return all supported source files under `root`, skipping ignored dirs."""
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file() or parser_for(path) is None:
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        files.append(path)
    return tuple(files)
