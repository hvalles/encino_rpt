# encino-rpt

## What This Is

`encino-rpt` es un reporteador financiero en Python que consume `list[dict]` (la salida de consultas ya materializadas) y produce un **árbol canónico de datos** (pydantic, serializable a JSON) con renderers opcionales a HTML, Excel, CSV, PDF y texto. Está dirigido a desarrolladores que necesitan reportes financieros — jerarquías de cortes, totales, pivotes, gráficos, KPIs y celdas enriquecidas (enlaces/imágenes) — sin acoplarse a un motor de base de datos.

## Core Value

Producir reportes financieros **correctos y seguros**: la agregación y el renderizado deben dar resultados exactos, idempotentes y sin inyecciones, siempre.

## Requirements

### Validated

<!-- Capacidades existentes inferidas del codebase map (.planning/codebase/) -->

- ✓ Builder fluido `Report` (grupos, secciones, detalle, campos calculados, enlaces, imágenes, KPIs, multi-dataset) — existente
- ✓ Motor de agregación (agrupación por columna/clave compuesta/jerarquía por ruta, grupos anidados, totales) — existente
- ✓ Evaluador seguro de expresiones (`ast` whitelist, sin `eval`) — existente
- ✓ Plantillas `{{token}}` / `{{param.N}}` / `{{total.NOMBRE}}` — existente
- ✓ Totales (`sum/avg/count/count_distinct/max/min/custom`) + condicionales + referencias cruzadas `TOTAL()` — existente
- ✓ Gráficos (pie/bar/line) y pivotes (cross-tab) — existente
- ✓ Formato condicional (estilos por regla) — existente
- ✓ 5 renderers: HTML, Excel (openpyxl), CSV, PDF (reportlab), texto — existente
- ✓ Serialización JSON vía `model_dump()` — existente

### Active

<!-- Endurecer + completar + feature nueva. Hipótesis hasta que se validen. -->

- [ ] `run()` es idempotente (re-ejecutar no duplica grupos)
- [ ] `format_value` conserva precisión en números grandes (sin `1e+06`)
- [ ] Excel `formulas=True` no doble-conta subtotales ni datos auxiliares de chart
- [ ] Totales, headers y celdas de Excel pasan por sanitización anti-inyección
- [ ] CSV sanitizer resiste espacios/BOM previos a caracteres peligrosos
- [ ] `order_by` funciona con `expression=` (funciones custom) y con total ausente (error claro)
- [ ] Errores de agregación reportan contexto (grupo/campo/fila), no excepciones crudas
- [ ] `source=` desconocido y tokens `{{...}}` sin resolver fallan o avisan, no callan
- [ ] Evaluador de expresiones robusto ante exponentes float y expresiones patológicas
- [ ] Estilos HTML condicionales no permiten inyección CSS vía `;`
- [ ] Pivot calcula totales en una sola pasada (sin O(rows × uniques))
- [ ] Grupos por ruta usan builder iterativo (sin límite de recursión ~1000)
- [ ] Link/Image se renderizan como enlace/imagen en HTML/Excel/CSV/PDF
- [ ] `page_break`, `repeat_header` (HTML), `column_position` y `show_collapsed`/`default_collapsed` tienen efecto real
- [ ] Traversal de renderers compartido (iterador único en lugar de 5 copias divergentes)
- [ ] `GroupSpec` tratado como inmutable + validación up-front (nombres duplicados, `parent` antes de hijo, `custom:` registrado)
- [ ] Dependencia muerta `encino-orm` eliminada
- [ ] Renderer JSON con schema versionado (export estable + round-trip validado)
- [ ] Cobertura de tests de regresión para todos los fixes
- [ ] CI con type checker, `ruff format --check`, gate de cobertura y smoke de rendimiento

### Out of Scope

- Generación de SQL / consulta a BD — el diseño delega agregados pesados a `GROUP BY ROLLUP`/`CUBE`
- Motor de agregación server-side para grandes volúmenes — el reporteador solo ensambla resultados materializados
- Gráficos como imágenes server-side (matplotlib) — los renderers degradan `chart` a tabla resumen
- Renderers Markdown/LaTeX — no seleccionado
- Integración oficial con `encinorm` — no seleccionado (deferido)

## Context

- **Código existente mapeado** en `.planning/codebase/` (STACK, ARCHITECTURE, STRUCTURE, CONVENTIONS, TESTING, INTEGRATIONS, CONCERNS).
- **Análisis de concerns** en `.planning/codebase/CONCERNS.md`: 196 líneas de hallazgos validados contra el código (bugs de correctness/seguridad, deuda, rendimiento, gaps de features y de tests).
- **Plan de oleadas 0–7** derivado de ese análisis (corrección primero): quick wins → correctness → robustez → seguridad → rendimiento → features → refactor → tests/CI.
- **Diseño de referencia** en `docs/design/10-report.md` (contrato §8 para Link/Image, `page_break`, `repeat_header`, `column_position`, `show_collapsed`/`default_collapsed`).
- Proyecto PyPI `encino-rpt` (v0.2.1), licencia MIT, `requires-python >=3.10`.

## Constraints

- **Tech stack**: Python `>=3.10`; `pydantic>=2` como única dependencia de runtime; `openpyxl` (extra `excel`) y `reportlab` (extra `pdf`) opcionales.
- **Seguridad**: nunca `eval`; evaluador de expresiones con whitelist `ast`; sanitización de fórmulas (OWASP) en Excel/CSV.
- **Compatibilidad**: no romper la API pública existente (`Report`, `Section`, `ReportResult`, `to_*`/`render_*`).
- **Rendimiento**: diseño in-memory; agregados pesados se delegan a SQL (no-objetivo documentado).

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Estructura por oleadas (corrección primero) | Priorizar correctness/seguridad sobre features nuevas | — Pending |
| Implementar features (no eliminar campos muertos) | Alineado con el contrato de `docs/design/10-report.md` §8 | — Pending |
| Quitar `encino-orm` | Dependencia de runtime sin uso (nada lo importa) | — Pending |
| Añadir renderer JSON con schema versionado | Export estable + round-trip validado, más allá de `model_dump()` crudo | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-16 after initialization*
