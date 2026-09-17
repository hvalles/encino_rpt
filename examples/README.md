# Ejemplos de encino-rpt

Ejemplos autocontenidos que demuestran las capacidades del reporteador. Los datos
de muestra viven en `data/` (CSV y JSON) y las salidas se escriben en `output/`
(gitignored).

## Cómo ejecutar

```bash
uv run python examples/01_tabla_basica.py
```

Los ejemplos de Excel/PDF requieren los extras:

```bash
pip install "encino-rpt[excel]" "encino-rpt[pdf]"   # o `uv sync --all-extras`
```

Sin los extras, `save()` omite `.xlsx`/`.pdf` y genera el resto.

## Datos de muestra

| Archivo | Contenido |
|---------|-----------|
| `data/ventas.csv` | Transacciones de ventas (fecha, agente, región, cuenta, sku, producto, cantidad, precio, descuento). |
| `data/presupuesto.json` | Presupuesto por agente (dataset secundario para multi-dataset). |

## Índice

| # | Ejemplo | Demuestra |
|---|---------|-----------|
| 01 | [tabla_basica](01_tabla_basica.py) | Lectura de CSV (`Report.read`) y detalle plano. |
| 02 | [grupos_totales](02_grupos_totales.py) | Cortes anidados (`parent=`), encabezado/pie y totales por nivel. |
| 03 | [campos_calculados](03_campos_calculados.py) | Columnas calculadas (`add_field`) y saldo corrido (`cumulative`). |
| 04 | [totales_condicionales](04_totales_condicionales.py) | Totales condicionales y `%` sobre el total general (`TOTAL(...)`). |
| 05 | [formato_estilos](05_formato_estilos.py) | Formato numérico (moneda/%/miles/fecha) y formato condicional. |
| 06 | [graficos](06_graficos.py) | Gráficos `pie`/`bar`/`line`. |
| 07 | [pivote](07_pivote.py) | Pivote cross-tab (filas × columnas) con totales. |
| 08 | [kpis](08_kpis.py) | Tarjetas KPI (`count`/`sum`/`avg`/`count_distinct`). |
| 09 | [enlaces_imagenes](09_enlaces_imagenes.py) | Celdas enriquecidas: `link` e `image`. |
| 10 | [multi_dataset](10_multi_dataset.py) | Multi-dataset (`add_dataset` + `source=`). |
| 11 | [reader_json](11_reader_json.py) | Readers: formato por extensión, auto-detección de tipos y `coerce=False`. |
| 12 | [markdown_streaming](12_markdown_streaming.py) | Salida Markdown y streaming (`iter_*` / `file=`). |
| 13 | [jerarquia_path](13_jerarquia_path.py) | Jerarquía por ruta (`path=`): cuentas contables. |

## Salidas

Cada ejemplo guarda, en `output/`, el resultado en HTML, CSV y Markdown — y en
Excel (`.xlsx`) y PDF si los extras están instalados.
