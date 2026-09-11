# Seguridad

`encino-rpt` está diseñado para procesar datos potencialmente no confiables sin
exponer ejecución de código ni facilitar inyecciones.

## Evaluador de expresiones sin `eval`

Las expresiones (`add_field`, `total(expression=...)`, `chart`/`pivot`) se evalúan
con un parser `ast` y una *whitelist* estricta, **nunca** con `eval`/`exec`:

- Solo literales, operadores aritméticos/comparación, nombres de campo y un
  conjunto fijo de funciones (`IF`, `lower`, `upper`, `concat`, `round`, `abs`,
  `AND`, `OR`, `NOT`, `IN`, `BETWEEN`).
- Sin subíndices, atributos arbitrarios, comprehensions, `import`, `lambda` ni
  acceso a `__`.

```python
>>> evaluate("__import__('os')", {})
ExpressionError: nombre desconocido: '__import__'
```

## Límites anti-DoS en expresiones

Para evitar consumo excesivo de CPU/memoria con entradas no confiables:

- Número máximo de nodos del AST (`_MAX_NODES`).
- Profundidad máxima de anidamiento (`_MAX_DEPTH`).
- Exponente acotado en `**` (`_MAX_POW_EXP`).

## Protección contra inyección de fórmulas (Excel/CSV)

Los renderers de Excel y CSV neutralizan celdas cuyo valor empieza con
`=`, `+`, `-`, `@`, tabulador o retorno de carro, para que Excel/Calc no las
interprete como fórmulas:

- **CSV**: se prefija una comilla simple (`'`).
- **Excel**: se fuerza el tipo de celda a texto (`data_type = "s"`).

Esto aplica a celdas de detalle, encabezados/pies, pivotes, gráficos y KPIs.
Los totales se calculan en Python (no por fórmula), por lo que no se ven
afectados.

## Escapado de salida

- **HTML**: el contenido de datos se escapa con `html.escape`; los nombres de
  propiedad de los estilos condicionales se validan y sus valores se escapan.
- **PDF**: el contenido interpolado en párrafos se escapa antes de insertarse.

## Plantillas

El índice `{{param.N}}` se valida: debe ser numérico y estar en rango; de lo
contrario se lanza un error explícito en lugar de indexar de forma insegura.
