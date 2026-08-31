"""TypeScript/JavaScript parser using tree-sitter."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node, Parser
from tree_sitter_language_pack import get_parser

from sentinel.domain.symbols import Language, SourceLocation, Symbol, SymbolKind
from sentinel.parsers.base import ParserBase, walk


class TypeScriptParser(ParserBase):
    """Extracts symbols and imports from TypeScript/JavaScript sources."""

    @property
    def language(self) -> Language:
        return Language.TYPESCRIPT

    def _build_parser(self) -> Parser:
        parser = get_parser("typescript")
        return parser  # type: ignore[return-value]

    def extract_symbols(self, tree: Node, file: Path) -> list[Symbol]:
        symbols: list[Symbol] = []
        for declaration in _class_declarations(tree):
            name_node = declaration.child_by_field_name("name")
            if name_node is None:
                continue
            symbols.append(
                    Symbol(
                        name_node.text.decode("utf-8"),
                        SymbolKind.CLASS,
                        SourceLocation(
                            file,
                            declaration.start_point[0] + 1,
                            declaration.start_point[1] + 1,
                        ),
                        self.language,
                    )
            )
        for func in _function_declarations(tree):
            name_node = func.child_by_field_name("name")
            if name_node is None:
                continue
            symbols.append(
                Symbol(
                    name_node.text.decode("utf-8"),
                    SymbolKind.FUNCTION,
                    SourceLocation(
                        file,
                        func.start_point[0] + 1,
                        func.start_point[1] + 1,
                    ),
                    self.language,
                )
            )
        return symbols

    def extract_imports(self, tree: Node, file: Path) -> list[tuple[str, int]]:
        imports: list[tuple[str, int]] = []
        for node in walk(tree):
            if node.type == "import_statement":
                parts = _string_children(node)
                if not parts:
                    continue
                imports.append((parts[0], node.start_point[0] + 1))
            elif node.type == "call_expression":
                callee = node.child_by_field_name("function")
                if callee is not None and callee.text.decode("utf-8") == "require":
                    parts = _string_children(node)
                    if parts:
                        imports.append((parts[0], node.start_point[0] + 1))
        return imports


def _class_declarations(node: Node) -> list[Node]:
    result: list[Node] = []
    for n in walk(node):
        if n.type == "class_declaration":
            result.append(n)
    return result


def _function_declarations(node: Node) -> list[Node]:
    result: list[Node] = []
    for n in walk(node):
        if n.type == "function_declaration":
            result.append(n)
    return result


def _string_children(node: Node) -> list[str]:
    values: list[str] = []
    for n in walk(node):
        if n.type == "string_fragment":
            values.append(n.text.decode("utf-8"))
    return values
