---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Engine bug fixes (correctness)
status: complete
stopped_at: Completed 11-01-PLAN.md
last_updated: 2026-09-17T13:49:48Z
last_activity: 2026-09-17
progress:
  total_phases: 11
  completed_phases: 11
  total_plans: 10
  completed_plans: 10
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-16)

**Core value:** Producir reportes financieros correctos y seguros — agregación y renderizado exactos, idempotentes y sin inyecciones.
**Current focus:** Milestone v1.2 — Engine bug fixes (correctness)

## Current Position

Phase: 11
Plan: 01 complete (Engine bug fixes)
Status: Complete
Last activity: 2026-09-17

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**

- Total plans completed: 10
- Average duration: - min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3 | - | - |
| 08 | 4 | - | - |
| 09 | 1 | - | - |
| 10 | 1 | - | - |
| 11 | 1 | - | - |

**Recent Trend:**

- Last 5 plans: -
- Trend: -

*Updated after each plan completion*
| Phase 8 P1 | 8min | 2 tasks | 1 files |
| Phase 8 P2 | 5min | 3 tasks | 3 files |
| Phase 08 P03 | 4min | 2 tasks | 22 files |
| Phase 08 P04 | 11min | 3 tasks | 7 files |
| Phase 9 P1 | 5min | 3 tasks | 4 files |
| Phase 10 P1 | 7min | 4 tasks | 5 files |
| Phase 11 P1 | 7min | 5 tasks | 8 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Estructura por oleadas (corrección primero): priorizar correctness/seguridad antes que features.
- Implementar features (no eliminar campos muertos): alineado con `docs/design/10-report.md` §8.
- Quitar `encino-orm`: dependencia de runtime sin uso.
- Añadir renderer JSON con schema versionado.
- [Phase 8]: Los bugs no-corregidos del engine se documentan con tests de regresión (assert comportamiento actual + comentario # CONCERNS.md), no se corrigen en esta fase
- [Phase 8]: Los bugs no-corregidos (JSON profundo, params muertos Excel, null byte) se documentan con assert del comportamiento actual + comentario # CONCERNS.md; TEST-02 no se marca completo (08-02 solo aporta el gate de smoke de rendimiento)
- [Phase 08]: mypy 2.3.1 elegido (no 1.x) — el plugin pydantic.mypy carga sin error; ruff format scoped a encino_rpt tests (nunca .) para no barrer los .md de .planning/ y docs/
- [Phase 08]: TEST-02 NO se marca completo en 08-03: solo aporta tooling + normalización; los jobs de CI (type check, format gate, coverage gate) aterrizan en 08-04
- [Phase 08]: mypy 2.3.1 confirmado (contingencia 1.20.2 NO necesaria): el plugin pydantic.mypy carga y el triage completa sin pinar 1.x
- [Phase 08]: disable_error_code=[import-untyped] para openpyxl/reportlab en lugar de # type: ignore por línea: evita fricción con ruff isort (I001) y es el relax justificado que el plan permite
- [Phase 08]: quality job sin needs (paralelo a test), replicando el patrón multi-job de publish.yml/docs.yml
- [Phase 09]: `Reader` como `typing.Protocol` (no ABC); `coerce` aplica solo a texto delimitado (csv/tsv) — json/jsonl/tuples/excel preservan tipos ya tipados para no corromper IDs tipo `"001"`.
- [Phase 10]: modo clases HTML opt-in (`css=False` por defecto, byte-idéntico al inline); el CSS del bloque `<style>` reutiliza `_SAFE_PROP`/`_UNSAFE_VALUE`/`_esc` (sin superficie de inyección nueva).
- [Phase 10]: `MarkdownRenderer` consume `walk()`; `_md_cell` escapa valores planos y emite links/imágenes nativos, `_md_table` escapa solo headers (evita doble-escape de `|`); wrapper de documento estructural (nunca Jinja2).
- [v1.1 Streaming]: SQLite temp-table descartado (pre-agregación fuera de alcance: rompe funciones custom, contradice el no-objetivo SQL y no resuelve la memoria de salida); streaming de ENTRADA = no-objetivo definitivo; streaming de SALIDA implementado (iter_csv/iter_text/iter_html/iter_markdown + `file=`), manteniendo el path `to_*` sin `file=` byte-idéntico.
- [Phase 11]: CORR-08 = `detail(source=)` solo a nivel raíz (opción b; con grupos `ValueError`); CORR-13 = `count`+expression conteo condicional (truthy), `count` sin expresión cuenta filas; CORR-09 = total `None` contribuye `0` al registro; CORR-14 = límite de profundidad documentado + `ValueError` claro (no serialización iterativa).

### Pending Todos

None yet.

### Blockers/Concerns

- **[Pendiente · infra · requiere acción manual] Workflow `Docs` falla en `configure-pages@v5`**: causa raíz confirmada — `GET /repos/hvalles/encino_rpt/pages` devuelve **404** (GitHub Pages NO está habilitado en el repo). El `docs.yml` es correcto (permisos `pages: write`/`id-token: write`, `configure-pages`+`upload-pages-artifact`+`deploy-pages`); el build de `mkdocs` pasa. **Fix manual del owner**: Repo Settings → Pages → Source = "GitHub Actions" (y habilitar Pages). No requiere cambio de código.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-09-17T13:49:48Z
Stopped at: Completed 11-01-PLAN.md
Resume file: None
