"""Builder fluido `Report`."""

from __future__ import annotations

from typing import Any

from ._specs import FieldSpec, GroupSpec, KpiSpec
from .models import ConditionalRule, Format, ReportResult
from .section import Section


class Report:
    """Constructor fluido de reportes a partir de filas `list[dict]`.

    Define columnas calculadas, cortes, totales, gráficos, pivotes y KPIs;
    `run()` materializa el árbol canónico (`ReportResult`).
    """

    def __init__(self, rows: list[dict], params: list | None = None, title: str | None = None):
        """Crea un reporte.

        Args:
            rows: Filas de entrada (`list[dict]`).
            params: Parámetros de la consulta, accesibles en plantillas como `{{param.N}}`.
            title: Título del reporte (se copia a `ReportMeta.title` en `run()`).
        """
        self._rows = list(rows)
        self._params = list(params or [])
        self._title = title
        self._functions: dict[str, Any] = {}
        self._aggregates: dict[str, Any] = {}
        self._fields: list[FieldSpec] = []
        self._detail: list[str] = []
        self._groups: dict[str, GroupSpec] = {}
        self._order: list[str] = []          # orden de declaración de los cortes
        self._formats: dict[str, Format] = {}
        self._styles: list[ConditionalRule] = []
        self._datasets: dict[str, list[dict]] = {}
        self._kpis: list[KpiSpec] = []

    # --- funciones / campos ---
    def add_function(self, name: str, fn) -> Report:
        """Registra una función de expresión (por renglón).

        Args:
            name: Nombre invocable desde una expresión.
            fn: Callable invocado con argumentos explícitos, p. ej. `redondear(total)`.

        Returns:
            El propio reporte (fluido).
        """
        self._functions[name] = fn
        return self

    def add_aggregate(self, name: str, fn) -> Report:
        """Registra una función de agregado para `custom:<nombre>`.

        Args:
            name: Nombre del agregado.
            fn: Callable con firma `fn(rows, column) -> value`.

        Returns:
            El propio reporte (fluido).
        """
        self._aggregates[name] = fn
        return self

    def set_format(self, column: str, *, kind: str = "number",
                   decimals: int | None = None, thousands: bool = False,
                   symbol: str | None = None, symbol_position: str = "prefix",
                   negative: str = "minus", percent_scale: bool = False,
                   pattern: str | None = None) -> Report:
        """Registra el formato de presentación de una columna.

        Args:
            column: Nombre de la columna.
            kind: `number`, `currency`, `percent` o `date`.
            decimals: Decimales a mostrar (None = no redondear).
            thousands: Usar separador de miles.
            symbol: Símbolo (p. ej. `"$"`, `"€"`).
            symbol_position: `prefix` o `suffix`.
            negative: `minus` (`-100`) o `paren` (`(100)`).
            percent_scale: En percent, multiplicar por 100 al mostrar.
            pattern: Patrón `strftime` cuando `kind="date"`.

        Returns:
            El propio reporte (fluido).
        """
        self._formats[column] = Format(
            kind=kind, decimals=decimals, thousands=thousands, symbol=symbol,
            symbol_position=symbol_position, negative=negative,
            percent_scale=percent_scale, pattern=pattern,
        )
        return self

    def add_style(self, column: str | None = None, *, when: str = "lt",
                  value: Any = 0, **style) -> Report:
        """Registra una regla de formato condicional por valor.

        Args:
            column: Columna a la que aplica (None = cualquier columna).
            when: Operador: `lt`, `le`, `gt`, `ge`, `eq` o `ne`.
            value: Valor de comparación.
            **style: Estilo a aplicar (p. ej. `color="red"`, `bold=True`).

        Returns:
            El propio reporte (fluido).
        """
        self._styles.append(ConditionalRule(column=column, when=when, value=value, style=style))
        return self

    def add_dataset(self, name: str, rows: list[dict]) -> Report:
        """Registra un conjunto de filas adicional (multi-query).

        Args:
            name: Nombre del conjunto, referenciado con `source=name`.
            rows: Filas del conjunto.

        Returns:
            El propio reporte (fluido).
        """
        self._datasets[name] = list(rows)
        return self

    def kpi(self, label: str, *, operator: str = "sum", column: str | None = None,
            expression: str | None = None, value: Any = None,
            format=None, source: str | None = None) -> Report:
        """Declara una tarjeta de indicador (KPI) en el resumen.

        Args:
            label: Etiqueta de la tarjeta.
            operator: Agregado si no se pasa `value`.
            column: Columna a agregar.
            expression: Expresión por renglón a agregar.
            value: Valor explícito (evita calcularlo).
            format: Formato de presentación.
            source: Conjunto de `add_dataset` sobre el que se calcula.

        Returns:
            El propio reporte (fluido).
        """
        self._kpis.append(KpiSpec(label, operator, column, expression, value, format, source))
        return self

    def add_field(self, name: str, expression: str | None = None, *,
                  after: str | None = None, format=None,
                  cumulative: str | None = None, start: Any = 0,
                  source: str | None = None) -> Report:
        """Declara una columna calculada.

        Args:
            name: Nombre de la columna.
            expression: Expresión evaluada con el evaluador seguro.
            after: Columna visible tras la que insertar (None = campo oculto).
            format: Formato de presentación.
            cumulative: `"sum"` para saldo corrido.
            start: Saldo inicial del acumulador.
            source: Conjunto de `add_dataset`.

        Returns:
            El propio reporte (fluido).
        """
        self._fields.append(
            FieldSpec(name=name, expression=expression, after=after, kind="expr",
                      format=format, cumulative=cumulative, start=start, source=source)
        )
        return self

    def link(self, name: str, target: str, href: str, label: str | None = None,
             *, after: str | None = None) -> Report:
        """Declara una columna de enlace.

        Args:
            name: Nombre de la columna.
            target: `section`, `report`, `page` o `external`.
            href: Plantilla de la URL (admite `{{campo}}`).
            label: Texto del enlace (opcional).
            after: Columna visible tras la que insertar.

        Returns:
            El propio reporte (fluido).
        """
        self._fields.append(
            FieldSpec(name=name, after=after, kind="link", target=target, href=href, label=label)
        )
        return self

    def image(self, name: str, src: str, *, alt: str | None = None,
              width: int | None = None, height: int | None = None,
              after: str | None = None) -> Report:
        """Declara una columna de imagen.

        Args:
            name: Nombre de la columna.
            src: Plantilla de la ruta/URL/data URI (admite `{{campo}}`).
            alt: Texto alternativo.
            width: Ancho en px.
            height: Alto en px.
            after: Columna visible tras la que insertar.

        Returns:
            El propio reporte (fluido).
        """
        self._fields.append(
            FieldSpec(name=name, after=after, kind="image", src=src, alt=alt,
                      width=width, height=height)
        )
        return self

    # --- detalle / grupos ---
    def detail(self, *columns: str, source: str | None = None) -> Report:
        """Define las columnas del detalle, en orden.

        Args:
            *columns: Nombres de columna.
            source: Conjunto de `add_dataset`.

        Returns:
            El propio reporte (fluido).
        """
        self._detail = list(columns)
        return self

    def group(self, name: str,
              columns: str | list[str] | tuple[str, ...] | None = None, *,
              parent: str | None = None,
              show_collapsed: bool = False,
              default_collapsed: bool = False,
              path: str | None = None, separator: str = ".",
              source: str | None = None) -> Section:
        """Crea (o devuelve) un corte.

        Args:
            name: Identificador del corte.
            columns: Columna (`"id"`) o lista (`["tenant_id", "code"]`) para agrupar
                por clave simple o compuesta. `None` = grupo raíz/global.
            parent: Nombre de un corte padre para anidar.
            show_collapsed: Mostrar el encabezado aunque el grupo esté colapsado.
            default_collapsed: Estado inicial (cerrado) para renderers interactivos.
            path: Columna con una jerarquía por datos (p. ej. `"1.2.3"`).
            separator: Separador de la ruta.
            source: Conjunto de `add_dataset`.

        Returns:
            Una `Section` para configurar la presentación del corte.
        """
        if columns is not None and path is not None:
            raise ValueError("`columns` y `path` son excluyentes")
        cols = None
        if columns is not None:
            cols = [columns] if isinstance(columns, str) else list(columns)
        spec = GroupSpec(
            name=name, columns=cols, parent=parent, path=path, separator=separator,
            show_collapsed=show_collapsed, default_collapsed=default_collapsed,
            source=source,
        )
        self._groups[name] = spec
        self._order.append(name)
        return Section(spec)

    def section(self, name: str) -> Section:
        """Devuelve la `Section` de un corte ya declarado.

        Args:
            name: Nombre del corte.

        Returns:
            La `Section` correspondiente.

        Raises:
            KeyError: Si el corte no fue declarado.
        """
        spec = self._groups.get(name)
        if spec is None:
            raise KeyError(f"corte no declarado: {name!r}")
        return Section(spec)

    def run(self) -> ReportResult:
        """Ejecuta el reporte y materializa el árbol canónico.

        Returns:
            El `ReportResult` con columnas, formatos, estilos, KPIs y el árbol de grupos.
        """
        from .aggregation import build

        return build(self)
