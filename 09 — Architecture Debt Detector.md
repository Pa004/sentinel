# 09 — Architecture Debt Detector

> Analizador de erosión arquitectónica, violaciones estructurales y evolución de deuda arquitectónica.

## Problema

Las métricas convencionales detectan problemas locales:

```text
Cyclomatic complexity
LOC
Duplication
```

pero pueden no detectar:

```text
Circular dependencies
Layer violations
God modules
Architecture erosion
Database leakage
High coupling
```

## Vacío

Comparar:

```text
Architecture Intended
        vs
Architecture Observed
```

## Innovación

Crear un modelo arquitectónico versionado.

## Ejemplo

```text
UI
 ↓
API
 ↓
Service
 ↓
Database
```

Violación:

```text
UI → Database
```

## Arquitectura

```text
Repository
   ↓
Parser
   ↓
Symbol Graph
   ↓
Dependency Graph
   ↓
Architecture Manifest
   ↓
Rule Engine
   ↓
Violation Engine
   ↓
Trend Analysis
```

## Manifest

```yaml
layers:
  presentation:
    may_depend_on:
      - application

  application:
    may_depend_on:
      - domain

  domain:
    may_depend_on: []
```

## Detecciones

- cycles;
- illegal dependencies;
- coupling;
- cohesion;
- god modules;
- boundary crossing;
- architectural drift.

## Lenguajes iniciales

- C#;
- Java;
- TypeScript;
- Python.

## Stack

- Rust;
- Tree-sitter;
- Python;
- React;
- TypeScript;
- SQLite;
- Git.

## Testing

Construir repositorios sintéticos con arquitectura conocida:

```text
GOOD
BAD
EVOLVING
```

Validar que cada violation sea detectada.

## Métricas

```text
Violations
Trend
Coupling
Cycle count
Layer violations
Architecture drift
```

## Metodología

```text
Architecture Definition
 ↓
Repository Analysis
 ↓
Observed Graph
 ↓
Comparison
 ↓
Violation
 ↓
Trend
 ↓
Remediation
```

## Prompt maestro

Actúa como **Senior Software Architect y Static Analysis Engineer**.

Construye Architecture Debt Detector.

No conviertas el producto en un simple linter.

Debe analizar la arquitectura como un sistema de relaciones.

Permite declarar una arquitectura objetivo y comparar contra la arquitectura observada.

Cada violation debe incluir:

- regla;
- evidencia;
- componentes;
- impacto;
- commit donde apareció;
- recomendación.

El sistema debe detectar también **regresión arquitectónica** entre commits.

## Resultado

Un producto de arquitectura y developer productivity capaz de medir cómo un sistema pierde estructura con el tiempo.