"""Mitigación de inyección de fórmulas en Excel/CSV (OWASP)."""

from __future__ import annotations

_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def is_dangerous(value) -> bool:
    """True si `value` es una cadena que Excel/Calc podría tratar como fórmula."""
    return isinstance(value, str) and value.startswith(_DANGEROUS_PREFIXES)


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
