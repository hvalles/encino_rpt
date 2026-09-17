# Roadmap: encino-rpt

## Overview

Hardening de `encino-rpt`, un reporteador financiero que produce un árbol canónico (pydantic) con renderers a HTML, Excel, CSV, PDF y texto. El viaje prioriza **corrección y seguridad primero** (quick wins → correctness → robustez → seguridad), luego **rendimiento**, después **features** (Link/Image, layout, JSON versionado), y cierra con **refactor** (traversal compartido, `GroupSpec` inmutable) y **tests/CI** consolidados. Cada oleada entrega una capacidad verificable e independiente, con tests de regresión por oleada que se consolidan en la fase final.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Quick Wins (Corrección low-risk)** - Fixes de bajo riesgo: precisión de `format_value`, `order_by`, sanitizer CSV, y quitar `encino-orm` *(vía GSD)*
- [x] **Phase 2: Correctness Crítico** - `run()` idempotente, SUM de Excel sin doble-conteo, sanitización total en Excel *(implementación directa)*
- [x] **Phase 3: Robustez** - Errores con contexto, fallos silenciosos eliminados, evaluador anti-DoS *(implementación directa)*
- [x] **Phase 4: Seguridad** - Inyección CSS en estilos condicionales HTML *(implementación directa)*
- [x] **Phase 5: Rendimiento** - Pivot en una sola pasada, grupos por ruta iterativos *(implementación directa)*
- [x] **Phase 6: Features** - Renderizado Link/Image, campos de layout, renderer JSON versionado *(implementación directa)*
- [x] **Phase 7: Refactor** - Traversal compartido, `GroupSpec` inmutable + validación *(implementación directa)*
- [ ] **Phase 8: Tests & CI** - Tests de regresión consolidados + CI endurecido

## Phase Details

### Phase 1: Quick Wins (Corrección low-risk)

**Goal**: Eliminar bugs puntuales de corrección/seguridad de bajo riesgo sin tocar la arquitectura — números grandes conservan precisión, `order_by` funciona con funciones custom y con total ausente, el sanitizer CSV es robusto, y la dependencia muerta desaparece.
**Depends on**: Nothing (first phase)
**Requirements**: CORR-02, CORR-04, CORR-05, SEC-02, DEP-01
**Success Criteria** (what must be TRUE):

  1. `format_value` conserva precisión completa en números grandes con `decimals=None` — `format_value(1234567.89, Format())` devuelve `"1234567.89"`, no `"1.23457e+06"`.
  2. `order_by(expression=...)` evalúa con las funciones custom registradas vía `add_function` (p. ej. `order_by(expression="doblado(monto)")` ya no lanza `ExpressionError`).
  3. `order_by(total=...)` con un total inexistente lanza un error claro que nombra el total, en lugar de un `TypeError` crudo.
  4. El sanitizer CSV detecta caracteres peligrosos precedidos de espacio/BOM — `" =1+1"` y `"\x0c=1+1"` quedan saneados.
  5. `encino-orm` se elimina de `pyproject.toml`; una instalación nueva ya no arrastra esa dependencia.

**Plans**: 3 planes

Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Precisión de `format_value` (CORR-02) + sanitizer whitespace/BOM (SEC-02)
- [x] 01-02-PLAN.md — `order_by` con funciones custom y error de total ausente (CORR-04, CORR-05)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-03-PLAN.md — Eliminar `encino-orm` y limpiar docs (DEP-01)

### Phase 2: Correctness Crítico

**Goal**: La agregación y la salida Excel son correctas — `run()` es idempotente, los rangos `SUM` cubren solo filas de detalle, y toda celda Excel pasa por sanitización anti-inyección.
**Depends on**: Phase 1
**Requirements**: CORR-01, CORR-03, SEC-01
**Success Criteria** (what must be TRUE):

  1. Ejecutar `run()` dos veces sobre el mismo `Report` produce un árbol idéntico (sin duplicar grupos ni totales).
  2. Con `formulas=True`, los rangos `SUM` de Excel cubren solo filas de detalle (sin doble-contar subtotales ni datos auxiliares de chart).
  3. Todas las escrituras de celda Excel (headers, labels de total, valores) pasan por `write_excel_cell` — un valor como `=1+1` en un header/total queda como texto inerte, no como fórmula viva.

**Plans**: TBD

### Phase 3: Robustez

**Goal**: Los fallos se reportan con contexto, los modos de fallo silencioso se eliminan, y el evaluador de expresiones resiste entradas patológicas.
**Depends on**: Phase 2
**Requirements**: CORR-06, CORR-07, SEC-04
**Success Criteria** (what must be TRUE):

  1. Los errores de agregación (división por cero, agregado `custom:` no registrado) reportan contexto — grupo, campo e índice de fila — en lugar de una excepción cruda sin ubicación.
  2. Un `source=` desconocido lanza/avisa explícitamente en lugar de caer silenciosamente al dataset principal.
  3. Un token `{{...}}` sin resolver falla o avisa en lugar de sustituirse por cadena vacía.
  4. El evaluador de expresiones maneja exponentes float enormes (`2 ** 1e100`) y expresiones anidadas patológicamente sin `OverflowError`/`RecursionError` crudos (envueltos como `ExpressionError`).

