---
phase: v1.1-readers-templates
verified: 2026-09-16T23:50:00Z
status: passed
score: 9/9 requirements verified (READ-01..05, TMPL-01..04)
overrides_applied: 0
---

# Milestone v1.1 Verification Report

**Milestone Goal:** Readers multi-formato + Templates HTML/Markdown
**Phases:** 09-readers-multi-formato (READ-01..05) + 10-templates-html-markdown (TMPL-01..04)
**Verified:** 2026-09-16
**Status:** passed
**Re-verification:** No — initial verification (no prior VERIFICATION.md found)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | READ-01: `Reader` protocol + registro `register_reader`/`get_reader` | ✓ VERIFIED | `encino_rpt/readers.py:12-62` — `Reader(Protocol)`, `_READERS`, `register_reader`, `get_reader` (ValueError si no registrado) |
| 2 | READ-02: readers stdlib `csv`/`tsv`/`json`/`jsonl`/`tuples` (`columns=`) | ✓ VERIFIED | `readers.py:153-262` (`_DelimitedReader`, `JsonReader`, `JsonLinesReader`, `TuplesReader`) + registro `readers.py:359-363`; `tests/test_readers.py` (csv path/filelike, tsv, json, jsonl, tuples, tuples-requires-columns) |
| 3 | READ-03: reader `excel` lazy tras extra `excel`, `ImportError` con hint | ✓ VERIFIED | `readers.py:265-299` — `from openpyxl import load_workbook` dentro de `read()`; `ImportError("openpyxl no está instalado; instala el extra \`excel\`")`; lazy confirmado: `import encino_rpt` no deja `openpyxl` en `sys.modules` |
| 4 | READ-04: auto-detección determinista (`int`/`float`/`bool`/`null`/`str`) con opt-out `coerce=False` | ✓ VERIFIED | `_coerce` (`readers.py:65-96`) — `"100"→100`, `"100.5"→100.5`, `"true"→True`, `""→None`, `"N/A"→"N/A"`, no-str intacto; `coerce=False` → todo str (`test_coerce_false`) |
| 5 | READ-05: `Report(rows=...)` / `add_dataset` intactos | ✓ VERIFIED | `Report.__init__` (`report.py:19-21`) sin cambios; `test_report_rows_unchanged` verde |
| 6 | TMPL-01: `render_html(css=True)` emite clases `rpt-cond-N` + `<style>`, sin `style="…"` inline | ✓ VERIFIED | `_matched_rules`/`_cell_attrs`/`_style_block`/`_css_decls` (`html.py:173-239`); reutiliza `_SAFE_PROP`/`_UNSAFE_VALUE`/`_esc`; `test_html_css_mode_no_inline_style` |
| 7 | TMPL-02: `render_html(template=True)` documento completo (`<head>`+`<style>`+`<body class="report">`) | ✓ VERIFIED | `render()` (`html.py:63-74`); `test_html_template_document`, `test_html_template_with_css_style_in_head` (style dentro de `<head>`) |
| 8 | TMPL-03: `MarkdownRenderer` + `to_markdown()` GFM (`\|`/newline, Link→`[label](href)`, Image→`![alt](src)`) | ✓ VERIFIED | `renderers/markdown.py` completo; `ReportResult.to_markdown` (`models.py:208-221`); export en `__all__`; `test_markdown_renderer`/`_link_image`/`_escapes_pipe` |
| 9 | TMPL-04: sin regresión de inyección CSS/HTML; sandbox `{{token}}`, nunca Jinja2 | ✓ VERIFIED | `test_html_css_mode_injection_mitigated` + `test_html_style_value_injection_mitigated` verdes; wrapper estructural (string fijo), `template.py` intacto |

**Score:** 9/9 requirements verified

### Deferred Items

