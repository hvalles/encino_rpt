# Phase 11: Engine bug fixes — Context

**Gathered:** 2026-09-17
**Status:** Ready for planning (2 decisiones pendientes de confirmar — ver abajo)
**Source:** `CONCERNS.md` (bugs documentados) + `analisys-11.md`

<domain>
## Phase Boundary

Corregir 7 bugs de correctitud del motor de agregación (`aggregation.py`, `report.py`, `pivot.py`, `models.py`/`json.py`), todos documentados con tests de regresión (xfail/assert). El objetivo es **fail-loudly y consistencia**, no nuevas features.
</domain>

<decisions>
## Implementation Decisions

### Enfoques de fix (confirmados por diseño existente)
- **CORR-10** (chart/pivot sin contexto): envolver `build_chart`/`build_pivot` en `_wrap` con `"gráfico (grupo …)"`/`"pivote (grupo …)"`.
- **CORR-11** (`suppress_zero` columna inexistente): lanzar `ValueError` claro (precedente CORR-05/WR-01 en `_sort_key`).
- **CORR-12** (valores no hashables): lanzar `ValueError` claro nombrando columna (no `TypeError` crudo).

### Decisiones PENDIENTES de confirmar (marcadas para discuss)
1. **CORR-08 — `detail(source=)`**: semántica del multi-dataset detail. Opciones:
   - (a) `detail(source=X)` reemplaza las filas de detalle de los grupos hoja por `sources[X]`.
   - (b) `detail(source=X)` solo aplica a nivel raíz (sin grupos); con grupos, lanza error de combinación inválida.
   - Recomendado: (b) — acotado y sin ambigüedad de partición.
2. **CORR-13 — `count` sobre `expression=`**: documentar (mantener "cuenta filas con expresión truthy") vs cambiar a "siempre cuenta filas". Recomendado: documentar la semántica actual (conditional count) + test que la fija.
3. **CORR-09 — totales `None` en registro**: `None` contribuye `0` al acumulado cruzado (sum) vs propagar `None`. Recomendado: contribuye `0` (grupo vacío no aporta).
4. **CORR-14 — serialización profunda**: límite documentado + `ValueError` claro (no `RecursionError`) vs serialización iterativa. Recomendado: límite documentado + error claro (la serialización iterativa de pydantic es inviable).
</decisions>

<canonical_refs>
## Canonical References

- `encino_rpt/aggregation.py` — `_partition` (:178), `_compute_totals_into` (:214), `_value_for` (:71), `_is_zero` (:428), chart/pivot (:353-368).
- `encino_rpt/report.py:330-341` — `detail` ignora `source`.
- `encino_rpt/pivot.py` — `buckets.setdefault((rv, cv), [])` (no hashable).
- `encino_rpt/renderers/json.py` — `to_dict`/`model_dump` recursivo.
- `encino_rpt/aggregation.py:334-343` — `_sort_key` (precedente de error claro).
- `tests/test_report.py` — tests xfail que documentan los bugs 1-3.
</canonical_refs>

<specifics>
## Specific Ideas

- Los fixes 3, 4, 5 son mecánicos (guard + `ValueError` con `!r`). El 1 y 6 dependen de las decisiones pendientes. El 7 es documentación + guard en `JsonRenderer`.
- Los tests xfail existentes se convierten a asserts verdes al corregir el bug correspondiente.
</specifics>

<deferred>
## Deferred Ideas

- Params muertos (`ExcelRenderer.styles`, `footer(column_position=)`, chart/pivot `source=`) — fase aparte (limpia, no correctitud).
- Pines de dependencias (`pydantic` tope, extras) — fase de infra.
</deferred>

---

*Phase: 11-engine-bug-fixes*
*Context gathered: 2026-09-17*
