"""Mitigación de inyección de fórmulas en Excel/CSV (OWASP)."""

from __future__ import annotations

import re

_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

_LEADING_TRIM = re.compile(r"^[\s\ufeff]+")


def is_dangerous(value) -> bool:
    """True si Excel/Calc podría tratar `value` como fórmula tras ignorar espacios/BOM iniciales."""
    return isinstance(value, str) and _LEADING_TRIM.sub("", value).startswith(
        _DANGEROUS_PREFIXES
    )


def sanitize_csv(value):
    """Prefija `'` a cadenas peligrosas para que el CSV se importe como texto."""
    if is_dangerous(value):
        return "'" + value
    return value


def write_excel_cell(cell, value):
    """Asigna `value` a la celda sin que openpyxl lo convierta en fórmula.

    Devuelve `cell` para poder encadenar (p. ej. `cell.number_format = ...`).
    """
    cell.value = value
    if is_dangerous(value):
        cell.data_type = "s"
    return cell
