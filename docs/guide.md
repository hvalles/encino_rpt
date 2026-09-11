# Guía de uso

## Columnas calculadas (`add_field`)

```python
rep.add_field("total", "cantidad * precio", after="precio")   # visible, tras "precio"
rep.add_field("es_par", "IF(pedido_id % 2 == 0)")             # oculto (after=None): 1|0
```

- `after=None` (por defecto): campo **oculto** — se calcula y queda disponible para
  expresiones/totales, pero no se imprime.
- `after="col"`: campo **visible**, insertado tras `col`.
- Un campo comparativo se declara como expresión que devuelve `1|0`
  (p. ej. `IF(pedido_id % 2 == 0)`); sirve de factor en totales condicionales.

### Saldo corrido (`cumulative`)

```python
rep.add_field("saldo", "debe - haber", cumulative="sum", start=0, after="haber")
```

El valor de la expresión se acumula sobre los renglones en el orden final;
`start` es el saldo inicial (apertura, por defecto `0`).

## Cortes y totales (`group` / `section`)

```python
rep.group("tot_agt", columns="id")            # corte por una columna
rep.group("tot_memb", columns=["tenant_id", "code"])  # clave compuesta
rep.group("global")                           # grupo raíz (columns=None)
```

Accede a la presentación de un corte con `section(name)`:

```python
s = rep.section("tot_agt")
s.header("{{id}} Agente: {{agente}}")
s.footer("Total agente {{agente}}")
s.total("sum", "total")
s.total("avg", "precio", label="Precio Promedio")
s.total("count", "pedido_id")
```

Operadores de `total`: `sum`, `avg`, `count`, `count_distinct`, `max`, `min`,
`custom:<nombre>` (función registrada con `add_aggregate`).

### Totales condicionales y porcentajes

```python
rep.section("tot_agt").total("sum", expression="es_par * total", label="Total (pares)")
```

`expression` evalúa la expresión por renglón y agrega los resultados.

Para porcentajes/razones entre secciones, usa `TOTAL("seccion.nombre")`:

```python
rep.section("global").total("sum", "total", name="total_gral")
rep.section("tot_agt").total(
    "sum", expression="total / TOTAL('global.total_gral') * 100",
    label="% del total", format={"kind": "percent", "decimals": 2},
)
```

El `name` de un total permite referenciarlo en plantillas como
`{{total.NOMBRE}}` y `{{total.SECCION.NOMBRE}}`.

## Plantillas

Sintaxis `{{token}}` en `header`/`footer`:

- `{{campo}}` → campo del renglón (o del `key` del grupo).
- `{{param.N}}` → `params[N]` de la consulta.
- `{{total.NOMBRE}}` → total nombrado del mismo corte.
- `{{total.SECCION.NOMBRE}}` → total de otra sección.

```python
rep = Report(rows, params=["2026-01-01", "2026-01-31"], title="Ventas")
rep.section("global").header("Reporte del {{param.0}} al {{param.1}}")
```

## Jerarquía por datos (`path`)

Agrupa por una jerarquía de profundidad variable (p. ej. catálogo de cuentas):

```python
rep.group("cuentas", path="cuenta_path", separator=".")
rep.section("cuentas").total("sum", "monto")
```

`columns` y `path` son excluyentes.

## Pivotes (`pivot`)

```python
rep.section("global").pivot(
    "agente", "mes", operator="sum", value_column="total",
    title="Ventas por agente/mes",
)
```

Produce un nodo `Pivot` (filas × columnas → celdas) con totales de fila/columna
si `show_totals=True`.

## Gráficos (`chart`)

```python
rep.section("global").chart(
    "pie", title="Ventas por agente",
    operator="sum", column="total", label_field="agente",
)
```

`kind` admite `pie`, `bar` y `line`. Con hijos grafica los subgrupos; sin hijos,
grafica los `totals` del corte.

## KPIs (`kpi`)

```python
rep.kpi("Ingresos totales", operator="sum", column="total",
        format={"kind": "currency", "symbol": "$", "decimals": 2})
rep.kpi("Ticket promedio", operator="avg", column="total")
```

Si no se pasa `value`, se calcula `operator(column|expression)` sobre las filas.

## Formato numérico (`set_format`)

```python
rep.set_format("total", kind="currency", symbol="$", decimals=2,
               thousands=True, negative="paren")
rep.set_format("fecha", kind="date", pattern="%d/%m/%Y")
```

`kind`: `number`, `currency`, `percent`, `date`. Los renderers lo aplican sin
alterar el valor crudo del árbol.

## Formato condicional (`add_style`)

```python
rep.add_style("total", when="lt", value=0, color="red", bold=True)
```

`when`: `lt`, `le`, `gt`, `ge`, `eq`, `ne`. Las reglas se guardan en
`ReportResult.styles` y las aplican HTML/Excel.

## Orden, Top-N y supresión de ceros

```python
rep.section("tot_agt").order_by(total="total_agt", direction="desc").top(10)
rep.section("tot_agt").suppress_zero(total="total_agt")
```

## Enlaces e imágenes

```python
rep.link("ver", "report", href="/pedido/{{id}}", label="Ver", after="id")
rep.image("foto", src="/media/{{sku}}.png", after="sku")
```

`target` de enlace: `section`, `report`, `page`, `external`.

## Multi-query (`add_dataset`)

```python
rep.add_dataset("presupuesto", presupuesto_rows)
rep.section("global").chart("bar", title="Real vs presupuesto",
                            operator="sum", column="monto", source="presupuesto")
```

`source` está disponible en `group`, `chart`, `pivot`, `add_field`, `detail`.

## Funciones personalizadas

```python
rep.add_function("redondear", lambda x: round(x, 2))     # expresión por renglón
rep.add_aggregate("mediana", median)                      # custom:<n>: fn(rows, column)
rep.section("global").total("custom:mediana", "monto")
```

## Renderers

El `ReportResult` expone métodos de conveniencia que delegan en los renderers:

| Método | Salida | Extra requerido |
|--------|--------|-----------------|
| `render_html(classes=None, repeat_header=False)` | `str` HTML | — |
| `to_csv(delimiter=",")` | `str` CSV | — |
| `to_text()` | `str` texto plano | — |
| `to_excel(ws=None, styles=None, formulas=False)` | hoja openpyxl | `excel` |
| `to_pdf(repeat_header=True, **opts)` | `bytes` PDF | `pdf` |
| `model_dump()` | JSON canónico | — |

`to_excel(formulas=True)` emite `=SUM(...)` para totales `sum` en lugar del valor.
