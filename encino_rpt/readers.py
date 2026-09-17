"""Readers multi-formato para `Report` (CSV, TSV, JSON, JSONL, tuplas, Excel)."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Protocol


class Reader(Protocol):
    """Protocolo de un reader de datos.

    Un reader consume una fuente y devuelve `list[dict]` (filas listas para
    construir un `Report`). Los readers pueden ser los incorporados (`csv`,
    `tsv`, `json`, `jsonl`, `tuples`, `excel`) o custom, registrados con
    `register_reader`.
    """

    def read(self, source, **opts) -> list[dict]:
        """Lee la fuente y devuelve una lista de filas.

        Args:
            source: Ruta (`str`/`PathLike`), objeto file-like (`.read()`) o datos crudos.
            **opts: Opciones específicas del reader (p. ej. `coerce`, `columns`).

        Returns:
            Las filas como `list[dict]`.
        """
        ...


_READERS: dict[str, Reader] = {}


def register_reader(name: str, reader: Reader) -> None:
    """Registra un reader (incorporado o custom) por nombre.

    Args:
        name: Nombre con el que se invoca (p. ej. `"csv"`, `"mi_formato"`).
        reader: Objeto con método `read(source, **opts) -> list[dict]`.
    """
    _READERS[name] = reader


def get_reader(name: str) -> Reader:
    """Devuelve el reader registrado bajo `name`.

    Args:
        name: Nombre del reader.

    Returns:
        El `Reader` registrado.

    Raises:
        ValueError: Si `name` no está registrado.
    """
    try:
        return _READERS[name]
    except KeyError as exc:
        raise ValueError(f"reader no registrado: {name!r}") from exc


def _coerce(value: Any) -> Any:
    """Convierte una celda `str` a su tipo más específico (auto-detección).

    Orden determinista: `null` (`""`/`"null"`/`"none"`) → `bool` (`true`/`false`)
    → `int` → `float`. Si nada aplica, devuelve el string original. Los valores
    no-`str` se devuelven intactos.

    Args:
        value: Valor de la celda.

    Returns:
        El valor convertido, o el original si no es `str` o no se pudo convertir.
    """
    if not isinstance(value, str):
        return value
    s = value.strip()
    low = s.lower()
    if low in ("", "null", "none"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return value


def _read_text(source, *, str_is_path: bool = True) -> str:
    """Normaliza una fuente (ruta, file-like o `str`) a texto.

    Args:
        source: Ruta (`Path`), objeto con `.read()`, o cadena cruda.
        str_is_path: Si `True`, una `str` se interpreta como ruta de archivo.

    Returns:
        El contenido como `str`.

    Raises:
        TypeError: Si la fuente no es una ruta, file-like ni `str`.
    """
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if isinstance(source, str):
        if str_is_path:
            return Path(source).read_text(encoding="utf-8")
        return source
    if hasattr(source, "read"):
        data = source.read()
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return data
    raise TypeError(f"fuente no soportada: {type(source).__name__!r}")


def _read_text_auto(source) -> str:
    """Normaliza una fuente a texto tratando `str` como ruta si existe, si no cruda.

    Args:
        source: Ruta (`Path`), objeto con `.read()`, o `str` (ruta existente o cruda).

    Returns:
        El contenido como `str`.

    Raises:
        TypeError: Si la fuente no es ruta, file-like ni `str`.
    """
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if isinstance(source, str):
        path = Path(source)
        if path.exists():
            return path.read_text(encoding="utf-8")
        return source
    if hasattr(source, "read"):
        data = source.read()
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return data
    raise TypeError(f"fuente no soportada: {type(source).__name__!r}")


class _DelimitedReader:
    """Reader base para texto delimitado (CSV/TSV).

    Usa `csv.DictReader` (primera fila = headers) y aplica auto-detección de
    tipos a cada celda salvo `coerce=False`.
    """

    def __init__(self, delimiter: str):
        self._delimiter = delimiter

    def read(self, source, *, coerce: bool = True, **opts) -> list[dict]:
        """Lee texto delimitado y devuelve `list[dict]`.

        Args:
            source: Ruta (`str`/`PathLike`) o file-like (`.read()` devuelve `str`).
            coerce: Auto-detectar tipos por celda; `False` = todo `str`.
            **opts: Opciones extra ignoradas.

        Returns:
            Las filas como `list[dict]`.
        """
        text = _read_text(source, str_is_path=True)
        reader = csv.DictReader(io.StringIO(text), delimiter=self._delimiter)
        rows: list[dict] = []
        for row in reader:
            if coerce:
                rows.append({k: _coerce(v) for k, v in row.items()})
            else:
                rows.append(dict(row))
        return rows


class JsonReader:
    """Reader para JSON: lista de objetos → `list[dict]`."""

    def read(self, source, **opts) -> list[dict]:
        """Lee JSON (ruta, file-like o cadena cruda).

        Args:
            source: Ruta (`Path`), file-like, o `str` con JSON crudo.
            **opts: Opciones extra ignoradas.

        Returns:
            Las filas como `list[dict]`.

        Raises:
            ValueError: Si el JSON no es una lista de objetos.
        """
        data = json.loads(_read_text_auto(source))
        if not isinstance(data, list):
            raise TypeError("el reader 'json' espera una lista de objetos")
        rows: list[dict] = []
        for item in data:
            if not isinstance(item, dict):
                raise TypeError(
                    "el reader 'json' espera objetos (dict) en cada elemento"
                )
            rows.append(item)
        return rows


class JsonLinesReader:
    """Reader para JSONL: una línea por objeto."""

    def read(self, source, **opts) -> list[dict]:
        """Lee JSONL (un objeto JSON por línea).

        Args:
            source: Ruta (`Path`), file-like, o `str` cruda.
            **opts: Opciones extra ignoradas.

        Returns:
            Las filas como `list[dict]`.

        Raises:
            ValueError: Si alguna línea no es un objeto.
        """
        text = _read_text_auto(source)
        rows: list[dict] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise TypeError("el reader 'jsonl' espera objetos (dict) por línea")
            rows.append(obj)
        return rows


class TuplesReader:
    """Reader para tuplas: `list[tuple]` + `columns=` → `list[dict]`."""

    def read(self, source, *, columns: list[str] | None = None, **opts) -> list[dict]:
        """Convierte `list[tuple]` a `list[dict]` usando `columns`.

        Args:
            source: Lista de tuplas.
            columns: Nombres de columna, en el mismo orden que los campos de la tupla.
            **opts: Opciones extra ignoradas.

        Returns:
            Las filas como `list[dict]`.

        Raises:
            ValueError: Si `columns` no fue provisto.
        """
        if columns is None:
            raise ValueError("`columns` requerido para reader 'tuples'")
        return [dict(zip(columns, row)) for row in source]


class ExcelReader:
    """Reader para hojas Excel (openpyxl, dependencia opcional)."""

    def read(self, source, **opts) -> list[dict]:
        """Lee la primera hoja activa de un workbook Excel.

        La primera fila se usa como headers; el resto como filas `dict`.

        Args:
            source: Ruta al archivo (`.xlsx`/`.xlsm`) o file-like.
            **opts: Opciones extra ignoradas.

        Returns:
            Las filas como `list[dict]`.

        Raises:
            ImportError: Si `openpyxl` no está instalado.
        """
        try:
            from openpyxl import load_workbook
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise ImportError(
                "openpyxl no está instalado; instala el extra `excel`"
            ) from exc

        wb = load_workbook(source)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        header = next(rows_iter, None)
        if header is None:
            return []
        rows: list[dict] = []
        for values in rows_iter:
            rows.append(dict(zip(header, values)))
        return rows


_FORMAT_BY_EXT = {
    ".csv": "csv",
    ".tsv": "tsv",
    ".json": "json",
    ".jsonl": "jsonl",
    ".xlsx": "excel",
    ".xlsm": "excel",
}


def _resolve_format(source, format: str | None) -> str:
    """Resuelve el nombre del reader a partir del `format` o la extensión.

    Args:
        source: Fuente de datos (se inspecciona su extensión si es una ruta).
        format: Nombre explícito del reader, o `None` para resolver por extensión.

    Returns:
        El nombre del reader.

    Raises:
        ValueError: Si `format` es `None` y no se puede resolver por extensión.
    """
    if format is not None:
        return format
    if isinstance(source, (str, Path)):
        ext = Path(str(source)).suffix.lower()
        if ext in _FORMAT_BY_EXT:
            return _FORMAT_BY_EXT[ext]
    raise ValueError("no se pudo resolver el formato del source; pásalo con `format=`")


def read(
    source, format: str | None = None, *, coerce: bool = True, columns=None, **opts
) -> list[dict]:
    """Lee una fuente con el reader indicado (o resuelto por extensión).

    Args:
        source: Ruta (`str`/`PathLike`), objeto file-like, o datos crudos.
        format: Nombre del reader (`csv`, `tsv`, `json`, `jsonl`, `tuples`, `excel`).
            Si es `None`, se resuelve por la extensión del archivo.
        coerce: Auto-detectar tipos por celda (int/float/bool/null); `False` = todo `str`.
        columns: Nombres de columna (requerido por el reader `tuples`).
        **opts: Opciones extra pasadas al reader.

    Returns:
        Las filas como `list[dict]`.

    Raises:
        ValueError: Si `format` es `None` y no se puede resolver por extensión,
            o si el reader indicado no está registrado.
    """
    name = _resolve_format(source, format)
    return get_reader(name).read(source, coerce=coerce, columns=columns, **opts)


# Readers incorporados (registrados al importar el módulo).
register_reader("csv", _DelimitedReader(","))
register_reader("tsv", _DelimitedReader("\t"))
register_reader("json", JsonReader())
register_reader("jsonl", JsonLinesReader())
register_reader("tuples", TuplesReader())
register_reader("excel", ExcelReader())
