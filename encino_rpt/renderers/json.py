"""Renderer JSON (schema versionado y round-trip validado)."""

from __future__ import annotations

import json

from .._serialize import DEPTH_ERROR, to_jsonable

SCHEMA_VERSION = "1.0"


class JsonRenderer:
    """Serializa el `ReportResult` a JSON con un campo `schema_version`."""

    def render(self, result, *, indent: int | None = 2) -> str:
        """Convierte el resultado a una cadena JSON.

        Args:
            result: El `ReportResult` a serializar.
            indent: Indentación (None = compacto).

        Returns:
            La cadena JSON.

        Raises:
            ValueError: Si la jerarquía es demasiado profunda para serializar
                (p. ej. un `path` con miles de niveles).
        """
        try:
            return json.dumps(self.to_dict(result), ensure_ascii=False, indent=indent)
        except RecursionError as exc:
            raise ValueError(DEPTH_ERROR) from exc

    def to_dict(self, result) -> dict:
        """Devuelve el dict canónico con `schema_version` (tipos JSON nativos).

        Raises:
            ValueError: Si la jerarquía es demasiado profunda para serializar a
                JSON (error controlado en vez de un `RecursionError`).
        """
        data = to_jsonable(result)
        return {"schema_version": SCHEMA_VERSION, **data}
