# AGENTS.md

## Estado actual

Este repositorio contiene **solo una especificación**: `09 - Architecture Debt Detector.md`.
No hay código, manifests, config de build ni CI todavía. Nada es ejecutable.

## Qué es el proyecto

Analizador de erosión arquitectónica y deuda de arquitectura. Compara una **arquitectura objetivo** (declarada en un manifest YAML) contra la **arquitectura observada** (dependency graph real extraído con parsers).

Especificación clave del prompt maestro (no convertir en un simple linter — `09...md` #162):
- Analizar arquitectura como un **sistema de relaciones**, no métricas locales (complexity, LOC, duplication).
- Comparar `Architecture Intended` vs `Architecture Observed`.
- Cada violation debe incluir: regla, evidencia, componentes, impacto, commit de origen y recomendación (#174-181).
- Detectar regresión arquitectónica entre commits (#183).

## Flujo arquitectónico definido (respetar)

```
Repository → Parser → Symbol Graph → Dependency Graph → Architecture Manifest → Rule Engine → Violation Engine → Trend Analysis
```

## Stack propuesto (si se implementa)

- Parser: Rust + Tree-sitter
- Backend/CLI: Python
- Frontend: React + TypeScript
- Persistencia: SQLite
- Control de versiones: Git (detección de commits de origen)
- Lenguajes objetivo: C#, Java, TypeScript, Python

## Flujo de trabajo Git (obligatorio)

- **Nunca trabajar directamente en `main`.** Todo desarrollo se hace en una rama.
- Antes de tocar código: crear rama con `git checkout -b <nombre>` (naming: corto y descriptivo, ej. `feat/core-cli`, `fix/circular-rule`).
- Commits de la rama se hacen contra la rama de trabajo, nunca contra `main`.
- Al terminar una feature/fix: abrir un **Pull Request** hacia `main` y resolver cualquier review ahí antes de mergear.
- `main` solo recibe cambios vía merge de PRs aprobados, nunca por commit directo.

## Reglas de seguridad y limpieza del repo

- **Nunca subir archivos `.env`, `.env.*`, credenciales, tokens, API keys, ni ningún secreto al repo.** Si un archivo .env es necesario para el proyecto, solo subir su `.env.example` con valores de ejemplo.
- **Actualizar `.gitignore` a medida que avanza el desarrollo.** Cada vez que se crea o se instala algo generatable (venv, `__pycache__`, `.pyc`, build/, dist/, node_modules/, .db, archivos de IDE, etc.), verificar que esté cubierto en `.gitignore` **antes de hacer commit**. Revisar `git status` antes de cada commit.
- **Nada que no sea estrictamente necesario.** No subir: logs, archivos temporales, resultados de pruebas intermedios, screenshots, dumps de debug, archivos de backup, ni outputs que se regeneran con un comando.
- **Si hay duda, no subir.** Antes de commitear un archivo nuevo, preguntarse: "¿Esto es necesario para que alguien clone el repo y lo haga funcionar?" Si la respuesta es no, no va al commit.

## Cómo verificar (cuando haya código)

La spec define que el testing se hace con repos sintéticos de arquitectura conocida: `GOOD / BAD / EVOLVING`, validando que cada violation sea detectada (#121-131). Usar ese patrón antes de asumir otro framework de test.
