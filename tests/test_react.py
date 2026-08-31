"""Tests for React component analysis."""

from __future__ import annotations

from pathlib import Path

from sentinel.analyzers.react_analyzer import detect_react_component
from sentinel.rules.react_component import ReactComponentRule


def test_detect_react_component_tsx(tmp_path: Path) -> None:
    f = tmp_path / "Button.tsx"
    f.write_text(
        'import React from "react";\n'
        "interface Props { label: string; onClick: () => void; }\n"
        "export default function Button({ label, onClick }: Props) {\n"
        "  return <button onClick={onClick}>{label}</button>;\n"
        "}\n",
        encoding="utf-8",
    )
    component = detect_react_component(f)
    assert component is not None
    assert component.name == "Button"
    assert component.prop_count == 2
    assert component.has_hooks is False
    assert component.export_default is True


def test_detect_react_component_with_hooks(tmp_path: Path) -> None:
    f = tmp_path / "Counter.tsx"
    f.write_text(
        'import React, { useState } from "react";\n'
        "export default function Counter() {\n"
        "  const [count, setCount] = useState(0);\n"
        "  return <div>{count}</div>;\n"
        "}\n",
        encoding="utf-8",
    )
    component = detect_react_component(f)
    assert component is not None
    assert component.has_hooks is True
    assert component.prop_count == 0


def test_detect_not_react_file(tmp_path: Path) -> None:
    f = tmp_path / "utils.ts"
    f.write_text("export const add = (a: number, b: number) => a + b;\n", encoding="utf-8")
    component = detect_react_component(f)
    assert component is None


def test_detect_not_react_py(tmp_path: Path) -> None:
    f = tmp_path / "app.py"
    f.write_text("def hello(): pass\n", encoding="utf-8")
    component = detect_react_component(f)
    assert component is None


def test_oversized_component_detected(tmp_path: Path) -> None:
    f = tmp_path / "BigComponent.tsx"
    lines = ['import React from "react";\n']
    lines.append("export default function BigComponent() {\n")
    lines.extend(f"  const x{i} = {i};\n" for i in range(160))
    lines.append("  return <div />;\n")
    lines.append("}\n")
    f.write_text("".join(lines), encoding="utf-8")
    from sentinel.analyzers.dependency_extractor import build_dependency_graph

    graph = build_dependency_graph((f,))
    from sentinel.domain.manifest import ArchitectureManifest, Layer

    manifest = ArchitectureManifest({"ui": Layer("ui", frozenset())})
    from sentinel.manifest.mapper import LayerMapper, LayerRule

    mapper = LayerMapper(manifest, (LayerRule("ui", ("",)),))
    violations = ReactComponentRule(max_lines=150).check(graph, manifest, mapper, tmp_path)
    assert any(v.rule == "react_oversized_component" for v in violations)


def test_too_many_props_detected(tmp_path: Path) -> None:
    f = tmp_path / "Form.tsx"
    props = ", ".join(f"prop{i}: string" for i in range(10))
    f.write_text(
        'import React from "react";\n'
        f"export default function Form({{ {props} }}: Props) {{\n"
        "  return <div />;\n"
        "}\n",
        encoding="utf-8",
    )
    from sentinel.analyzers.dependency_extractor import build_dependency_graph

    graph = build_dependency_graph((f,))
    from sentinel.domain.manifest import ArchitectureManifest, Layer

    manifest = ArchitectureManifest({"ui": Layer("ui", frozenset())})
    from sentinel.manifest.mapper import LayerMapper, LayerRule

    mapper = LayerMapper(manifest, (LayerRule("ui", ("",)),))
    violations = ReactComponentRule(max_props=8).check(graph, manifest, mapper, tmp_path)
    assert any(v.rule == "react_too_many_props" for v in violations)


def test_small_component_not_flagged(tmp_path: Path) -> None:
    f = tmp_path / "Badge.tsx"
    f.write_text(
        'import React from "react";\n'
        "export default function Badge({ text }: { text: string }) {\n"
        "  return <span>{text}</span>;\n"
        "}\n",
        encoding="utf-8",
    )
    from sentinel.analyzers.dependency_extractor import build_dependency_graph

    graph = build_dependency_graph((f,))
    from sentinel.domain.manifest import ArchitectureManifest, Layer

    manifest = ArchitectureManifest({"ui": Layer("ui", frozenset())})
    from sentinel.manifest.mapper import LayerMapper, LayerRule

    mapper = LayerMapper(manifest, (LayerRule("ui", ("",)),))
    violations = ReactComponentRule().check(graph, manifest, mapper, tmp_path)
    assert violations == []
