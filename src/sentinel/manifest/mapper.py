"""Map module files to architecture layers using path patterns."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sentinel.domain.manifest import ArchitectureManifest
from sentinel.parsers.registry import IGNORED_DIRS


@dataclass(frozen=True)
class LayerRule:
    """A path-prefix rule assigning files to a layer."""

    layer: str
    patterns: tuple[str, ...]


class LayerMapper:
    """Assigns a file to a layer based on its relative path.

    Rules are checked in order of specificity (longest prefix first).
    A file that matches no rule is assigned to the default layer.
    """

    def __init__(self, manifest: ArchitectureManifest, rules: tuple[LayerRule, ...]) -> None:
        self._manifest = manifest
        self._rules = sorted(rules, key=lambda r: max(len(p) for p in r.patterns), reverse=True)

    def layer_for(self, file: Path, root: Path) -> str:
        try:
            rel = file.relative_to(root)
        except ValueError:
            rel = file
        posix = rel.as_posix()
        for rule in self._rules:
            if any(posix.startswith(p) for p in rule.patterns):
                return rule.layer
        # fallback: first directory segment
        parts = rel.parts
        if parts and parts[0] not in IGNORED_DIRS:
            return parts[0]
        return "default"

    def layer_of_module(self, file: Path, root: Path) -> str:
        return self.layer_for(file, root)
