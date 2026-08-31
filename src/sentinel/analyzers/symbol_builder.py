"""Analyzer that builds a SymbolGraph from parsed source files."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.symbols import SymbolGraph
from sentinel.parsers.registry import parser_for


def build_symbol_graph(files: tuple[Path, ...]) -> SymbolGraph:
    """Parse each file and index its declared symbols into a SymbolGraph."""
    graph = SymbolGraph()
    for file in files:
        parser = parser_for(file)
        if parser is None:
            continue
        try:
            source = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        tree = parser.parse(source, file)
        for symbol in parser.extract_symbols(tree, file):
            graph.add(symbol)
    return graph
