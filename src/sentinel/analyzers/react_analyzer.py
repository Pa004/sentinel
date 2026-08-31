"""React component analysis: detects components and measures their properties."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReactComponent:
    """A detected React component with its properties."""

    file: Path
    name: str
    line_count: int
    prop_count: int
    has_hooks: bool
    export_default: bool


_JSX_PATTERNS = re.compile(
    r"<[A-Z][a-zA-Z0-9]*[\s/>]|"  # <Component or <Component />
    r"React\.createElement|"  # React.createElement
    r"from\s+['\"]react['\"]"  # import from 'react'
)

_HOOK_PATTERNS = re.compile(r"\b(useState|useEffect|useContext|useReducer|useMemo|useCallback)\b")

_FUNCTION_COMPONENT_RE = re.compile(
    r"(?:export\s+(?:default\s+)?)?"  # optional export default
    r"(?:const|let|var|function)\s+"
    r"([A-Z][a-zA-Z0-9]*)"  # component name (PascalCase)
)

_PROPS_PARAM_RE = re.compile(
    r"(?:const|let|var|function)\s+[A-Z][a-zA-Z0-9]*\s*\(\s*\{([^}]*)\}"  # destructured props
    r"|"
    r"(?:const|let|var|function)\s+[A-Z][a-zA-Z0-9]*\s*\(\s*props"  # props parameter
)


def detect_react_component(file: Path) -> ReactComponent | None:
    """Detect if a file contains a React component and return its properties."""
    if file.suffix not in {".tsx", ".jsx", ".ts", ".js"}:
        return None

    try:
        source = file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    if not _JSX_PATTERNS.search(source):
        return None

    lines = source.splitlines()
    line_count = len(lines)

    name_match = _FUNCTION_COMPONENT_RE.search(source)
    if name_match is None:
        return None
    name = name_match.group(1)

    prop_count = _count_props(source)
    has_hooks = bool(_HOOK_PATTERNS.search(source))
    export_default = "export default" in source

    return ReactComponent(
        file=file,
        name=name,
        line_count=line_count,
        prop_count=prop_count,
        has_hooks=has_hooks,
        export_default=export_default,
    )


def _count_props(source: str) -> int:
    """Count the number of props a component receives."""
    match = _PROPS_PARAM_RE.search(source)
    if match is None:
        return 0
    props_str = match.group(1) if match.group(1) else ""
    if not props_str.strip():
        return 0
    return len([p.strip().split(":")[0].strip() for p in props_str.split(",") if p.strip()])
