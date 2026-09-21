"""Load and validate an architecture manifest from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from sentinel.domain.manifest import (
    FLAT_TUNING_KEYS,
    RULE_TUNING_FIELDS,
    VALID_RULE_KEYS,
    ArchitectureManifest,
    Layer,
    normalize_rule_key,
)


class ManifestError(ValueError):
    """Raised when the manifest YAML is malformed or invalid."""


def load_manifest(path: Path) -> ArchitectureManifest:
    """Parse a manifest YAML into an ArchitectureManifest, validating structure."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestError(f"cannot read manifest: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ManifestError(f"invalid YAML: {exc}") from exc

    if not isinstance(raw, dict) or "layers" not in raw:
        raise ManifestError("manifest must contain a 'layers' mapping")

    layers_raw = raw["layers"]
    if not isinstance(layers_raw, dict) or not layers_raw:
        raise ManifestError("'layers' must be a non-empty mapping")

    layers: dict[str, Layer] = {}
    for name, spec in layers_raw.items():
        if not isinstance(name, str) or not name.strip():
            raise ManifestError("layer names must be non-empty strings")
        if not isinstance(spec, dict):
            raise ManifestError(f"layer '{name}' must be a mapping")
        allowed = spec.get("may_depend_on", [])
        if not isinstance(allowed, list) or not all(isinstance(x, str) for x in allowed):
            raise ManifestError(f"layer '{name}' may_depend_on must be a list of strings")
        layers[name] = Layer(name, frozenset(allowed))

    rules = _parse_rules(raw.get("rules"))

    return ArchitectureManifest(layers, rules)


def _parse_rules(raw: object) -> dict[str, dict[str, int | float]]:
    """Validate the optional `rules` block and return per-rule tuning.

    Keys accept hyphen or underscore style plus legacy aliases; they are
    stored under the canonical hyphenated block name.
    """
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ManifestError("'rules' must be a mapping")
    result: dict[str, dict[str, int | float]] = {}
    for key, spec in raw.items():
        if key not in VALID_RULE_KEYS:
            raise ManifestError(f"unknown rule '{key}'; valid: {sorted(VALID_RULE_KEYS)}")
        if not isinstance(spec, dict):
            raise ManifestError(f"rule '{key}' must be a mapping")
        # Flat legacy keys, e.g. `react_max_lines: {threshold: 150}`.
        if key in FLAT_TUNING_KEYS:
            block, field = FLAT_TUNING_KEYS[key]
            tuning = _validate_tuning(key, block, spec, {field})
            merged = result.setdefault(block, {})
            # Legacy flat form only carries `threshold` meaning `field`.
            if "threshold" in tuning:
                merged[field] = tuning["threshold"]
            continue
        canonical = normalize_rule_key(key)
        # Legacy react split-keys used `threshold` to mean max_lines/max_props.
        if key in {
            "react_oversized_component",
            "react_oversized-component",
            "react-oversized-component",
        } and set(spec) == {"threshold"}:
            tuning = _validate_tuning(key, canonical, spec, {"threshold"})
            result.setdefault(canonical, {}).setdefault("max_lines", tuning["threshold"])
            continue
        if key in {"react_too_many_props", "react_too_many-props", "react-too-many-props"} and set(
            spec
        ) == {"threshold"}:
            tuning = _validate_tuning(key, canonical, spec, {"threshold"})
            result.setdefault(canonical, {}).setdefault("max_props", tuning["threshold"])
            continue
        allowed = RULE_TUNING_FIELDS.get(canonical, frozenset({"threshold"}))
        tuning = _validate_tuning(key, canonical, spec, allowed)
        merged = result.setdefault(canonical, {})
        merged.update(tuning)
    return result


def _validate_tuning(
    key: str, canonical: str, spec: dict, allowed: set | frozenset
) -> dict[str, int | float]:
    tuning: dict[str, int | float] = {}
    for name, value in spec.items():
        if name not in allowed:
            raise ManifestError(f"rule '{key}' only supports {sorted(allowed)}, got '{name}'")
        if not isinstance(value, (int, float)) or value < 0:
            raise ManifestError(f"rule '{key}' field '{name}' must be a non-negative number")
        tuning[name] = value
    return tuning
