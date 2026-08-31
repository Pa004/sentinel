"""Tests for manifest loader and layer mapper."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinel.domain.manifest import ArchitectureManifest, Layer
from sentinel.manifest.loader import ManifestError, load_manifest
from sentinel.manifest.mapper import LayerMapper, LayerRule

VALID_YAML = """
layers:
  presentation:
    may_depend_on:
      - application
  application:
    may_depend_on:
      - domain
  domain:
    may_depend_on: []
"""


def test_load_valid_manifest(tmp_path: Path) -> None:
    p = tmp_path / "manifest.yaml"
    p.write_text(VALID_YAML, encoding="utf-8")
    manifest = load_manifest(p)
    assert set(manifest.layer_names()) == {"presentation", "application", "domain"}
    assert manifest.layer("presentation").may_depend_on == frozenset({"application"})
    assert manifest.allows("presentation", "application")
    assert not manifest.allows("presentation", "domain")


def test_load_manifest_missing_layers(tmp_path: Path) -> None:
    p = tmp_path / "manifest.yaml"
    p.write_text("foo: bar\n", encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(p)


def test_load_manifest_invalid_may_depend_on(tmp_path: Path) -> None:
    p = tmp_path / "manifest.yaml"
    p.write_text("layers:\n  a:\n    may_depend_on: notalist\n", encoding="utf-8")
    with pytest.raises(ManifestError):
        load_manifest(p)


def _mapper() -> LayerMapper:
    manifest = ArchitectureManifest(
        {
            "presentation": Layer("presentation", frozenset({"application"})),
            "application": Layer("application", frozenset({"domain"})),
            "domain": Layer("domain", frozenset()),
        }
    )
    rules = (
        LayerRule("presentation", ("ui/", "presentation/")),
        LayerRule("application", ("application/", "app/")),
        LayerRule("domain", ("domain/", "domain_models/")),
    )
    return LayerMapper(manifest, rules)


def test_mapper_assignment_by_prefix(tmp_path: Path) -> None:
    mapper = _mapper()
    root = tmp_path / "src"
    assert mapper.layer_for(root / "ui" / "App.ts", root) == "presentation"
    assert mapper.layer_for(root / "app" / "service.ts", root) == "application"
    assert mapper.layer_for(root / "domain" / "model.py", root) == "domain"


def test_mapper_fallback_to_first_segment(tmp_path: Path) -> None:
    mapper = _mapper()
    root = tmp_path / "src"
    assert mapper.layer_for(root / "infra" / "db.py", root) == "infra"
