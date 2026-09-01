"""Java parser using tree-sitter."""

from __future__ import annotations

from pathlib import Path

from tree_sitter import Node, Parser
from tree_sitter_language_pack import get_parser

from sentinel.domain.symbols import Language, SourceLocation, Symbol, SymbolKind
from sentinel.parsers.base import ParserBase, walk


class JavaParser(ParserBase):
    """Extracts symbols and imports from Java sources."""

    @property
    def language(self) -> Language:
        return Language.JAVA

    def _build_parser(self) -> Parser:
        parser = get_parser("java")
        return parser  # type: ignore[return-value]

    def extract_symbols(self, tree: Node, file: Path) -> list[Symbol]:
        symbols: list[Symbol] = []
        for node in walk(tree):
            if node.type == "class_declaration":
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
            elif node.type == "method_declaration":
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
        for node in walk(tree):
            if node.type == "import_declaration":
                text = node.text.decode("utf-8").strip()
                # `import com.example.model.User;` -> `com.example.model.User`
                parts = text.split()
                if len(parts) >= 2:
                    fqn = parts[1].strip().rstrip(";")
                    if fqn and not fqn.endswith("*"):
                        imports.append((fqn, node.start_point[0] + 1))
        return imports
