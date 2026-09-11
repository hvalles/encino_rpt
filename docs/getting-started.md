# Getting started

## Instalación

Requiere Python **3.10+**.

```bash
pip install encino-rpt

# extras opcionales
pip install "encino-rpt[excel]"   # render a Excel (openpyxl)
pip install "encino-rpt[pdf]"     # render a PDF (reportlab)
```

## Primer reporte en 5 pasos

Partimos de una lista de diccionarios:

```python
from encino_rpt import Report

rows = [
    {"agente": "Ana", "monto": 100},
    {"agente": "Ana", "monto": 50},
    {"agente": "Bob", "monto": 200},
]
```

### 1. Crear el reporte

```python
rep = Report(rows, title="Ventas por agente")
```

### 2. Declarar el detalle

```python
rep.detail("agente", "monto")
```

### 3. Agrupar y añadir totales

```python
rep.group("por_agente", columns="agente")
rep.section("por_agente").header("Agente {{agente}}")
rep.section("por_agente").total("sum", "monto")

rep.group("global")
rep.section("global").total("sum", "monto")
```

### 4. Ejecutar

```python
result = rep.run()
```

### 5. Renderizar

```python
print(result.render_html())   # tabla HTML
print(result.to_csv())        # CSV
print(result.to_text())       # texto plano
result.to_excel()             # hoja openpyxl (extra `excel`)
result.to_pdf()               # bytes PDF (extra `pdf`)
result.model_dump()           # JSON canónico
```

## Siguiente paso

Consulta la [guía de uso](guide.md) para cortes anidados, columnas calculadas,
totales condicionales, pivotes, gráficos, KPIs y formato numérico.
