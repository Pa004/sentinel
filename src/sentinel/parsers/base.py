"""Parser interface and shared helpers for tree-sitter based extraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from tree_sitter import Node, Parser

from sentinel.domain.symbols import Language, Symbol


def walk(node: Node) -> Node:
    """Yield `node` and all its descendants depth-first."""
    yield node
    for i in range(node.child_count):
        child = node.child(i)
        if child is not None:
            yield from walk(child)


class ParserBase(ABC):
    """Base class for language parsers built on tree-sitter.

    Implementations provide:
    - `language`: the target Language enum
    - `extract_symbols`: walk the tree and index declared symbols
    - `extract_imports`: resolve module references (import/require statements)
    """

    def __init__(self) -> None:
        self._parser: Parser = self._build_parser()

    @property
    @abstractmethod
    def language(self) -> Language:
        ...

    @abstractmethod
    def _build_parser(self) -> Parser:
        ...

    @abstractmethod
    def extract_symbols(self, tree: Node, file: Path) -> list[Symbol]:
        """Return symbols declared in `file` with their source locations."""

    @abstractmethod
    def extract_imports(self, tree: Node, file: Path) -> list[tuple[str, int]]:
        """Return raw module references as (module_or_path, line) pairs.

        The concrete module resolution (path -> file) happens in the analyzer
        layer so this stays a pure syntax concern.
        """

    def parse(self, source: str, file: Path) -> Node:
        """Parse source text into a tree-sitter syntax tree."""
        tree = self._parser.parse(source.encode("utf-8"))
        return tree.root_node
