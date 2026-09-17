---
phase: 10-templates-html-markdown
reviewed: 2026-09-16T00:00:00Z
status: issues
critical: 0
major: 2
minor: 6
info: 4
---

# Code Review — v1.1 (Phase 9 readers + Phase 10 templates/markdown)

**Rango:** `888a795`..`d55e93e`
**Archivos revisados:** `encino_rpt/readers.py`, `encino_rpt/renderers/html.py`, `encino_rpt/renderers/markdown.py`, `encino_rpt/models.py`, `encino_rpt/report.py`, `encino_rpt/__init__.py`, `encino_rpt/renderers/__init__.py`, `tests/test_readers.py`, `tests/test_report_renderers.py`, `tests/test_security.py`

**Verificación ejecutada:** `pytest -q` → 101 passed / 3 xfailed; `ruff check encino_rpt` → limpio; `mypy encino_rpt` → limpio. Los defectos abajo son *correctness/fidelity*, no de lint/tipado.

---

## Verificaciones clave (sin hallazgos)

- **Path por defecto byte-idéntico (HTML):** el refactor de `_style_attr`→`_style_items`/`_matched_rules` es comportamiento-equivalente; `render_html()` sin `css` conserva `style="color:red"` y no emite `<style>` (cubierto por `test_html_css_mode_default_unchanged`).
- **Guardas de inyección CSS preservadas:** `_SAFE_PROP`/`_UNSAFE_VALUE`/`_esc` se reutilizan en `_style_items`, por lo que `css=True` filtra `background="red;position:fixed"` (cubierto por `test_html_css_mode_injection_mitigated`).
- **Nombres de clase deterministas:** `rpt-cond-{i}` con `i` = índice en `result.styles`, alineado entre `_matched_rules` y `_style_block`.
- **Import perezoso de openpyxl:** `ExcelReader.read` importa `load_workbook` dentro de la función; importar `encino_rpt` no carga openpyxl.
- **API pública intacta:** `Report(rows=...)`, `add_dataset`, `render_html()` (sin args) y todos los `to_*` siguen funcionando; `css`/`template`/`title` son keyword-only.

---

## Major

### MAJ-01: `_coerce` convierte `"nan"`/`"inf"`/`"infinity"` a float no-finito y `"1_000"` a `1000` (coerción silenciosa)

**File:** `encino_rpt/readers.py:88-95`
**Issue:** `int(s)` acepta separadores `_` (Python 3.6+) y `float(s)` acepta `nan`/`inf`/`-inf`/`infinity` (case-insensitive). Una celda de texto legítima `"nan"`, `"inf"` o `"1_000"` (p. ej. un código de producto o un placeholder) se convierte silenciosamente a `float('nan')`, `float('inf')` o `1000`. Un `NaN` en una columna numérica hace que los agregados `sum`/`avg` devuelvan `NaN` sin error — corrupción silenciosa de totales, exactamente lo que el diseño (`'N/A' -> 'N/A'` en el plan) intenta evitar. Verificado: `_coerce('nan') == nan`, `_coerce('inf') == inf`, `_coerce('1_000') == 1000`.
**Fix:** Validar finitud/forma antes de devolver float, y no aceptar `_` en ints:
```python
try:
    return int(s)
except ValueError:
    pass
try:
    f = float(s)
except ValueError:
    return value
if not math.isfinite(f) or "_" in s or "inf" in low or "nan" in low:
    return value
return f
```
(Alternativa equivalente: listar `low in ("nan","inf","+inf","-inf","infinity","-infinity")` y devolver `value`.)

### MAJ-02: Links/Images en Markdown no escapan `|`, `)` ni saltos de línea (rompen tablas GFM y enlaces)

**File:** `encino_rpt/renderers/markdown.py:15-21`
**Issue:** `_md_cell` emite `[{label}]({href})` y `![{alt}]({src})` sin aplicar `_md_escape`. Un `label` con `|` (p. ej. `"Q1 | Q2"`) rompe la alineación de columnas de la tabla GFM, y un `href`/`src` con `)` o `]` cierra el enlace antes de tiempo. Verificado: `href='/x)foo', label='a|b'` produce `[a|b](/x)foo)` (tabla + enlace corruptos). `_md_escape` sólo se aplica a la rama de texto plano, no a Link/Image — el `threat_model` T-TP-02 no cubre este caso.
**Fix:** Escapar los componentes:
```python
if isinstance(value, Link):
    label = value.label or value.href
    return f"[{_md_escape(label)}]({_md_escape(value.href)})"
if isinstance(value, Image):
    return f"![{_md_escape(value.alt or '')}]({_md_escape(value.src)})"
```
(Nota: `_md_escape` también debería reemplazar `)`/`]` para evitar cierre prematuro del enlace en label/alt.)

---

## Minor

### MIN-01: CSV/TSV tratan `str` siempre como ruta; JSON/JSONL usan "ruta si existe, si no cruda" — inconsistencia y error confuso

**File:** `encino_rpt/readers.py:99-150, 174`
**Issue:** `_DelimitedReader.read` llama `_read_text(source, str_is_path=True)`, así que `read('a,b\n1,2', format='csv')` intenta abrir un archivo y falla con `OSError` (verificado), mientras `read('[{"a":1}]', format='json')` sí funciona como crudo. Además `_read_text_auto` (JSON/JSONL) enmascara rutas inexistentes: `read('missing.json')` devuelve `JSONDecodeError` en vez de `FileNotFoundError` (verificado), porque "no existe" se interpreta como "string crudo".
**Fix:** Unificar: o bien `_DelimitedReader` usa `_read_text_auto`, o bien `_read_text_auto` distingue "parece JSON" vs "parece ruta" (p. ej. si el `str` empieza con `{`/`[` o contiene `\n` → crudo; si no existe como ruta → `FileNotFoundError`). Documentar explícitamente qué `str` se trata como ruta.

