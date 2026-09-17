---
phase: 10-templates-html-markdown
plan: 01
subsystem: rendering
tags: [python, pydantic, html, css, markdown, gfm, renderers]

# Dependency graph
requires:
  - phase: 09-readers-multi-formato
    provides: [Report.read, Reader protocol, test conventions]
provides:
  - "encino_rpt/renderers/html.py: modo clases css=True (rpt-cond-N + <style>) y template de documento completo"
  - "encino_rpt/renderers/markdown.py: MarkdownRenderer + _md_escape/_md_cell/_md_table"
  - "ReportResult.render_html(css/template/title) y ReportResult.to_markdown()"
  - "tests: 7 renderers + 1 seguridad (regresión CSS)"
affects: [docs, future LaTeX renderer, downstream consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Opt-in CSS por clases: _matched_rules -> rpt-cond-N + _style_block reutilizando _SAFE_PROP/_UNSAFE_VALUE/_esc"
    - "Wrapper de documento estructural (nunca motor de templates): <!DOCTYPE html><head><style>…</style></head><body class=\"report\">"
    - "MarkdownRenderer consume walk(); buffer de detalle flusheado en chart/pivot/group_start/group_end"

key-files:
  created: [encino_rpt/renderers/markdown.py]
  modified: [encino_rpt/renderers/html.py, encino_rpt/models.py, encino_rpt/renderers/__init__.py, tests/test_report_renderers.py, tests/test_security.py]

key-decisions:
  - "Modo clases opt-in (css=False por defecto): el path inline byte-idéntico se conserva; el CSS se emite como .rpt-cond-<i> con las mismas guardas de seguridad"
  - "Markdown: _md_cell escapa valores planos y emite [label](href)/![alt](src); _md_table escapa headers (no re-escapa celdas ya finales) para evitar doble-escape de pipes"
  - "Chart degrada a texto (sin gráficos en Markdown); Pivot a tabla GFM filas×columnas"

patterns-established:
  - "Método de conveniencia to_markdown() con import perezoso (mismo patrón que to_csv/to_text/to_excel/to_pdf)"
  - "Tabla GFM: | h1 | h2 | + |---|---| + celdas escapadas (| -> \\|, newline -> espacio)"

requirements-completed: [TMPL-01, TMPL-02, TMPL-03, TMPL-04]

# Metrics
duration: 7min
completed: 2026-09-17
---

# Phase 10 Plan 1: Templates HTML + Markdown Summary

**Modo HTML por clases (sin CSS inline, opt-in), template de documento completo, y `MarkdownRenderer` con `to_markdown()` (tablas GFM, Link→`[label](href)`, Image→`![alt](src)`), preservando las guardas de seguridad CSS/HTML.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-17T05:35:30Z
- **Completed:** 2026-09-17T05:42:00Z
- **Tasks:** 4
- **Files modified:** 5 (1 creado, 4 modificados)

## Accomplishments

- `HtmlRenderer` con modo clases opt-in: `css=True` emite `class="rpt-cond-N"` en las celdas condicionales y un bloque `<style>` con `.rpt-cond-N{…}`, reutilizando `_SAFE_PROP`/`_UNSAFE_VALUE`/`_esc`; el path por defecto (`css=False`) queda byte-idéntico (sigue `style="…"` inline).
- `render_html(template=True)` envuelve la tabla en un documento HTML completo (`<!DOCTYPE html><html><head><meta charset="utf-8"><title>…</title>{style}</head><body class="report">…`), con `title` escapado y el `<style>` dentro de `<head>` cuando `css=True`.
- `MarkdownRenderer` nuevo: grupos → encabezados `#` por profundidad (depth 0 → `##`), detalle → tabla GFM por grupo, totales/KPI → `**label:** value`, footer → texto indentado, chart degrada a texto, pivot → tabla GFM filas×columnas.
- `ReportResult.to_markdown()` (import perezoso) y `MarkdownRenderer` exportado en `__all__`.
- 8 tests nuevos (7 en `test_report_renderers.py`, 1 en `test_security.py`) con suite completa verde: `101 passed, 3 xfailed`.

## Task Commits

Each task was committed atomically:

1. **Task 1: modo clases CSS en HtmlRenderer** - `f4bd9f7` (feat)
2. **Task 2: template de documento + render_html(css/template/title)** - `1e32e57` (feat)
3. **Task 3: MarkdownRenderer + to_markdown + export** - `04b5596` (feat)
4. **Task 4: tests renderers/seguridad** - `4f25eb3` (test)

**Plan metadata:** `(final)` (docs: complete plan)

## Files Created/Modified

- `encino_rpt/renderers/html.py` - `_matched_rules`/`_style_items`/`_css_decls`/`_style_block`; modo clases y wrapper de documento; kwargs `css`/`template`/`title`.
- `encino_rpt/renderers/markdown.py` - `MarkdownRenderer` + helpers `_md_escape`/`_md_cell`/`_md_table`.
- `encino_rpt/models.py` - `render_html(css/template/title)` y `to_markdown()`.
- `encino_rpt/renderers/__init__.py` - exporta `MarkdownRenderer`.
- `tests/test_report_renderers.py` - 7 tests (css mode, template, markdown, link/image, pipe escape).
- `tests/test_security.py` - `test_html_css_mode_injection_mitigated`.

## Decisions Made

- `css`/`template`/`title` son keyword-only con default `False`/`None`: el comportamiento público existente no cambia (opt-in).
- La generación CSS reutiliza exactamente las mismas guardas que el inline (`_SAFE_PROP`, `_UNSAFE_VALUE`, `_esc`), de modo que el bloque `<style>` no introduce superficie de inyección nueva.
- Escapado de Markdown en un solo punto por tipo de celda: `_md_cell` escapa valores planos (y emite links/imágenes nativos), `_md_table` escapa solo los headers para no doble-escapar pipes.
- El wrapper de documento es estructural (string fijo), no un motor de templates: el sandbox `{{token}}` sigue viviendo solo en `template.py` (nunca Jinja2).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Ninguna de bloqueo. La estructura del árbol canónico confirmó que el grupo raíz (depth 0) no lleva header por defecto, por lo que el primer grupo de usuario renderiza como `###` (depth 1); el criterio `"## " in md` de los tests se satisface tanto para el grupo raíz con header (`##`) como para subgrupos.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Templates HTML + Markdown completos para el milestone v1.1; `MarkdownRenderer` es el último renderer seleccionado (LaTeX permanece out-of-scope).
- Sin blockers nuevos. La preocupación preexistente del workflow `Docs` (GitHub Pages `configure-pages@v5`) sigue ajena a esta fase.

---

*Phase: 10-templates-html-markdown*
*Completed: 2026-09-17*

## Self-Check: PASSED

- Created files exist: `encino_rpt/renderers/markdown.py` ✓
- Modified files exist: `encino_rpt/renderers/html.py`, `encino_rpt/models.py`, `encino_rpt/renderers/__init__.py`, `tests/test_report_renderers.py`, `tests/test_security.py` ✓
- Commits exist: `f4bd9f7`, `1e32e57`, `04b5596`, `4f25eb3` ✓
