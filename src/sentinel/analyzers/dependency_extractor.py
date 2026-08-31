"""Analyzer that builds a DependencyGraph by resolving module references."""

from __future__ import annotations

from pathlib import Path

from sentinel.domain.graph import Dependency, DependencyGraph
from sentinel.parsers.registry import parser_for

EXTERNAL_LIBS = {
    "react",
    "react-dom",
    "vue",
    "os",
    "sys",
    "collections",
    "path",
    "re",
    "json",
    "datetime",
    "typing",
    "typing_extensions",
    "dataclasses",
    "enum",
    "itertools",
    "functools",
}

_SUFFIXES = (".ts", ".tsx", ".js", ".jsx", ".py", ".cs", ".java")


class DependencyExtractor:
    """Resolves raw module references to concrete files within the repo.

    Resolution order per reference:
    1. relative path (starting with .) resolved against the importing file's dir
    2. absolute alias (starting with / or @/) resolved against the project root
    3. bare module name matched against known file stems

    External libraries (stdlib / node packages) are ignored.
    """

    def __init__(self, files: tuple[Path, ...]) -> None:
        self._files = files
        self._root = _project_root(files)
        self._by_stem: dict[str, Path] = {}
        self._by_posix: dict[str, Path] = {}
        for file in files:
            self._by_stem.setdefault(file.stem, file)
            try:
                rel = file.relative_to(self._root)
            except ValueError:
                rel = file
            self._by_posix.setdefault(rel.with_suffix("").as_posix(), file)

    def resolve(self, reference: str, importer: Path) -> Path | None:
        clean = _clean_reference(reference)
        if not clean or clean in EXTERNAL_LIBS:
            return None
        if clean.startswith("."):
            return self._file_with_extension((importer.parent / clean).resolve())
        if clean.startswith("@/"):
            return self._file_with_extension(self._root / clean[2:])
        if clean.startswith("/"):
            return self._file_with_extension(self._root / clean.lstrip("/"))
        return self._by_stem.get(clean)

    def extract(self, file: Path) -> list[Dependency]:
        parser = parser_for(file)
        if parser is None:
            return []
        try:
            source = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return []
        tree = parser.parse(source, file)
        deps: list[Dependency] = []
        for reference, line in parser.extract_imports(tree, file):
            target = self.resolve(reference, file)
            if target is None or target == file:
                continue
            deps.append(
                Dependency(
                    source=file,
                    target=target,
                    evidence=reference,
                    line=line,
                )
            )
        return deps

    def _file_with_extension(self, candidate: Path) -> Path | None:
        if candidate.is_file():
            return candidate
        for suffix in _SUFFIXES:
            p = candidate.with_suffix(suffix)
            if p in self._files:
                return p
        return None


def build_dependency_graph(files: tuple[Path, ...]) -> DependencyGraph:
    """Build the full repo dependency graph from a set of source files."""
    extractor = DependencyExtractor(files)
    graph = DependencyGraph()
    for file in files:
        for dep in extractor.extract(file):
            graph.add_dependency(dep)
    return graph


def _project_root(files: tuple[Path, ...]) -> Path:
    if not files:
        return Path(".")
    if len(files) == 1:
        return Path(files[0]).parent
    root = Path(files[0])
    all_absolute = [f.resolve() for f in files]
    root = Path(all_absolute[0])
    for f in all_absolute[1:]:
        new = _common_path(root, f)
        if new is None:
            break
        root = new
    return root


def _common_path(a: Path, b: Path) -> Path | None:
    try:
        return Path(__import__("os").path.commonpath([str(a), str(b)]))
    except ValueError:
        return None


def _clean_reference(reference: str) -> str:
    return reference.strip().strip("'\"")
