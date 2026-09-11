# encino-rpt

Reporteador financiero sobre `list[dict]`. Convierte filas ya materializadas
(la salida de `fetch_all` / `fetch_many` / `paginate`) en un **árbol canónico**
desacoplado del destino, y lo renderiza a HTML, Excel, CSV, PDF o texto plano.

```python
from encino_rpt import Report

rows = [
    {"agente": "Ana", "monto": 100},
    {"agente": "Ana", "monto": 50},
    {"agente": "Bob", "monto": 200},
]

rep = Report(rows, title="Ventas por agente")
rep.group("por_agente", columns="agente")
rep.section("por_agente").header("Agente {{agente}}")
rep.section("por_agente").total("sum", "monto")
rep.group("global")
rep.section("global").total("sum", "monto")

result = rep.run()
print(result.render_html())
```

## Características

- **Jerarquías de cortes** (grupos anidados por columna simple o compuesta) con
  encabezado, pie y total por nivel.
- **Evaluador de expresiones seguro** (sin `eval`; *whitelist* vía `ast`):
  `cantidad * precio`, `IF(...)`, `upper(...)`, lógica `AND`/`OR`/`NOT`/`IN`/`BETWEEN`.
- **Columnas calculadas** (visibles u ocultas) y **saldos corridos**
  (`cumulative="sum"`).
- **Plantillas** `{{campo}}`, `{{param.N}}` y `{{total.NOMBRE}}` en header/footer.
- **Totales** `sum`/`avg`/`count`/`count_distinct`/`max`/`min`/`custom:<n>`,
  incluyendo totales condicionales y porcentajes entre secciones (`TOTAL(...)`).
- **Celdas enriquecidas**: enlaces (`Link`) e imágenes (`Image`).
- **Gráficos** (`pie`/`bar`/`line`) y **pivotes** (cross-tab filas × columnas).
- **KPIs**, **formato numérico** (moneda, `%`, miles, paréntesis, fechas) y
  **formato condicional**.
- **Multi-query** (`add_dataset` + `source=`) para sub-reportes.
- Salida **renderer-agnóstica**: un único árbol alimenta JSON (`model_dump()`),
  HTML, Excel, CSV, PDF y texto.
- **Mitigaciones de seguridad** integradas: evaluador sin `eval`, anti-DoS en
  expresiones y protección contra inyección de fórmulas en Excel/CSV.

## Instalación

Requiere Python **3.10+**.

```bash
pip install encino-rpt

# extras opcionales
pip install "encino-rpt[excel]"   # render a Excel (openpyxl)
pip install "encino-rpt[pdf]"     # render a PDF (reportlab)
```

## Inicio rápido

```python
from encino_rpt import Report

rows = [
    {"sku": "A1", "cantidad": 2, "precio": 10.0},
    {"sku": "A1", "cantidad": 1, "precio": 5.0},
    {"sku": "B2", "cantidad": 3, "precio": 4.0},
]

rep = Report(rows, params=["2026-01-01", "2026-01-31"], title="Inventario")

rep.add_field("total", "cantidad * precio", after="precio")   # columna calculada
rep.detail("sku", "cantidad", "precio", "total")

rep.group("por_sku", columns="sku")
rep.section("por_sku").header("SKU {{sku}}")
rep.section("por_sku").total("sum", "total")

rep.group("global")
rep.section("global").header("Reporte del {{param.0}} al {{param.1}}")
rep.section("global").total("sum", "total", name="total_gral")

result = rep.run()

result.render_html()      # tabla HTML
result.to_csv()           # CSV
result.to_text()          # texto plano
result.to_excel()         # hoja openpyxl (requiere extra `excel`)
result.to_pdf()           # bytes PDF (requiere extra `pdf`)
result.model_dump()       # JSON canónico
```

## Documentación

| Documento | Contenido |
|-----------|-----------|
| [Getting started](https://hvalles.github.io/encino_rpt/getting-started/) | Instalación y primer reporte en 5 pasos. |
| [Guía de uso](https://hvalles.github.io/encino_rpt/guide/) | Cortes, totales, campos calculados, pivotes, gráficos, KPIs, formatos y más. |
| [Referencia de API](https://hvalles.github.io/encino_rpt/api/) | Documentación de clases y métodos. |
| [Seguridad](https://hvalles.github.io/encino_rpt/security/) | Mitigaciones implementadas. |

## Pruebas

```bash
uv run pytest        # suite completa
uv run ruff check    # linter
```

## Licencia

Distribuido bajo la licencia [MIT](LICENSE). Consulta el archivo `LICENSE`
para el texto íntegro.

## Créditos

Desarrollado con la asistencia de **OpenCode** y el modelo **DeepSeek V4 Pro**.