None — streaming de salida (`STRM-01`) está explícitamente diferido en REQUIREMENTS.md y no forma parte del milestone v1.1 alcanzable (marcado "*(diferido)*" en ROADMAP.md).

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `encino_rpt/readers.py` | Protocolo Reader + registro + readers stdlib + excel + `_coerce` | ✓ VERIFIED | 364 líneas, completo |
| `encino_rpt/renderers/html.py` | modo clases (`css=True`) + template de documento | ✓ VERIFIED | 239 líneas |
| `encino_rpt/renderers/markdown.py` | `MarkdownRenderer` + GFM escaping | ✓ VERIFIED | 114 líneas |
| `encino_rpt/report.py` | `Report.read`/`Report.register_reader` | ✓ VERIFIED | `report.py:44-89` |
| `encino_rpt/models.py` | `render_html(css/template/title)` + `to_markdown()` | ✓ VERIFIED | `models.py:150-183, 208-221` |
| `encino_rpt/__init__.py` | exporta `Reader` | ✓ VERIFIED | `__init__.py:18,31` |
| `encino_rpt/renderers/__init__.py` | exporta `MarkdownRenderer` | ✓ VERIFIED | `__init__.py:7,16` |
| `tests/test_readers.py` | tests de readers y auto-detección | ✓ VERIFIED | 15 tests |
| `tests/test_report_renderers.py` | tests css/template/markdown | ✓ VERIFIED | 7 tests nuevos |
| `tests/test_security.py` | regresión CSS en modo clases | ✓ VERIFIED | `test_html_css_mode_injection_mitigated` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `readers.py` | `report.py` | `from .readers import read as read_rows` en `Report.read` | ✓ WIRED | `report.py:74-77` |
| `readers.py` | `report.py` | `register_reader` delegado en `Report.register_reader` | ✓ WIRED | `report.py:87-89` |
| `markdown.py` | `_walk.py` | `from ._walk import walk` | ✓ WIRED | `markdown.py:7,81` |
| `models.py` | `markdown.py` | import perezoso en `to_markdown` | ✓ WIRED | `models.py:219-221` |
| `models.py` | `html.py` | `HtmlRenderer(css=, template=, title=)` en `render_html` | ✓ WIRED | `models.py:177-183` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `html.py` `_style_block` | `result.styles[i].style` | `Report.add_style` → `ConditionalRule` | Sí (declaraciones reales filtradas por `_SAFE_PROP`/`_UNSAFE_VALUE`) | ✓ FLOWING |
| `markdown.py` `_md_table` | `result.columns` / `node.row` | filas del árbol canónico | Sí (celdas reales vía `_md_cell`) | ✓ FLOWING |
| `readers.py` `_DelimitedReader` | `csv.DictReader` sobre `io.StringIO(text)` | `_read_text` (ruta/file-like) | Sí (texto real del source) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| openpyxl lazy (READ-03) | `import encino_rpt; assert 'openpyxl' not in sys.modules` | `openpyxl lazy OK` | ✓ PASS |
| `Reader`/`Report` exportados | `'Reader' in __all__ and 'Report' in __all__` | `True True` | ✓ PASS |
| JSON end-to-end + css/template | `Report.read(json).run()` + `render_html(css=True, template=True)` | assert `<td class="rpt-cond-0">`, `<style>…</style>`, `<!DOCTYPE html>`, style antes de `</head>` | ✓ PASS |

### Probe Execution

No probes declared (`scripts/*/tests/probe-*.sh` no existe; fase de librería, sin probes). SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| READ-01 | Phase 9 | Protocolo `Reader` + registro | ✓ SATISFIED | `readers.py:12-62` |
| READ-02 | Phase 9 | readers stdlib | ✓ SATISFIED | `readers.py:153-262,359-363` |
| READ-03 | Phase 9 | reader excel lazy | ✓ SATISFIED | `readers.py:265-299` |
| READ-04 | Phase 9 | auto-detección + `coerce=False` | ✓ SATISFIED | `readers.py:65-96` |
| READ-05 | Phase 9 | compatibilidad `Report(rows=...)` | ✓ SATISFIED | `report.py:19-21` |
| TMPL-01 | Phase 10 | HTML por clases (css=True) | ✓ SATISFIED | `html.py:173-239` |
| TMPL-02 | Phase 10 | template de documento | ✓ SATISFIED | `html.py:63-74` |
| TMPL-03 | Phase 10 | `MarkdownRenderer` + `to_markdown` | ✓ SATISFIED | `markdown.py` + `models.py:208` |
| TMPL-04 | Phase 10 | sin regresión de inyección | ✓ SATISFIED | `test_security.py:126-133` |

No orphaned requirements: all 9 milestone requirements are claimed by their plans and verified.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | — |

`rg` sobre `TBD|FIXME|XXX|PLACEHOLDER|TODO|return null|return []|return {}` en los archivos modificados → `NO_DEBT_MARKERS`.

### Gates (ejecutados por el verificador)

| Gate | Command | Result |
|------|---------|--------|
| Test suite | `uv run pytest -q` | `101 passed, 3 xfailed` |
| Type check | `uv run mypy encino_rpt` | `Success: no issues found in 22 source files` |
| Lint | `uv run ruff check` | `All checks passed!` |
| Format | `uv run ruff format --check encino_rpt tests` | `27 files already formatted` |

### Human Verification Required

None. El milestone es una librería Python pura; todos los "truths" son verificables programáticamente (strings HTML/Markdown, coerciones, resolución de formatos) y fueron confirmados vía tests + spot-checks. No hay UI visual, servicio externo ni comportamiento en tiempo real.

### Gaps Summary

No gaps. Los 9 requirements del milestone v1.1 (READ-01..05, TMPL-01..04) están implementados, cableados y cubiertos por tests que pasan. Los 4 gates de CI (pytest, mypy, ruff check, ruff format) están verdes, ejecutados por el verificador — no por las SUMMARYs.

---

_Verified: 2026-09-16_
_Verifier: the agent (gsd-verifier)_
