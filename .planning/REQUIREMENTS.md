# Requirements: encino-rpt

**Defined:** 2026-09-16
**Core Value:** Producir reportes financieros correctos y seguros — agregación y renderizado exactos, idempotentes y sin inyecciones.

## v1 Requirements

Requirements para el hardening + features. Cada uno mapea a una fase del roadmap.

### Correctness

- [x] **CORR-01**: `run()` es idempotente — ejecutar el mismo `Report` dos veces produce el mismo árbol (sin duplicar grupos).
- [x] **CORR-02**: `format_value` conserva precisión completa en números grandes con `decimals=None` (sin notación científica ni pérdida de dígitos).
- [x] **CORR-03**: Excel `formulas=True` emite rangos `SUM` que cubren solo filas de detalle (sin doble-contar subtotales ni datos auxiliares de chart).
- [x] **CORR-04**: `order_by(expression=...)` evalúa con las funciones custom registradas vía `add_function`.
- [x] **CORR-05**: `order_by(total=...)` con un total inexistente lanza un error claro (nombrando el total) en lugar de un `TypeError` crudo.
- [x] **CORR-06**: los errores de agregación reportan contexto (grupo, campo, índice de fila) en lugar de excepciones crudas sin ubicación.
- [x] **CORR-07**: un `source=` desconocido y un token `{{...}}` sin resolver fallan o avisan explícitamente (no sustituyen silenciosamente por vacío/conjunto por defecto).

### Security

- [x] **SEC-01**: todos los valores de Excel (headers, totales, celdas) pasan por sanitización anti-inyección de fórmulas (`write_excel_cell`).
- [x] **SEC-02**: el sanitizer CSV detecta caracteres peligrosos precedidos de espacio/BOM (`" =1+1"`).
- [x] **SEC-03**: los estilos condicionales HTML no permiten inyección CSS vía valores con `;` u otros caracteres de escape.
- [x] **SEC-04**: el evaluador de expresiones resiste exponentes float enormes y expresiones patológicamente anidadas (sin `OverflowError`/`RecursionError` crudos).

### Performance

- [x] **PERF-01**: el pivot calcula totales de fila/columna en una sola pasada (sin re-escaneo O(rows × uniques)).
- [x] **PERF-02**: los grupos por ruta (`path=`) usan un builder iterativo y dividen cada fila una sola vez (sin límite de recursión ~1000).

### Features

- [x] **FEAT-01**: las columnas `Link`/`Image` se renderizan como enlace/imagen en HTML (`<a>`/`<img>`), Excel (`cell.hyperlink`), CSV (texto `label`/`href`) y PDF.
- [x] **FEAT-02**: `page_break`, `repeat_header` (HTML), `column_position` y `show_collapsed`/`default_collapsed` tienen efecto real en los renderers correspondientes.

### Refactor

- [x] **REF-01**: el traversal del árbol está compartido (iterador único de filas tipadas) en lugar de 5 copias divergentes.
- [x] **REF-02**: `GroupSpec` se trata como inmutable y se validan up-front nombres duplicados, orden `parent`-antes-de-hijo y agregados `custom:` registrados.

### Dependencies

- [x] **DEP-01**: la dependencia muerta `encino-orm` se elimina de `pyproject.toml`.

### JSON

- [x] **JSON-01**: existe un renderer JSON con schema versionado (campo `schema_version` + round-trip `model_dump`/`model_validate` validado).

### Testing

- [x] **TEST-01**: hay tests de regresión para cada uno de los fixes anteriores (idempotencia, precisión, SUM, sanitización, `order_by`, errores con contexto, multi-dataset, Link/Image, jerarquías profundas).
- [x] **TEST-02**: CI incluye type checker, `ruff format --check`, gate de cobertura y smoke test de rendimiento con entradas grandes.

## v1.1 Requirements

Milestone v1.1: Readers multi-formato + Templates HTML/Markdown.

### Readers

- [x] **READ-01**: existe un protocolo/ABC `Reader` (`read(source, **opts) -> list[dict]`) y un registro de readers custom (patrón `add_function`/`add_aggregate`).
- [x] **READ-02**: readers stdlib incluidos: `csv`, texto delimitado (TSV), `json`, `jsonl`, `tuples` (con `columns=` para mapear posición→nombre).
- [x] **READ-03**: reader `excel` (openpyxl) tras el extra `excel`; lanza `ImportError` con hint si falta.
- [x] **READ-04**: auto-detección de tipos determinista por celda (`int`→`float`→`bool`→`null`→`str`) con opt-out `coerce=False`; documentado y con test de borde para valores mixtos (p. ej. `"N/A"` queda `str`).
- [x] **READ-05**: `Report(rows=...)` y `add_dataset` intactos (compatibilidad total).

