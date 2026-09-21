"""Pure domain types for the architecture manifest (intended architecture)."""

from __future__ import annotations

from dataclasses import dataclass, field

CANONICAL_RULE_KEYS = {
    "circular-dependency",
    "god-module",
    "high-coupling",
    "layer-violation",
    "database-leakage",
    "low-cohesion",
    "boundary-crossing",
    "react-component",
}

# Alias -> canonical block. Underscore variants, legacy per-rule split keys,
# and flat tuning keys (used directly in violation_engine before the fix).
RULE_KEY_ALIASES = {
    "circular_dependency": "circular-dependency",
    "god_module": "god-module",
    "high_coupling": "high-coupling",
    "layer_violation": "layer-violation",
    "database_leakage": "database-leakage",
    "low_cohesion": "low-cohesion",
    "low-cohesion_min_symbols": "low-cohesion",
    "low_cohesion_min_symbols": "low-cohesion",
    "boundary_crossing": "boundary-crossing",
    "boundary-crossing": "boundary-crossing",
    "react_oversized_component": "react-component",
    "react_too_many_props": "react-component",
    "react-oversized-component": "react-component",
    "react-too-many-props": "react-component",
    "react_max_lines": "react-component",
    "react-max-lines": "react-component",
    "react_max_props": "react-component",
    "react-max-props": "react-component",
}

# Flat legacy top-level keys that encode (block, field) in the key name.
FLAT_TUNING_KEYS: dict[str, tuple[str, str]] = {
    "low_cohesion_min_symbols": ("low-cohesion", "min_symbols"),
    "low-cohesion_min_symbols": ("low-cohesion", "min_symbols"),
    "react_max_lines": ("react-component", "max_lines"),
    "react-max-lines": ("react-component", "max_lines"),
    "react_max_props": ("react-component", "max_props"),
    "react-max-props": ("react-component", "max_props"),
}

# Allowed tuning fields per canonical block.
RULE_TUNING_FIELDS: dict[str, frozenset[str]] = {
    "circular-dependency": frozenset({"threshold"}),
    "god-module": frozenset({"threshold"}),
    "high-coupling": frozenset({"threshold"}),
    "layer-violation": frozenset({"threshold"}),
    "database-leakage": frozenset({"threshold"}),
    "boundary-crossing": frozenset({"threshold"}),
    "low-cohesion": frozenset({"threshold", "min_symbols"}),
    "react-component": frozenset({"max_lines", "max_props"}),
}

# Backwards-compatible set accepted by the loader (canonical + aliases +
# flat legacy keys). Kept under the old name so existing imports keep working.
VALID_RULE_KEYS = (
    CANONICAL_RULE_KEYS
    | frozenset(RULE_KEY_ALIASES)
    | frozenset(FLAT_TUNING_KEYS)
    | {
        "circular-dependency",
        "god-module",
        "high-coupling",
        "layer-violation",
        "database-leakage",
        "low_cohesion",
        "boundary_crossing",
        "react_oversized_component",
        "react_too_many_props",
    }
)


def normalize_rule_key(key: str) -> str:
    """Return the canonical block name for a rule key or alias."""
    if key in CANONICAL_RULE_KEYS:
        return key
    if key in RULE_KEY_ALIASES:
        return RULE_KEY_ALIASES[key]
    underscored = key.replace("-", "_")
    if underscored in RULE_KEY_ALIASES:
        return RULE_KEY_ALIASES[underscored]
    hyphenated = key.replace("_", "-")
    if hyphenated in CANONICAL_RULE_KEYS:
        return hyphenated
    return key


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
    rules: dict[str, dict[str, int | float]] = field(default_factory=dict)

    def layer_names(self) -> tuple[str, ...]:
        return tuple(self.layers.keys())

    def layer(self, name: str) -> Layer | None:
        return self.layers.get(name)

    def has_layer(self, name: str) -> bool:
        return name in self.layers

    def allows(self, source_layer: str, target_layer: str) -> bool:
        """Whether a dependency source_layer -> target_layer is legal."""
        src = self.layers.get(source_layer)
        if src is None:
            return False
        tgt = self.layers.get(target_layer)
        if tgt is None:
            return True
        return src.may_depend_on_layer(target_layer)

    def rule_tuning(self, rule_key: str, field: str, default: int | float) -> int | float:
        """Return a tuning value, resolving aliases and legacy flat keys."""
        # Legacy flat top-level keys, e.g. {"react_max_lines": {"threshold": 150}}.
        if rule_key in FLAT_TUNING_KEYS:
            block, flat_field = FLAT_TUNING_KEYS[rule_key]
            if field == flat_field:
                direct = self.rules.get(rule_key, {}).get("threshold", None)
                if direct is not None:
                    return direct
            rule_key = block
        canonical = normalize_rule_key(rule_key)
        # Direct hit on the canonical block.
        value = self.rules.get(canonical, {}).get(field, None)
        if value is not None:
            return value
        # Backwards compat: manifest built by hand with alias keys.
        for alias, target in RULE_KEY_ALIASES.items():
            if target != canonical:
                continue
            value = self.rules.get(alias, {}).get(field, None)
            if value is not None:
                # Legacy `threshold` under a react split-key maps to its field.
                if canonical == "react-component" and field in {"max_lines", "max_props"}:
                    return value
                if field == "threshold" or alias == rule_key:
                    return value
        # Legacy react split-keys stored `threshold` meaning max_lines/max_props.
        if canonical == "react-component" and field in {"max_lines", "max_props"}:
            legacy_key = (
                "react_oversized_component" if field == "max_lines" else "react_too_many_props"
            )
            value = self.rules.get(legacy_key, {}).get("threshold", None)
            if value is not None:
                return value
        return default

    def rule_threshold(self, rule_key: str, default: int | float) -> int | float:
        # Legacy flat keys encode the field in the key name.
        if rule_key in FLAT_TUNING_KEYS:
            block, field = FLAT_TUNING_KEYS[rule_key]
            return self.rule_tuning(block, field, default)
        # Legacy `threshold` under react split-keys maps to max_lines/max_props.
        if rule_key in {"react_oversized_component", "react_oversized-component"}:
            return self.rule_tuning("react-component", "max_lines", default)
        if rule_key in {"react_too_many_props", "react_too-many-props"}:
            return self.rule_tuning("react-component", "max_props", default)
        if rule_key in {"react_max_lines", "react-max-lines"}:
            return self.rule_tuning("react-component", "max_lines", default)
        if rule_key in {"react_max_props", "react-max-props"}:
            return self.rule_tuning("react-component", "max_props", default)
        if rule_key in {"low_cohesion_min_symbols", "low-cohesion_min_symbols"}:
            return self.rule_tuning("low-cohesion", "min_symbols", default)
        return self.rule_tuning(rule_key, "threshold", default)