**Plans**: TBD

### Phase 4: Seguridad

**Goal**: Los estilos condicionales HTML no permiten inyección CSS vía valores con `;` u otros caracteres de escape.
**Depends on**: Phase 3
**Requirements**: SEC-03
**Success Criteria** (what must be TRUE):

  1. Un valor de estilo con `;` (p. ej. `background="red;position:fixed"`) se rechaza o codifica — no se inyectan declaraciones CSS adicionales dentro del atributo `style`.
  2. Los valores de estilo legítimos (colores/longitudes permitidas) siguen renderizándose correctamente.

**Plans**: TBD

### Phase 5: Rendimiento

**Goal**: El pivot y la construcción de grupos por ruta son de una sola pasada / iterativos, sin coste cuadrático ni límite de recursión.
**Depends on**: Phase 4
**Requirements**: PERF-01, PERF-02
**Success Criteria** (what must be TRUE):

  1. Los totales de fila/columna del pivot se calculan en una sola pasada — un pivot de alta cardinalidad ya no re-escanea O(rows × uniques).
  2. Los grupos por ruta (`path=`) usan un builder iterativo — rutas de >1000 segmentos ya no lanzan `RecursionError`.
  3. Cada fila se divide por ruta una sola vez (no se re-split en cada nivel de profundidad).

**Plans**: TBD

### Phase 6: Features

**Goal**: Las columnas `Link`/`Image` se renderizan como enlace/imagen, los campos de layout tienen efecto real, y existe un renderer JSON con schema versionado y round-trip validado.
**Depends on**: Phase 5
**Requirements**: FEAT-01, FEAT-02, JSON-01
**Success Criteria** (what must be TRUE):

  1. Las columnas `Link` se renderizan como `<a>` en HTML, `cell.hyperlink` en Excel, texto `label`/`href` en CSV, y enlace en PDF.
  2. Las columnas `Image` se renderizan como `<img>` en HTML (y representación apropiada en los demás renderers).
  3. `page_break`, `repeat_header` (HTML), `column_position` y `show_collapsed`/`default_collapsed` tienen efecto observable en sus renderers correspondientes.
  4. El renderer JSON emite un campo `schema_version` y hace round-trip `model_dump`/`model_validate` (export → re-import → árbol equivalente).

**Plans**: TBD

### Phase 7: Refactor

**Goal**: Un único traversal compartido sustituye las 5 copias divergentes, y `GroupSpec` se trata como inmutable con validación up-front.
**Depends on**: Phase 6
**Requirements**: REF-01, REF-02
**Success Criteria** (what must be TRUE):

  1. Los cinco renderers consumen un único iterador compartido de filas tipadas (una sola implementación de traversal).
  2. `GroupSpec` se trata como inmutable — `run()` construye un grafo interno nuevo sin mutar los specs de entrada.
  3. La validación up-front detecta nombres duplicados, orden `parent`-antes-de-hijo y agregados `custom:` no registrados con errores claros.

**Plans**: TBD

### Phase 8: Tests & CI

**Goal**: Suite de regresión consolidada para todos los fixes + CI endurecido (type checker, format, cobertura, smoke de rendimiento).
**Depends on**: Phase 7
**Requirements**: TEST-01, TEST-02
**Success Criteria** (what must be TRUE):

  1. Existen tests de regresión para cada fix previo (idempotencia, precisión, SUM, sanitización, `order_by`, errores con contexto, multi-dataset, Link/Image, jerarquías profundas).
  2. CI ejecuta type checker, `ruff format --check`, gate de cobertura y smoke test de rendimiento con entradas grandes.
  3. CI pasa end-to-end (todos los checks verdes).

**Plans**: 4 planes

Plans:
**Wave 1**

- [ ] 08-01-PLAN.md — Regresiones TEST-01 en `test_report.py` (7 tests: multi-dataset, suppress_zero, totales None, no-hashable, detail source, count, chart/pivot)
- [ ] 08-02-PLAN.md — Regresiones renderers/seguridad + smoke de rendimiento 50k filas (TEST-01 + TEST-02)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 08-03-PLAN.md — Tooling config (mypy + pytest-cov + secciones `[tool.*]`) + normalización one-time de `ruff format` (TEST-02)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 08-04-PLAN.md — CI jobs `test`+`quality`, triage de mypy y verificación end-to-end de gates (TEST-02)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Quick Wins (Corrección low-risk) | 3/3 | Complete | 2026-09-16 |
| 2. Correctness Crítico | - | Complete (directa) | 2026-09-16 |
| 3. Robustez | - | Complete (directa) | 2026-09-16 |
| 4. Seguridad | - | Complete (directa) | 2026-09-16 |
| 5. Rendimiento | - | Complete (directa) | 2026-09-16 |
| 6. Features | - | Complete (directa) | 2026-09-16 |
| 7. Refactor | - | Complete (directa) | 2026-09-16 |
| 8. Tests & CI | 0/4 | Not started | - |
