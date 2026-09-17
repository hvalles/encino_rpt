# Requirements: encino-rpt

**Defined:** 2026-09-16
**Core Value:** Producir reportes financieros correctos y seguros — agregación y renderizado exactos, idempotentes y sin inyecciones.

## v1 Requirements

Requirements para el hardening + features. Cada uno mapea a una fase del roadmap.

### Correctness

- [ ] **CORR-01**: `run()` es idempotente — ejecutar el mismo `Report` dos veces produce el mismo árbol (sin duplicar grupos).
- [ ] **CORR-02**: `format_value` conserva precisión completa en números grandes con `decimals=None` (sin notación científica ni pérdida de dígitos).
- [ ] **CORR-03**: Excel `formulas=True` emite rangos `SUM` que cubren solo filas de detalle (sin doble-contar subtotales ni datos auxiliares de chart).
- [ ] **CORR-04**: `order_by(expression=...)` evalúa con las funciones custom registradas vía `add_function`.
- [ ] **CORR-05**: `order_by(total=...)` con un total inexistente lanza un error claro (nombrando el total) en lugar de un `TypeError` crudo.
- [ ] **CORR-06**: los errores de agregación reportan contexto (grupo, campo, índice de fila) en lugar de excepciones crudas sin ubicación.
- [ ] **CORR-07**: un `source=` desconocido y un token `{{...}}` sin resolver fallan o avisan explícitamente (no sustituyen silenciosamente por vacío/conjunto por defecto).

### Security

- [ ] **SEC-01**: todos los valores de Excel (headers, totales, celdas) pasan por sanitización anti-inyección de fórmulas (`write_excel_cell`).
- [ ] **SEC-02**: el sanitizer CSV detecta caracteres peligrosos precedidos de espacio/BOM (`" =1+1"`).
- [ ] **SEC-03**: los estilos condicionales HTML no permiten inyección CSS vía valores con `;` u otros caracteres de escape.
- [ ] **SEC-04**: el evaluador de expresiones resiste exponentes float enormes y expresiones patológicamente anidadas (sin `OverflowError`/`RecursionError` crudos).

### Performance

- [ ] **PERF-01**: el pivot calcula totales de fila/columna en una sola pasada (sin re-escaneo O(rows × uniques)).
- [ ] **PERF-02**: los grupos por ruta (`path=`) usan un builder iterativo y dividen cada fila una sola vez (sin límite de recursión ~1000).

### Features

- [ ] **FEAT-01**: las columnas `Link`/`Image` se renderizan como enlace/imagen en HTML (`<a>`/`<img>`), Excel (`cell.hyperlink`), CSV (texto `label`/`href`) y PDF.
- [ ] **FEAT-02**: `page_break`, `repeat_header` (HTML), `column_position` y `show_collapsed`/`default_collapsed` tienen efecto real en los renderers correspondientes.

### Refactor

- [ ] **REF-01**: el traversal del árbol está compartido (iterador único de filas tipadas) en lugar de 5 copias divergentes.
- [ ] **REF-02**: `GroupSpec` se trata como inmutable y se validan up-front nombres duplicados, orden `parent`-antes-de-hijo y agregados `custom:` registrados.

### Dependencies

- [ ] **DEP-01**: la dependencia muerta `encino-orm` se elimina de `pyproject.toml`.

### JSON

- [ ] **JSON-01**: existe un renderer JSON con schema versionado (campo `schema_version` + round-trip `model_dump`/`model_validate` validado).

### Testing

- [x] **TEST-01**: hay tests de regresión para cada uno de los fixes anteriores (idempotencia, precisión, SUM, sanitización, `order_by`, errores con contexto, multi-dataset, Link/Image, jerarquías profundas).
- [x] **TEST-02**: CI incluye type checker, `ruff format --check`, gate de cobertura y smoke test de rendimiento con entradas grandes.

## v2 Requirements

Deferred. No en el roadmap actual.

- **FEAT-02b**: renderers Markdown/LaTeX — no seleccionado.
- **INTEG-01**: integración oficial con `encinorm` (`fetch_all` → `Report`) — no seleccionado.
- **CHART-01**: gráficos como imagen server-side (matplotlib) — degradación a tabla por ahora.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Generación de SQL / consulta a BD | El diseño delega agregados pesados a `ROLLUP`/`CUBE` |
| Motor de agregación server-side | No-objetivo documentado en `docs/design/10-report.md` |
| Renderers Markdown/LaTeX | No seleccionado |
| Integración encinorm | No seleccionado (deferido a v2) |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORR-01 | Phase 2 | Pending |
| CORR-02 | Phase 1 | Pending |
| CORR-03 | Phase 2 | Pending |
| CORR-04 | Phase 1 | Pending |
| CORR-05 | Phase 1 | Pending |
| CORR-06 | Phase 3 | Pending |
| CORR-07 | Phase 3 | Pending |
| SEC-01 | Phase 2 | Pending |
| SEC-02 | Phase 1 | Pending |
| SEC-03 | Phase 4 | Pending |
| SEC-04 | Phase 3 | Pending |
| PERF-01 | Phase 5 | Pending |
| PERF-02 | Phase 5 | Pending |
| FEAT-01 | Phase 6 | Pending |
| FEAT-02 | Phase 6 | Pending |
| REF-01 | Phase 7 | Pending |
| REF-02 | Phase 7 | Pending |
| DEP-01 | Phase 1 | Pending |
| JSON-01 | Phase 6 | Pending |
| TEST-01 | Phase 8 | Complete |
| TEST-02 | Phase 8 | Complete |

**Coverage:**
- v1 requirements: 21 total
- Mapped to phases: 21 (roadmap creado)
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-16*
*Last updated: 2026-09-16 after roadmap (traceability filled)*
