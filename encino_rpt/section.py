"""Fachada pública `Section`: muta la `GroupSpec` de un corte."""

from __future__ import annotations

from ._specs import ChartSpec, GroupSpec, PivotSpec, TotalSpec


class Section:
    """Acceso fluido a las piezas de presentación de un corte (header/footer/total/chart/pivot/...)."""

    def __init__(self, spec: GroupSpec):
        self._spec = spec

    def header(self, template: str) -> Section:
        """Fija el encabezado del corte.

        Args:
            template: Plantilla `{{campo}}`/`{{param.N}}`/`{{total.NOMBRE}}`.

        Returns:
            La propia sección (fluido).
        """
        self._spec.header = template
        return self

    def footer(self, template: str, column_position: str | None = None) -> Section:
        """Fija el pie del corte.

        Args:
            template: Plantilla `{{campo}}`/`{{param.N}}`/`{{total.NOMBRE}}`.
            column_position: Pista de presentación (columna bajo la que alinear).

        Returns:
            La propia sección (fluido).
        """
        self._spec.footer = template
        self._spec.footer_column_position = column_position
        return self

    def total(self, operator: str, column: str | None = None, *,
              expression: str | None = None, name: str | None = None,
              label: str | None = None, column_position: str | None = None,
              format=None) -> Section:
        """Añade un total al corte.

        Args:
            operator: `sum`, `avg`, `count`, `count_distinct`, `max`, `min` o
                `custom:<nombre>`.
            column: Columna a agregar.
            expression: Expresión por renglón a agregar (habilita totales
                condicionales y `TOTAL("seccion.nombre")`).
            name: Nombre para referenciarlo como `{{total.NOMBRE}}`.
            label: Etiqueta del total.
            column_position: Pista de presentación (columna bajo la que alinear).
            format: Formato de presentación.

        Returns:
            La propia sección (fluido).
        """
        self._spec.totals.append(
            TotalSpec(operator, column, expression, name, label, format, column_position)
        )
        return self

    def chart(self, kind: str, *, title: str | None = None,
              operator: str = "sum", column: str | None = None,
              expression: str | None = None, label_field: str | None = None,
              options: dict | None = None, source: str | None = None) -> Section:
        """Declara un gráfico dentro del corte.

        Args:
            kind: `pie`, `bar` o `line`.
            title: Título del gráfico.
            operator: Agregado sobre `column`/`expression`.
            column: Columna a agregar.
            expression: Expresión por renglón a agregar.
            label_field: Campo para etiquetar los subgrupos (None = primera
                columna de agrupación).
            options: Pistas de estilo opcionales.
            source: Conjunto de `add_dataset`.

        Returns:
            La propia sección (fluido).
        """
        self._spec.charts.append(
            ChartSpec(kind, title, operator, column, expression, label_field, options, source)
        )
        return self

    def pivot(self, row_column: str, column_column: str, *,
              operator: str = "sum", value_column: str | None = None,
              value_expression: str | None = None, title: str | None = None,
              show_totals: bool = True, options: dict | None = None,
              source: str | None = None) -> Section:
        """Declara una matriz de doble entrada (cross-tab).

        Args:
            row_column: Columna de la dimensión fila.
            column_column: Columna de la dimensión columna.
            operator: Agregado sobre `value_column`/`value_expression`.
            value_column: Columna a agregar.
            value_expression: Expresión por renglón a agregar.
            title: Título del pivote.
            show_totals: Añadir totales de fila/columna.
            options: Pistas de estilo opcionales.
            source: Conjunto de `add_dataset`.

        Returns:
            La propia sección (fluido).
        """
        self._spec.pivots.append(
            PivotSpec(row_column, column_column, operator, value_column,
                      value_expression, title, show_totals, options, source)
        )
        return self

    def order_by(self, column: str | None = None, *, direction: str = "asc",
                 total: str | None = None, expression: str | None = None) -> Section:
        """Ordena los hijos del corte.

        Args:
            column: Columna por la que ordenar.
            direction: `asc` o `desc`.
            total: Nombre de un total por el que ordenar.
            expression: Expresión por la que ordenar.

        Returns:
            La propia sección (fluido).
        """
        if direction.lower() not in ("asc", "desc"):
            raise ValueError(f"dirección de orden inválida: {direction!r}")
        self._spec.order_by = {
            "column": column,
            "direction": direction.lower(),
            "total": total,
            "expression": expression,
        }
        return self

    def top(self, n: int) -> Section:
        """Conserva solo los primeros `n` hijos.

        Args:
            n: Número de hijos a conservar.

        Returns:
            La propia sección (fluido).
        """
        self._spec.top_n = n
        return self

    def suppress_zero(self, column: str | None = None, total: str | None = None) -> Section:
        """Descarta los hijos con valor cero/None.

        Args:
            column: Columna a comprobar.
            total: Nombre de un total a comprobar.

        Returns:
            La propia sección (fluido).
        """
        self._spec.suppress_zero = {"column": column, "total": total}
        return self

    def page_break(self, enabled: bool = True) -> Section:
        """Marca el corte para iniciar en página nueva.

        Args:
            enabled: Activar/desactivar el salto de página.

        Returns:
            La propia sección (fluido).
        """
        self._spec.page_break = enabled
        return self
