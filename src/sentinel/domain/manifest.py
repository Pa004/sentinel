"""Pure domain types for the architecture manifest (intended architecture)."""

from __future__ import annotations

from dataclasses import dataclass, field

VALID_RULE_KEYS = {"god_module", "high_coupling"}


@dataclass(frozen=True)
class Layer:
    """A named layer and the set of other layers it may depend on."""

    name: str
    may_depend_on: frozenset[str]

    def may_depend_on_layer(self, other: str) -> bool:
        return other in self.may_depend_on


@dataclass(frozen=True)
class ArchitectureManifest:
    """The declared target architecture: layers and their allowed edges.

    `rules` holds optional per-rule tuning, e.g. {"god_module": {"threshold": 12}}.
    """

    layers: dict[str, Layer]
    rules: dict[str, dict[str, int]] = field(default_factory=dict)

    def layer_names(self) -> tuple[str, ...]:
        return tuple(self.layers.keys())

    def layer(self, name: str) -> Layer | None:
        return self.layers.get(name)

    def allows(self, source_layer: str, target_layer: str) -> bool:
        """Whether a dependency source_layer -> target_layer is legal."""
        src = self.layers.get(source_layer)
        if src is None:
            return False
        tgt = self.layers.get(target_layer)
        if tgt is None:
            return True
        return src.may_depend_on_layer(target_layer)

    def rule_threshold(self, rule_key: str, default: int) -> int:
        return int(self.rules.get(rule_key, {}).get("threshold", default))
