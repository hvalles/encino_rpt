"""Modelo de datos canónico del reporte (pydantic, serializable a JSON)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, PrivateAttr


class Link(BaseModel):
    """Enlace a otra sección, reporte, página o URL externa."""

    type: Literal["link"] = "link"
    target: Literal["section", "report", "page", "external"]
    href: str
    label: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class Image(BaseModel):
    """Imagen por ruta, URL o data URI."""

    type: Literal["image"] = "image"
    src: str
    alt: str | None = None
    width: int | None = None
    height: int | None = None


class Format(BaseModel):
    """Formato de presentación de una columna o total (lo aplican los renderers)."""

    kind: Literal["number", "currency", "percent", "date"] = "number"
    decimals: int | None = None  # None -> no redondea
    thousands: bool = False  # separador de miles
    symbol: str | None = None  # p. ej. "$", "€"
    symbol_position: Literal["prefix", "suffix"] = "prefix"
    negative: Literal["minus", "paren"] = "minus"
    percent_scale: bool = False  # percent: multiplica por 100 al mostrar
    pattern: str | None = None  # kind="date": patrón strftime


class Total(BaseModel):
    """Total de un corte (resultado ya calculado)."""

    operator: str
    column: str | None = None
    expression: str | None = None
    name: str | None = None
    label: str | None = None
    value: Any = None
    format: Format | None = None
    column_position: str | None = None


class Detail(BaseModel):
    """Renglón del detalle."""

    type: Literal["detail"] = "detail"
    row: dict[str, Any]


class Series(BaseModel):
    """Serie de un gráfico (una línea/barra/sector)."""

    label: str | None = None
    values: list[Any] = Field(default_factory=list)


class Chart(BaseModel):
    type: Literal["chart"] = "chart"
    kind: Literal["pie", "bar", "line"]
    title: str | None = None
    labels: list[Any] = Field(default_factory=list)
    series: list[Series] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)


class Pivot(BaseModel):
    """Matriz de doble entrada (cross-tab): filas x columnas."""

    type: Literal["pivot"] = "pivot"
    title: str | None = None
    rows: list[Any] = Field(default_factory=list)
    columns: list[Any] = Field(default_factory=list)
    cells: list[list[Any]] = Field(default_factory=list)
    row_totals: list[Any] = Field(default_factory=list)
    column_totals: list[Any] = Field(default_factory=list)
    options: dict[str, Any] = Field(default_factory=dict)


class ConditionalRule(BaseModel):
    """Regla de formato condicional por valor (la aplican los renderers)."""

    column: str | None = None
    when: Literal["lt", "le", "gt", "ge", "eq", "ne"] = "lt"
    value: Any = 0
    style: dict[str, Any] = Field(default_factory=dict)


class Kpi(BaseModel):
    """Tarjeta de indicador (métrica escalar)."""

    type: Literal["kpi"] = "kpi"
    label: str | None = None
    value: Any = None
    format: Format | None = None
    options: dict[str, Any] = Field(default_factory=dict)


class Group(BaseModel):
    type: Literal["group"] = "group"
    name: str
    key: dict[str, Any] | None = None
    header: str | None = None
    footer: str | None = None
    show_collapsed: bool = False
    default_collapsed: bool = False
    page_break: bool = False
    totals: list[Total] = Field(default_factory=list)
    children: list[Detail | Group | Chart | Pivot] = Field(default_factory=list)

    # Contexto interno (no serializado) para renderizar header/footer en la fase final.
    _first_row: dict = PrivateAttr(default_factory=dict)
    _header_tpl: str | None = PrivateAttr(default=None)
    _footer_tpl: str | None = PrivateAttr(default=None)


class ReportMeta(BaseModel):
    """Metadatos del reporte (título y parámetros de la consulta)."""

    title: str | None = None
    params: list[Any] = Field(default_factory=list)


class ReportResult(BaseModel):
    """Árbol canónico del reporte (dato puro, serializable a JSON).

    Expone métodos de conveniencia (`render_html`, `to_csv`, `to_text`,
    `to_excel`, `to_pdf`) que delegan en los renderers sin modificar el árbol.
    """

    meta: ReportMeta = Field(default_factory=ReportMeta)
    columns: list[str] = Field(default_factory=list)
    formats: dict[str, Format] = Field(default_factory=dict)
    styles: list[ConditionalRule] = Field(default_factory=list)
    kpis: list[Kpi] = Field(default_factory=list)
    root: Group

    def render_html(
        self,
        classes: dict | None = None,
        repeat_header: bool = False,
        *,
        css: bool = False,
        template: bool = False,
        title: str | None = None,
    ) -> str:
        """Renderiza el reporte a una tabla HTML (o documento completo).

        Args:
            classes: Mapa de clases CSS por tipo de fila (`group`, `total`, ...).
            repeat_header: Repetir el encabezado de columnas por grupo.
            css: Emitir el formato condicional como clases `rpt-cond-N` + bloque
                `<style>` en vez de estilos `style="..."` inline (opt-in; el
                comportamiento por defecto no cambia).
            template: Envolver la tabla en un documento HTML completo
                (`<!DOCTYPE html>`, `<head>`, `<body class="report">`). El bloque
                `<style>` (si `css`) va dentro de `<head>`.
            title: Título del documento (`<title>`); por defecto usa `meta.title`.

        Returns:
            El HTML como cadena.
        """
        from .renderers.html import HtmlRenderer

        return HtmlRenderer(
            classes=classes,
            repeat_header=repeat_header,
            css=css,
            template=template,
            title=title,
        ).render(self)

    def to_csv(self, delimiter: str = ",") -> str:
        """Renderiza el reporte a CSV (aplanado).

        Args:
            delimiter: Delimitador de campos.

        Returns:
            El CSV como cadena.
        """
        from .renderers.csv import CsvRenderer

        return CsvRenderer(delimiter=delimiter).render(self)

    def to_text(self) -> str:
        """Renderiza el reporte a texto plano (para inspección).

        Returns:
            El texto como cadena.
        """
        from .renderers.text import TextRenderer

        return TextRenderer().render(self)

    def to_markdown(self) -> str:
        """Renderiza el reporte a Markdown (tablas GFM, grupos como encabezados).

        Fidelidad limitada: sin formato condicional ni gráficos — los `Chart`
        degradan a una línea de texto resumen y los `Pivot` a una tabla GFM
        filas×columnas. Los enlaces/imágenes se emiten como `[label](href)` /
        `![alt](src)`.

        Returns:
            El Markdown como cadena.
        """
        from .renderers.markdown import MarkdownRenderer

        return MarkdownRenderer().render(self)

    def to_excel(self, ws=None, styles: dict | None = None, formulas: bool = False):
        """Renderiza el reporte a una hoja de Excel (openpyxl).

        Args:
            ws: Hoja existente (None = crea un workbook nuevo).
            styles: Estilos adicionales.
            formulas: Emitir `=SUM(...)` para totales `sum` en lugar del valor.

        Returns:
            La hoja (`Worksheet`) con el contenido.
        """
        from .renderers.excel import ExcelRenderer

        return ExcelRenderer(styles=styles, formulas=formulas).render(self, ws=ws)

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serializa el reporte a JSON con schema versionado.

        Args:
            indent: Indentación de la salida (None = compacto).

        Returns:
            La cadena JSON con `schema_version`.
        """
        from .renderers.json import JsonRenderer

        return JsonRenderer().render(self, indent=indent)

    def to_pdf(self, *, repeat_header: bool = True, **opts) -> bytes:
        """Renderiza el reporte a PDF (reportlab).

        Args:
            repeat_header: Repetir el encabezado de columnas en cada página.
            **opts: Opciones adicionales para `SimpleDocTemplate`.

        Returns:
            Los bytes del PDF.
        """
        from .renderers.pdf import PdfRenderer

        return PdfRenderer().render(self, repeat_header=repeat_header, **opts)


Group.model_rebuild()
