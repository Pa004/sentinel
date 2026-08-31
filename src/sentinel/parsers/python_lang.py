"""Python parser using tree-sitter."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node, Parser
from tree_sitter_language_pack import get_parser

from sentinel.domain.symbols import Language, SourceLocation, Symbol, SymbolKind
from sentinel.parsers.base import ParserBase


class PythonParser(ParserBase):
    """Extracts symbols and imports from Python sources."""

    @property
    def language(self) -> Language:
        return Language.PYTHON

    def _build_parser(self) -> Parser:
        parser = get_parser("python")
        return parser  # type: ignore[return-value]

    def extract_symbols(self, tree: Node, file: Path) -> list[Symbol]:
        symbols: list[Symbol] = []
        for node in _walk(tree):
            if node.type == "class_definition":
                name_node = node.child_by_field_name("name")
                if name_node is None:
                    continue
                symbols.append(
                    Symbol(
                        name_node.text.decode("utf-8"),
                        SymbolKind.CLASS,
                        SourceLocation(file, node.start_point[0] + 1, node.start_point[1] + 1),
                        self.language,
                    )
                )
            elif node.type == "function_definition":
                name_node = node.child_by_field_name("name")
                if name_node is None:
                    continue
                symbols.append(
                    Symbol(
                        name_node.text.decode("utf-8"),
                        SymbolKind.FUNCTION,
                        SourceLocation(file, node.start_point[0] + 1, node.start_point[1] + 1),
                        self.language,
                    )
                )
        return symbols

    def extract_imports(self, tree: Node, file: Path) -> list[tuple[str, int]]:
        imports: list[tuple[str, int]] = []
        for node in _walk(tree):
            if node.type == "import_statement":
                module = _dotted_name_text(node)
                if module:
                    imports.append((module, node.start_point[0] + 1))
            elif node.type == "import_from_statement":
                module = _from_module_text(node)
                if module:
                    imports.append((module, node.start_point[0] + 1))
        return imports


def _dotted_name_text(node: Node) -> str:
    for n in _walk(node):
        if n.type == "dotted_name":
            return n.text.decode("utf-8")
    return ""


def _from_module_text(node: Node) -> str:
    for i in range(node.child_count):
        child = node.child(i)
        if child is not None and child.type == "dotted_name":
            return child.text.decode("utf-8")
        if child is not None and child.type == "relative_import":
            return child.text.decode("utf-8")
    return ""


def _walk(node: Node) -> Node:
    yield node
    for i in range(node.child_count):
        child = node.child(i)
        if child is not None:
            yield from _walk(child)
