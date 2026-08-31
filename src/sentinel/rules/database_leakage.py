"""Database leakage rule: flags direct dependencies to data-layer modules."""

from __future__ import annotations

import contextlib
import re
from pathlib import Path

from sentinel.domain.graph import DependencyGraph
from sentinel.domain.manifest import ArchitectureManifest
from sentinel.domain.violations import Severity, Violation, ViolationKind
from sentinel.manifest.mapper import LayerMapper
from sentinel.rules.base import Rule

# Heuristic patterns that identify a module as belonging to the data/persistence layer.
_DATA_LAYER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(^|/)repository(/|$|\.)", re.IGNORECASE),
    re.compile(r"(^|/)repositories(/|$|\.)", re.IGNORECASE),
    re.compile(r"(^|/)persistence(/|$|\.)", re.IGNORECASE),
    re.compile(r"(^|/)dal(/|$|\.)", re.IGNORECASE),
    re.compile(r"(^|/)db(/|$|\.|_)", re.IGNORECASE),
    re.compile(r"(^|/)data(/|$|\.|store)", re.IGNORECASE),
    re.compile(r"(^|/)store(/|$|\.|_)", re.IGNORECASE),
    re.compile(r"(^|/)dao(/|$|\.|_)", re.IGNORECASE),
)


def _relative(path: Path, root: Path) -> str:
    """Return *path* as a POSIX string relative to *root*."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _is_data_layer_module(module_path: str, root: Path | None = None) -> bool:
    """Return True if *module_path* looks like a data/persistence module.

    Checks parent directory names (not filenames) against heuristic patterns,
    so ``domain/db.ts`` does NOT match while ``repository/user_repo.ts`` does.
    """
    p = Path(module_path)
    if root is not None:
        with contextlib.suppress(ValueError):
            p = p.relative_to(root)
    # Walk parent directories: repository/, persistence/, db/, etc.
    for part in p.parts[:-1]:  # skip the filename itself
        normalized = part.replace("\\", "/")
        if any(pat.search(f"/{normalized}/") for pat in _DATA_LAYER_PATTERNS):
            return True
    return False


class DatabaseLeakageRule(Rule):
    """Detect when a non-data module depends directly on a data/persistence module.

    This fires independently of the manifest layer declaration: even if the
    manifest does not declare a 'data' layer, the heuristic catches direct
    imports to repository / DAO / persistence modules.
    """

    def check(
        self,
        graph: DependencyGraph,
        manifest: ArchitectureManifest,
        mapper: LayerMapper,
        root: Path,
    ) -> list[Violation]:
        violations: list[Violation] = []
        for source in graph.nodes():
            src_str = str(source)
            # Skip data-layer sources — we only care about non-data -> data leakage
            if _is_data_layer_module(src_str, root):
                continue
            for dep in graph.dependencies_of(source):
                tgt_str = str(dep.target)
                if _is_data_layer_module(tgt_str, root):
                    src_rel = _relative(source, root)
                    tgt_rel = _relative(dep.target, root)
                    violations.append(
                        Violation(
                            rule="database-leakage",
                            kind=ViolationKind.DATABASE_LEAKAGE,
                            evidence=f"{dep.source}:{dep.line} -> {dep.target} ({dep.evidence})",
                            components=(src_rel, tgt_rel),
                            impact=(
                                f"{src_rel} imports directly from data/persistence "
                                f"module {tgt_rel}; bypasses the repository pattern"
                            ),
                            recommendation=(
                                f"Route access to {tgt_rel} through an intermediary "
                                f"(service or repository interface)"
                            ),
                            severity=Severity.ERROR,
                        )
                    )
        return violations
