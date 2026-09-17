# Phase 9: Readers multi-formato — Context

**Gathered:** 2026-09-17
**Status:** Ready for planning
**Source:** discuss v1.1 (decidido con el usuario)

<domain>
## Phase Boundary

`Report` puede consumir fuentes heterogéneas (CSV, texto delimitado, JSON, JSONL, tuplas, Excel) mediante readers registrables, sin tocar el motor ni romper `Report(rows=...)`.
</domain>

<decisions>
## Implementation Decisions

### Protocolo `Reader`
- `Reader` = Protocol con `read(source, **opts) -> list[dict]`.
- Registro a nivel módulo `encino_rpt/readers.py` (dict `_READERS` + `register_reader`/`get_reader`), patrón análogo a `add_function`/`add_aggregate`.
- `Report.read(...)` y `Report.register_reader(...)` como classmethods que delegan en el módulo readers.

### Auto-detección de tipos (decisión del usuario)
- Default: **auto-detección determinista** por celda, orden: `null` (`""`/`"null"`/`"none"`) → `bool` (`true`/`false`) → `int` → `float` → si nada aplica, queda `str` (valor original).
- Opt-out `coerce=False` → todo `str`.
- Documentado en README/guide; test que fija el comportamiento con valores mixtos (`"N/A"` queda `str`).

### Formatos
- stdlib: `csv` (delimiter `,`), `tsv` (delimiter `\t`), `json`, `jsonl`, `tuples` (requiere `columns=`).
- `excel` (openpyxl) tras el extra `excel`; `ImportError` con hint si falta.
- Resolución de `format` por extensión de archivo si no se pasa explícito.

### Fuente
- `source` puede ser: ruta (str/PathLike), objeto file-like (`.read()`), o (para json/tuples) datos crudos.
</decisions>

<canonical_refs>
## Canonical References

- `encino_rpt/report.py` — `add_function`/`add_aggregate` (patrón de registro), `__init__(rows, ...)`.
- `encino_rpt/renderers/excel.py` — patrón de import perezoso + `ImportError` con hint (`encino-rpt[excel]`).
- `tests/test_report.py`, `tests/test_report_renderers.py` — convenciones de test.
- `docs/design/10-report.md:36` — contrato de entrada `list[dict]`.
</canonical_refs>

<specifics>
## Specific Ideas

- CSV/TSV usan `csv.DictReader` (primera fila = headers) → `list[dict]` directo.
- JSON: `json.load` sobre array de objetos; JSONL: un objeto por línea.
- Tuplas: `list[tuple]` + `columns=` → `dict(zip(columns, row))`.
- Excel: `openpyxl.load_workbook`, primera hoja, primera fila = headers.
</specifics>

<deferred>
## Deferred Ideas

- Streaming de entrada (no-objetivo).
- Coerción configurable por columna (solo global `coerce=` por ahora).
</deferred>

---

*Phase: 09-readers-multi-formato*
*Context gathered: 2026-09-17*
