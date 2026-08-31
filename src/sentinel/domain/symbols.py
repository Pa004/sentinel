"""Pure domain types for the symbol/language layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class Language(StrEnum):
    """Supported source languages."""

    TYPESCRIPT = "typescript"
    PYTHON = "python"
    CSHARP = "csharp"
    JAVA = "java"


class SymbolKind(StrEnum):
    """Kinds of symbols that can be indexed from source."""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    VARIABLE = "variable"


@dataclass(frozen=True)
class SourceLocation:
    """A location inside a source file, 1-based line/column."""

    file: Path
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


@dataclass(frozen=True)
class Symbol:
    """A named entity declared in source, tied to its defining file."""

    name: str
    kind: SymbolKind
    location: SourceLocation
    language: Language

    @property
    def qualified_name(self) -> str:
        """Fully qualified name relative to its file stem."""
        return f"{self.location.file.stem}.{self.name}"


@dataclass(frozen=True)
class SymbolGraph:
    """Index of all symbols across a repository, keyed by file path."""

    symbols: dict[Path, tuple[Symbol, ...]] = field(default_factory=dict)

    def symbols_in(self, file: Path) -> tuple[Symbol, ...]:
        return self.symbols.get(file, ())

    def all_files(self) -> tuple[Path, ...]:
        return tuple(sorted(self.symbols.keys()))

    def add(self, symbol: Symbol) -> None:
        existing = self.symbols.get(symbol.location.file, ())
        key = symbol.location.file
        if symbol not in existing:
            self.symbols[key] = (*existing, symbol)
