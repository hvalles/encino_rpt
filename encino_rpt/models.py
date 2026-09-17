"""Modelo de datos canónico del reporte (dataclasses stdlib, serializable a JSON)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


@dataclass
class Link:
    """Enlace a otra sección, reporte, página o URL externa."""

    target: Literal["section", "report", "page", "external"]
    href: str
    type: Literal["link"] = "link"
    label: str | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.target not in ("section", "report", "page", "external"):
            raise ValueError(f"target inválido: {self.target!r}")


@dataclass
class Image:
    """Imagen por ruta, URL o data URI."""

    src: str
    type: Literal["image"] = "image"
    alt: str | None = None
    width: int | None = None
    height: int | None = None


@dataclass
class Format:
    """Formato de presentación de una columna o total (lo aplican los renderers)."""

    kind: Literal["number", "currency", "percent", "date"] = "number"
    decimals: int | None = None  # None -> no redondea
    thousands: bool = False  # separador de miles
    symbol: str | None = None  # p. ej. "$", "€"
    symbol_position: Literal["prefix", "suffix"] = "prefix"
    negative: Literal["minus", "paren"] = "minus"
    percent_scale: bool = False  # percent: multiplica por 100 al mostrar
    pattern: str | None = None  # kind="date": patrón strftime

    def __post_init__(self):
        if self.kind not in ("number", "currency", "percent", "date"):
            raise ValueError(f"kind inválido: {self.kind!r}")
        if self.symbol_position not in ("prefix", "suffix"):
            raise ValueError(f"symbol_position inválido: {self.symbol_position!r}")
        if self.negative not in ("minus", "paren"):
            raise ValueError(f"negative inválido: {self.negative!r}")


@dataclass
class Total:
    """Total de un corte (resultado ya calculado)."""

    operator: str
    column: str | None = None
    expression: str | None = None
    name: str | None = None
    label: str | None = None
    value: Any = None
    format: Format | None = None
    column_position: str | None = None
    hidden: bool = False  # referenciable vía {{total.NOMBRE}} pero no renderizado


@dataclass
class Detail:
    """Renglón del detalle."""

    row: dict[str, Any]
    type: Literal["detail"] = "detail"


@dataclass
class Series:
    """Serie de un gráfico (una línea/barra/sector)."""

    label: str | None = None
    values: list[Any] = field(default_factory=list)


@dataclass
class Chart:
    kind: Literal["pie", "bar", "line"]
    type: Literal["chart"] = "chart"
    title: str | None = None
    labels: list[Any] = field(default_factory=list)
    series: list[Series] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.kind not in ("pie", "bar", "line"):
            raise ValueError(f"kind de gráfico inválido: {self.kind!r}")


@dataclass
class Pivot:
    """Matriz de doble entrada (cross-tab): filas x columnas."""

    type: Literal["pivot"] = "pivot"
    title: str | None = None
    rows: list[Any] = field(default_factory=list)
    columns: list[Any] = field(default_factory=list)
    cells: list[list[Any]] = field(default_factory=list)
    row_totals: list[Any] = field(default_factory=list)
    column_totals: list[Any] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionalRule:
    """Regla de formato condicional por valor (la aplican los renderers)."""

    column: str | None = None
    when: Literal["lt", "le", "gt", "ge", "eq", "ne"] = "lt"
    value: Any = 0
    style: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.when not in ("lt", "le", "gt", "ge", "eq", "ne"):
            raise ValueError(f"when inválido: {self.when!r}")


@dataclass
class Kpi:
    """Tarjeta de indicador (métrica escalar)."""

    type: Literal["kpi"] = "kpi"
    label: str | None = None
    value: Any = None
    format: Format | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class Group:
    type: Literal["group"] = "group"
    name: str = ""
    key: dict[str, Any] | None = None
    header: str | None = None
    footer: str | None = None
    show_collapsed: bool = False
    default_collapsed: bool = False
    page_break: bool = False
    totals: list[Total] = field(default_factory=list)
    children: list[Detail | Group | Chart | Pivot] = field(default_factory=list)

    def __post_init__(self):
        # Contexto interno (no serializado) para renderizar header/footer en la
        # fase final. Atributos de instancia (no campos), replican PrivateAttr.
        self._first_row: dict = {}
        self._header_tpl: str | None = None
        self._footer_tpl: str | None = None


@dataclass
class ReportMeta:
    """Metadatos del reporte (título y parámetros de la consulta)."""

    title: str | None = None
    params: list[Any] = field(default_factory=list)


@dataclass
class ReportResult:
    """Árbol canónico del reporte (dato puro, serializable a JSON).

    Expone métodos de conveniencia (`render_html`, `to_csv`, `to_text`,
    `to_excel`, `to_pdf`, `to_json`) que delegan en los renderers sin modificar
    el árbol, y `to_dict`/`from_dict`/`from_json` para la serialización.
    """

    root: Group
    meta: ReportMeta = field(default_factory=ReportMeta)
    columns: list[str] = field(default_factory=list)
    formats: dict[str, Format] = field(default_factory=dict)
    styles: list[ConditionalRule] = field(default_factory=list)
    kpis: list[Kpi] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Devuelve el árbol como dict con tipos JSON nativos.

        Returns:
            El árbol canónico como `dict` (equivalente al anterior
            `model_dump(mode="json")`), sin `schema_version`.
        """
        from ._serialize import to_jsonable

        return to_jsonable(self)

    @classmethod
    def from_dict(cls, data: dict) -> ReportResult:
        """Reconstruye un `ReportResult` a partir de un dict (round-trip).

        Args:
            data: Dict producido por `to_dict()` (o `to_json()` parseado).

        Returns:
            El `ReportResult` reconstruido.
        """
        from ._serialize import from_dict

        return from_dict(data)

    @classmethod
    def from_json(cls, s: str) -> ReportResult:
        """Reconstruye un `ReportResult` a partir de una cadena JSON.

        Args:
            s: JSON producido por `to_json()`.

        Returns:
            El `ReportResult` reconstruido.
        """
        import json

        return cls.from_dict(json.loads(s))

    def render_html(
        self,
        classes: dict | None = None,
        repeat_header: bool = False,
        *,
        css: bool = False,
        template: bool = False,
        title: str | None = None,
        file=None,
    ) -> str | None:
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
            file: Objeto file-like con `write(str)`; si se provee, el HTML se
                escribe ahí (streaming) y devuelve `None`.

        Returns:
            El HTML como cadena, o `None` si se pasó `file`.
        """
        from .renderers.html import HtmlRenderer

        renderer = HtmlRenderer(
            classes=classes,
            repeat_header=repeat_header,
            css=css,
            template=template,
            title=title,
        )
        if file is None:
            return renderer.render(self)
        renderer.write(self, file)
        return None

    def iter_html(
        self,
        classes: dict | None = None,
        repeat_header: bool = False,
        *,
        css: bool = False,
        template: bool = False,
        title: str | None = None,
    ):
        """Genera los fragmentos HTML del reporte (streaming).

        Args:
            classes: Mapa de clases CSS por tipo de fila.
            repeat_header: Repetir el encabezado de columnas por grupo.
            css: Formato condicional como clases + `<style>` (opt-in).
            template: Envolver en documento HTML completo.
            title: Título del documento.

        Yields:
            Fragmentos HTML cuya concatenación equivale a `render_html()`.
        """
        from .renderers.html import HtmlRenderer

        renderer = HtmlRenderer(
            classes=classes,
            repeat_header=repeat_header,
            css=css,
            template=template,
            title=title,
        )
        yield from renderer.iter_html(self)

    def to_csv(self, delimiter: str = ",", *, file=None) -> str | None:
        """Renderiza el reporte a CSV (aplanado).

        Args:
            delimiter: Delimitador de campos.
            file: Objeto file-like con `write(str)`; si se provee, el CSV se
                escribe ahí (streaming) y devuelve `None`.

        Returns:
            El CSV como cadena, o `None` si se pasó `file`.
        """
        from .renderers.csv import CsvRenderer

        renderer = CsvRenderer(delimiter=delimiter)
        if file is None:
            return renderer.render(self)
        renderer.write(self, file)
        return None

    def iter_csv(self, delimiter: str = ","):
        """Genera las líneas CSV del reporte (streaming).

        Args:
            delimiter: Delimitador de campos.

        Yields:
            Cada línea CSV como `str` (sin terminador de línea).
        """
        from .renderers.csv import CsvRenderer

        yield from CsvRenderer(delimiter=delimiter).iter_csv(self)

    def to_text(self, *, file=None) -> str | None:
        """Renderiza el reporte a texto plano (para inspección).

        Args:
            file: Objeto file-like con `write(str)`; si se provee, el texto se
                escribe ahí (streaming) y devuelve `None`.

        Returns:
            El texto como cadena, o `None` si se pasó `file`.
        """
        from .renderers.text import TextRenderer

        renderer = TextRenderer()
        if file is None:
            return renderer.render(self)
        renderer.write(self, file)
        return None

    def iter_text(self):
        """Genera las líneas de texto del reporte (streaming).

        Yields:
            Cada línea de texto como `str`.
        """
        from .renderers.text import TextRenderer

        yield from TextRenderer().iter_text(self)

    def to_markdown(self, *, file=None) -> str | None:
        """Renderiza el reporte a Markdown (tablas GFM, grupos como encabezados).

        Fidelidad limitada: sin formato condicional ni gráficos — los `Chart`
        degradan a una línea de texto resumen y los `Pivot` a una tabla GFM
        filas×columnas. Los enlaces/imágenes se emiten como `[label](href)` /
        `![alt](src)`.

        Args:
            file: Objeto file-like con `write(str)`; si se provee, el Markdown se
                escribe ahí (streaming) y devuelve `None`.

        Returns:
            El Markdown como cadena, o `None` si se pasó `file`.
        """
        from .renderers.markdown import MarkdownRenderer

        renderer = MarkdownRenderer()
        if file is None:
            return renderer.render(self)
        renderer.write(self, file)
        return None

    def iter_markdown(self):
        """Genera las líneas Markdown del reporte (streaming).

        Yields:
            Cada línea Markdown como `str`.
        """
        from .renderers.markdown import MarkdownRenderer

        yield from MarkdownRenderer().iter_markdown(self)

    def to_excel(self, ws=None, formulas: bool = False):
        """Renderiza el reporte a una hoja de Excel (openpyxl).

        Args:
            ws: Hoja existente (None = crea un workbook nuevo).
            formulas: Emitir `=SUM(...)` para totales `sum` en lugar del valor.

        Returns:
            La hoja (`Worksheet`) con el contenido.
        """
        from .renderers.excel import ExcelRenderer

        return ExcelRenderer(formulas=formulas).render(self, ws=ws)

    def to_json(self, *, indent: int | None = 2) -> str:
        """Serializa el reporte a JSON con schema versionado.

        Args:
            indent: Indentación de la salida (None = compacto).

        Returns:
            La cadena JSON con `schema_version`.

        Raises:
            ValueError: Si la jerarquía es demasiado profunda para serializar a
                JSON (p. ej. un `path` con miles de niveles); se lanza un error
                controlado en lugar de un `RecursionError`.
        """
        from .renderers.json import JsonRenderer

        return JsonRenderer().render(self, indent=indent)

    def to_pdf(self, *, repeat_header: bool = True, file=None, **opts) -> bytes | None:
        """Renderiza el reporte a PDF (reportlab).

        Args:
            repeat_header: Repetir el encabezado de columnas en cada página.
            file: Objeto file-like binario (`.write(bytes)`); si se provee, el PDF
                se escribe ahí (streaming) y devuelve `None`.
            **opts: Opciones adicionales para `SimpleDocTemplate`.

        Returns:
            Los bytes del PDF, o `None` si se pasó `file`.
        """
        from .renderers.pdf import PdfRenderer

        return PdfRenderer().render(
            self, repeat_header=repeat_header, file=file, **opts
        )
