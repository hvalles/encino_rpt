# Estrategia de uso de GSD

Estrategia híbrida para decidir cuándo usar la ceremonia completa de GSD y cuándo implementar directo, maximizando valor por costo y minimizando consumo de tokens.

## Principio

**Por defecto, implementación directa.** El valor de GSD está en el análisis y la verificación, no en la ceremonia de ejecución. Para trabajo trivial o mecánico, lanzar `map-codebase`/`plan`/`execute` (con research + planner + checker + executor + verifier, cada uno con contexto fresco) quema cientos de miles de tokens sin valor proporcional.

## Triage por riesgo (default = directo)

| Situación | Acción |
|-----------|--------|
| Tarea trivial / mecánica / bien entendida (fix puntual, doc, config, typo) | **Implementación directa** (default) |
| Antes de decidir *qué* hacer en un cambio grande o desconocido | `map-codebase` (análisis estático) — solo si aporta |
| Bug difícil, no reproducible a simple vista | `/gsd-debug` |
| Feature nueva con decisiones de diseño, refactor transversal, trabajo sensible a seguridad, infra (CI) | `/gsd-execute-phase` (ceremonia completa) |
| Después de cerrar trabajo con riesgo/ambigüedad | `code-review` + `verifier` (read-only, baratos) |
| Tras trabajo directo | Sincronizar `.planning/ROADMAP.md`, `STATE.md`, `PROJECT.md` (edición directa) |

## Reglas

1. **Directo por defecto.** No invocar GSD para lo que se resuelve en un puñado de edits + tests. El usuario puede forzar GSD explícitamente (`/gsd-*`) si quiere la ceremonia.
2. **GSD completo solo con ambigüedad o riesgo.** Feature nueva, refactor transversal, seguridad, infra/CI → vale el overhead.
3. **Análisis barato, no obligatorio.** `code-review` + `verifier` al cerrar trabajo de riesgo; `map-codebase` solo cuando el mapa está desactualizado o el cambio es grande.
4. **Reconciliación ligera tras trabajo directo.** Sincronizar ROADMAP/STATE/PROJECT para no acumular deriva de estado.

## Estado actual (2026-09-17)

- Milestones v1.0–v1.4 completos; proyecto production-ready (`v0.3.1`).
- Sin fases activas; pendientes son backlog menor (GitHub Pages, límite de profundidad JSON, renderers no re-entrantes).