### MIN-02: `ExcelReader` ignora `coerce` y `columns` (contrato inconsistente)

**File:** `encino_rpt/readers.py:268-299`
**Issue:** `read()` siempre reenvía `coerce=coerce, columns=columns` a todo reader, pero `ExcelReader.read(self, source, **opts)` los descarta. `read('x.xlsx', coerce=False)` devuelve los tipos nativos de openpyxl (int/float/datetime), NO todo-`str` como promete el contrato de `coerce=False` en CSV/TSV. No hay test para `coerce=False` con Excel. Tampoco aplica `_coerce` (aceptable si se respeta el tipo nativo, pero debe documentarse que `coerce` no aplica a Excel).
**Fix:** Documentar en el docstring que Excel devuelve tipos nativos de openpyxl (o aplicar `_coerce` cuando `coerce=True` y normalizar a `str` cuando `coerce=False`). Añadir test.

### MIN-03: `wb` de openpyxl no se cierra (resource leak menor)

**File:** `encino_rpt/readers.py:290-299`
**Issue:** `wb = load_workbook(source)` nunca se cierra con `wb.close()`. Para entrada por ruta openpyxl libera el zip tras cargar, pero el workbook mantiene estructuras en memoria y, con file-like, el puntero queda al final sin liberar explícitamente.
**Fix:** Envolver en `try/finally` con `wb.close()`, o leer `ws` y cerrar antes de `return`.

### MIN-04: No se elimina BOM UTF-8 en CSV/TSV (primer header con `\ufeff`)

**File:** `encino_rpt/readers.py:113, 116, 139, 143`
**Issue:** `Path.read_text(encoding="utf-8")` no descarta BOM. Un CSV exportado por Excel (`utf-8` con BOM) produce una primera columna `"\ufeffnombre"` en lugar de `"nombre"`, y `json.loads` falla ante un JSON con BOM.
**Fix:** Usar `encoding="utf-8-sig"` en `_read_text`/`_read_text_auto`.

### MIN-05: Clase `rpt-cond-N` colgante cuando todas las declaraciones de una regla se filtran

**File:** `encino_rpt/renderers/html.py:173-178, 231-239`
**Issue:** Si una regla matchea pero su `style` queda sin declaraciones seguras (p. ej. `background="red;position:fixed"`), `_style_block` omite `.rpt-cond-N{...}` pero `_cell_attrs` igualmente emite `class="rpt-cond-0"`. Verificado: `render_html(css=True)` con ese estilo produce `<td class="rpt-cond-0">` sin bloque `<style>` correspondiente. Cosmético (la guarda de seguridad sí funciona), pero deja una clase sin definición.
**Fix:** En `_cell_attrs` (modo css) filtrar los índices matcheados cuyos `_css_decls(result.styles[i].style)` son vacíos antes de construir la clase.

### MIN-06: `TuplesReader` trunca silenciosamente filas de largo dispar

**File:** `encino_rpt/readers.py:246-262`
**Issue:** `dict(zip(columns, row))` descarta valores sobrantes si `len(row) > len(columns)` y omite columnas si es menor, sin validación ni error. Pérdida silenciosa de datos ante tuplas malformadas.
**Fix:** Validar `len(row) == len(columns)` y lanzar `ValueError` con detalle en caso contrario.

---

## Info

### INFO-01: Duplicación `_read_text` vs `_read_text_auto`

**File:** `encino_rpt/readers.py:99-150`
**Issue:** Dos helpers casi idénticos que sólo difieren en la rama `str`. El plan pedía un único `_to_text`. Refactor a un único helper con flag explícito (`str_is_path` / `allow_raw`).

### INFO-02: `format` sombrea el builtin `format()`

**File:** `encino_rpt/readers.py:312, 335` y `encino_rpt/report.py:47`
**Issue:** El parámetro `format` sombrea el builtin. Ruff por defecto no lo marca (A002), pero es un footgun de legibilidad. Considerar `fmt` como nombre.

### INFO-03: `read()` reenvía `coerce`/`columns` a todo reader, incluso a los que no los usan

**File:** `encino_rpt/readers.py:354-355`
**Issue:** `get_reader(name).read(source, coerce=coerce, columns=columns, **opts)` fuerza a los readers custom a aceptar `**opts`. Un reader con firma estricta `read(self, source)` rompería con `TypeError`. El `Protocol` exige `**opts`, así que es un contrato blando, pero conviene documentarlo o pasar sólo los kwargs relevantes por formato.

### INFO-04: KPI label / encabezados de grupo / footer no escapan `|` ni newline en Markdown

**File:** `encino_rpt/renderers/markdown.py:52-54, 84-85, 96-98`
**Issue:** `**{label}:**`, `## {header}` y `{footer}` se emiten sin `_md_escape`. Un header/footer con `\n` (posible vía templates con datos de usuario) rompe el heading/la línea. No es tabla, así que `|` es inofensivo, pero el salto de línea sí. Baja prioridad (el plan sólo exigió escapar celdas de tabla).

---

## Resumen

La implementación cumple los objetivos centrales (readers multi-formato, `css=True` sin regresión de seguridad, template de documento, `to_markdown`) y la suite completa pasa (101 passed / 3 xfailed) con lint y mypy limpios. Los hallazgos relevantes son de **correctness silenciosa** — `_coerce` convirtiendo `nan`/`inf`/`1_000` a tipos numéricos (riesgo de totales corruptos) y el escape incompleto de Link/Image en Markdown — más un conjunto de inconsistencias de contrato en los readers (CSV-vs-JSON para `str` crudo, `coerce` ignorado en Excel, BOM, cierre de workbook).
