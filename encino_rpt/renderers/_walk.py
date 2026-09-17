"""Traversal compartido del árbol canónico (una sola implementación, iterativa)."""

from __future__ import annotations

from ..models import Chart, Detail, Group, Pivot


def walk(root):
    """Genera eventos tipados en orden de documento, sin recursión.

    Yields tuplas `(evento, nodo)`:
      - ``("group_start", Group)`` antes del encabezado/hijos del grupo.
      - ``("group_end", Group)`` tras los hijos (para totales/footer).
      - ``("detail", Detail)``, ``("chart", Chart)``, ``("pivot", Pivot)``.
    """
    stack = [(root, False)]
    while stack:
        node, closing = stack.pop()
        if closing:
            yield ("group_end", node)
        elif isinstance(node, Group):
            yield ("group_start", node)
            stack.append((node, True))
            for child in reversed(node.children):
                stack.append((child, False))
        elif isinstance(node, Detail):
            yield ("detail", node)
        elif isinstance(node, Chart):
            yield ("chart", node)
        elif isinstance(node, Pivot):
            yield ("pivot", node)
