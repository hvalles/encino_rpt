"""Renderer JSON (schema versionado y round-trip validado)."""

from __future__ import annotations

import json

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
        """
        return json.dumps(self.to_dict(result), ensure_ascii=False, indent=indent)

    def to_dict(self, result) -> dict:
        """Devuelve el dict canónico con `schema_version` (tipos JSON nativos)."""
        return {"schema_version": SCHEMA_VERSION, **result.model_dump(mode="json")}