### Templates / Markdown

- [x] **TMPL-01**: `render_html(css=True)` emite clases + bloque `<style>` en vez de `style="…"` inline (opt-in), preservando `_SAFE_PROP`/`_UNSAFE_VALUE`/`_esc`.
- [x] **TMPL-02**: `render_html(template=...)` envuelve la tabla en un documento HTML completo (`<head>`+`<style>`+`<body>`).
- [x] **TMPL-03**: existe `MarkdownRenderer` + `to_markdown()` (tablas GFM con escapado de `|`/newline, links/imágenes nativos, chart→texto).
- [x] **TMPL-04**: sin regresión de inyección CSS/HTML; plantillas solo vía sandbox `template.py` (`{{token}}`), nunca Jinja2 arbitrario.

### Streaming (diferido)

- [x] **STRM-01**: salida en streaming (`iter_csv`/`iter_text`/`iter_html`/`iter_markdown` + `file=` en `to_csv`/`to_text`/`to_markdown`/`render_html`/`to_pdf`). Entrada en streaming descartada (no-objetivo).

## v1.2 Requirements

Milestone v1.2: Engine bug fixes (correctness). Bugs documentados en `CONCERNS.md`.

- [ ] **CORR-08**: `detail(source=...)` usa el dataset indicado (multi-dataset detail), no el principal.
- [ ] **CORR-09**: totales nombrados con valor `None` no rompen el acumulador del registro (`0 + None`).
- [ ] **CORR-10**: errores de chart/pivot se envuelven con contexto de grupo (`_wrap`).
- [ ] **CORR-11**: `suppress_zero(column=...)` con columna inexistente lanza error claro (no suprime todo el grupo).
- [ ] **CORR-12**: valores no hashables al agrupar/pivotear lanzan error claro (no `TypeError` crudo).
- [ ] **CORR-13**: `count` con `expression=` tiene semántica documentada y consistente.
- [ ] **CORR-14**: jerarquías profundas no revientan `to_json()`/`model_dump()` con `RecursionError` (límite documentado o error claro).

## v2 Requirements

Deferred. No en el roadmap actual.

- **FEAT-02b**: renderer LaTeX — no seleccionado.
- **INTEG-01**: integración oficial con `encinorm` (`fetch_all` → `Report`) — no seleccionado.
- **CHART-01**: gráficos como imagen server-side (matplotlib) — degradación a tabla por ahora.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Generación de SQL / consulta a BD | El diseño delega agregados pesados a `ROLLUP`/`CUBE` |
| Motor de agregación server-side | No-objetivo documentado en `docs/design/10-report.md` |
| Renderer LaTeX | No seleccionado (Markdown seleccionado en v1.1) |
| Integración encinorm | No seleccionado (deferido a v2) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORR-01 | Phase 2 | Complete |
| CORR-02 | Phase 1 | Complete |
| CORR-03 | Phase 2 | Complete |
| CORR-04 | Phase 1 | Complete |
| CORR-05 | Phase 1 | Complete |
| CORR-06 | Phase 3 | Complete |
| CORR-07 | Phase 3 | Complete |
| SEC-01 | Phase 2 | Complete |
| SEC-02 | Phase 1 | Complete |
| SEC-03 | Phase 4 | Complete |
| SEC-04 | Phase 3 | Complete |
| PERF-01 | Phase 5 | Complete |
| PERF-02 | Phase 5 | Complete |
| FEAT-01 | Phase 6 | Complete |
| FEAT-02 | Phase 6 | Complete |
| REF-01 | Phase 7 | Complete |
| REF-02 | Phase 7 | Complete |
| DEP-01 | Phase 1 | Complete |
| JSON-01 | Phase 6 | Complete |
| TEST-01 | Phase 8 | Complete |
| TEST-02 | Phase 8 | Complete |
| READ-01 | Phase 9 | Complete |
| READ-02 | Phase 9 | Complete |
| READ-03 | Phase 9 | Complete |
| READ-04 | Phase 9 | Complete |
| READ-05 | Phase 9 | Complete |
| TMPL-01 | Phase 10 | Complete |
| TMPL-02 | Phase 10 | Complete |
| TMPL-03 | Phase 10 | Complete |
| TMPL-04 | Phase 10 | Complete |
| STRM-01 | Direct (streaming de salida) | Complete |
| CORR-08 | Phase 11 | Pending |
| CORR-09 | Phase 11 | Pending |
| CORR-10 | Phase 11 | Pending |
| CORR-11 | Phase 11 | Pending |
| CORR-12 | Phase 11 | Pending |
| CORR-13 | Phase 11 | Pending |
| CORR-14 | Phase 11 | Pending |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21 (roadmap creado)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-16*
*Last updated: 2026-09-16 after roadmap (traceability filled)*
