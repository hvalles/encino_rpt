"""Plantillas `{{token}}` para header/footer (sin colisión con `{0}`)."""

from __future__ import annotations

import re

_TOKEN = re.compile(r"\{\{([a-zA-Z_][a-zA-Z0-9_.]*)\}\}")


def render(template: str, ctx: dict, params: list | None = None) -> str:
    """Interpola `{{campo}}`, `{{param.N}}` y los valores ya inyectados en `ctx`.

    `{{total.NOMBRE}}` / `{{total.SECCION.NOMBRE}}` se resuelven antes (fase de
    totales) y se inyectan en `ctx` con esas claves.
    """
    params = params or []

    def repl(match: re.Match) -> str:
        token = match.group(1)
        if token.startswith("param."):
            suffix = token.split(".", 1)[1]
            if not suffix.isdigit():
                raise ValueError(f"índice de parámetro inválido: {token!r}")
            index = int(suffix)
            if index < 0 or index >= len(params):
                raise IndexError(f"parámetro {index} fuera de rango (hay {len(params)})")
            return str(params[index])
        return str(ctx.get(token, ""))

    return _TOKEN.sub(repl, template)
