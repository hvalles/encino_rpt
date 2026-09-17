# Phase 10: Templates HTML + Markdown — Context

**Gathered:** 2026-09-17
**Status:** Ready for planning
**Source:** discuss v1.1 (decisión reabierta: Markdown ahora seleccionado)

<domain>
## Phase Boundary

HTML renderiza por clases (sin CSS inline, modo opt-in) y con template de documento completo; nuevo `MarkdownRenderer` + `to_markdown()`. Sin regresión de seguridad (CSS/HTML).
</domain>

<decisions>
## Implementation Decisions

### Modo clases (opt-in)
- `render_html(..., css=False)` — por defecto el comportamiento actual (inline) no cambia.
- Con `css=True`, el formato condicional se emite como clases deterministas `rpt-cond-<i>` (índice de regla en `result.styles`) + un bloque `<style>` con las declaraciones, en vez de `style="…"`.
- Las guardas de seguridad (`_SAFE_PROP`, `_UNSAFE_VALUE`, `_esc`) se reutilizan al generar el CSS.

### Template de documento
- `render_html(..., template=False)`: con `template=True` envuelve la tabla en un documento HTML completo (`<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title|meta.title}</title><style>{css}</style></head><body class="report">{table}</body></html>`). El `title` se escapa.
- `template=True` implica bloque `<style>` (si `css=True`).

### Markdown
- `MarkdownRenderer` + `ReportResult.to_markdown()`.
- Grupos → encabezados `#` por profundidad; totales/KPI → `**label:** value`; footer → texto.
- Detalle → tabla GFM por grupo (buffered), headers de `result.columns`, celdas escapadas (`|`→`\|`, newline→espacio).
- Pivot → tabla GFM (filas×columnas). Chart → degrada a texto (`**title** (kind): label: values`).
- Link → `[label](href)`; Image → `![alt](src)`.
- **Fidelidad documentada**: sin formato condicional ni gráficos (degrada a texto).
</decisions>

<canonical_refs>
## Canonical References

- `encino_rpt/renderers/html.py` — `_style_attr`, `_SAFE_PROP`, `_UNSAFE_VALUE`, `_esc`, `_full_row`.
- `encino_rpt/renderers/text.py` — espejo para el MarkdownRenderer.
- `encino_rpt/renderers/_walk.py` — eventos del traversal.
- `encino_rpt/renderers/csv.py` — `_cell_text` (Link/Image a texto).
- `encino_rpt/models.py` — `ReportResult.to_*` (patrón de método de conveniencia).
- `tests/test_security.py` — guardas de inyección CSS/HTML.
</canonical_refs>

<specifics>
## Specific Ideas

- La generación CSS reutiliza la lógica de `_style_attr` pero emite `prop:value` en un bloque `<style>`, no en un atributo.
- El MarkdownRenderer consume el mismo `walk()`; el buffer de detalle se limpia al salir de cada grupo.
</specifics>

<deferred>
## Deferred Ideas

- Plantillas de documento definidas por el usuario (más allá del wrapper + `<style>`).
- Streaming de salida.
</deferred>

---

*Phase: 10-templates-html-markdown*
*Context gathered: 2026-09-17*
