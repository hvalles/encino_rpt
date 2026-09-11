# encino-rpt

Reporteador financiero sobre `list[dict]`. Convierte filas ya materializadas
(la salida de `fetch_all` / `fetch_many` / `paginate`) en un **árbol canónico**
desacoplado del destino, y lo renderiza a HTML, Excel, CSV, PDF o texto plano.

## Por qué encino-rpt

Los ORM ya resuelven agregados planos en SQL (`GROUP BY`, `SUM`, `AVG`, ...). El
reporteador aporta lo que SQL no expresa limpiamente entre motores:

- **Jerarquías de cortes** (grupos anidados) con encabezado, pie y total por nivel.
- Columnas calculadas con un **evaluador seguro** (sin `eval`).
- Salida **tipada y serializable** (`ReportResult`), lista para un frontend o para
  exportar a distintos formatos.

## Modelo mental

```
list[dict]  ──►  Builder (Report)  ──►  Árbol canónico (ReportResult)  ──►  Renderers
 (entrada)      enriquecer/agrupar        dato puro (JSON)                HTML/Excel/CSV/PDF/Texto
```

1. **Entrada**: filas `list[dict]` + parámetros de la consulta (`params`).
2. **`Report`**: builder fluido que define columnas calculadas, detalle, grupos,
   secciones, totales, enlaces, imágenes, gráficos, pivotes y KPIs.
3. **`ReportResult`**: árbol de datos canónico; `run()` lo materializa.
4. **Renderers**: clases *visitor* que convierten el árbol al formato destino.

## Referencias

- [Getting started](getting-started.md) — primer reporte en 5 pasos.
- [Guía de uso](guide.md) — cortes, totales, campos, pivotes, gráficos, KPIs, formatos.
- [Referencia de API](api.md) — clases y métodos.
- [Seguridad](security.md) — mitigaciones implementadas.
