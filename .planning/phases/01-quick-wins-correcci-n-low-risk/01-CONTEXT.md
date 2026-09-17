# Phase 1: Quick Wins (Corrección low-risk) - Context

**Gathered:** 2026-09-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Fixes de bajo riesgo, sin tocar la arquitectura: precisión en `format_value`, `order_by` con funciones custom y con total ausente (error claro), sanitizer CSV/Excel robusto ante espacios/BOM, y eliminación de la dependencia muerta `encino-orm`. No introduce features nuevas.

</domain>

<decisions>
## Implementation Decisions

### Precisión de `format_value` (CORR-02)
- **D-01:** Con `decimals=None`, usar `str(num)` (repr de round-trip más corto) en lugar de `f"{abs(num):g}"`. `1234567.89` → `"1234567.89"`, nunca `"1.23457e+06"`.
- **D-02:** Se acepta notación científica solo para magnitudes extremas: `|num| >= 1e16` o `< 1e-4`. No se exige render expandido de magnitudes enormes.
- **D-03:** La precisión debe encadenar correctamente con todas las opciones de `Format`: `percent_scale` (×100), paréntesis para negativos, símbolo prefijo/sufijo, y `_add_thousands` (separador de miles) debe sobrevivir a strings de precisión completa — `1234567.89` con miles → `"1,234,567.89"`, no romper en `e+06`.

### `order_by` (CORR-04)
- **D-04:** `order_by(expression=...)` evalúa con `report._functions` (y `report._aggregates` donde aplique) — no con `{}`. Consistente con los sitios de evaluación de totales (`aggregation.py:102,174`). No se inyecta el registro `TOTAL()` en el contexto de ordenamiento.

### `order_by` con total ausente (CORR-05)
- **D-05:** Cuando `order_by(total=...)` referencia un total inexistente, lanzar un error claro en español que nombre el total (estilo `f"total de orden inexistente: {name!r}"`), en lugar de devolver `None` y dejar que `sorted()` falle con `TypeError` crudo.
- **D-06:** El error se lanza en cuanto CUALQUIER hijo carece del total (aunque otros hijos sí lo tengan). Política predecible y ruidosa: error en el primer hijo faltante.

### Sanitizer CSV/Excel (SEC-02)
- **D-07:** `is_dangerous` debe escanear pasado el whitespace inicial mediante `value.lstrip()` y también el BOM `\ufeff`, antes de comprobar los prefijos peligrosos (`=`, `+`, `-`, `@`).
- **D-08:** Se amplía el `is_dangerous` compartido — el cambio aplica TANTO a `sanitize_csv` (CSV) como a `write_excel_cell` (Excel). Fuente única de verdad; cierra la misma brecha en Excel.

### Sanitización de salida CSV
- **D-09:** `sanitize_csv` prefija `'` al valor ORIGINAL (con el espacio/BOM intacto), no al valor limpio. `" =1+1"` → `"' =1+1"`. Se conservan los datos del usuario verbatim + prefijo de seguridad.

### Dependencias (DEP-01)
- **D-10:** Eliminar `encino-orm` de `dependencies` en `pyproject.toml` AND limpiar las referencias a 'companion encino-orm' en README/docs que queden como engañosas. El contrato de entrada permanece `list[dict]`. Regenerar `uv.lock`.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Formato
- `encino_rpt/renderers/_format.py` — la función `format_value` (línea 29: `f"{abs(num):g}"` es el bug) y `_add_thousands`.
- `encino_rpt/models.py` — definición del modelo `Format` (campos `decimals`, `percent_scale`, `thousands`, `symbol`, `negative`, etc.).

### `order_by`
- `encino_rpt/aggregation.py` — `_apply_order` (277-287) y `_sort_key` (290-307); sitios de evaluación con funciones: 102, 174.
- `encino_rpt/section.py` — `Section.order_by` (117-138), almacenamiento del dict `order_by` en `GroupSpec`.
- `encino_rpt/expressions.py` — firma de `evaluate`.

### Sanitización
- `encino_rpt/renderers/_sanitize.py` — `_DANGEROUS_PREFIXES` (5), `is_dangerous` (8-10), `sanitize_csv` (13-17), `write_excel_cell` (20-27).
- `encino_rpt/renderers/csv.py` — uso de `sanitize_csv` en `CsvRenderer`.
- `encino_rpt/renderers/excel.py` — uso de `write_excel_cell`.

### Dependencias
- `pyproject.toml` — `dependencies` (línea 32-35): eliminar `encino-orm>=0.2.1`.

### Contexto/seguridad
- `.planning/codebase/CONCERNS.md` — sección "Known Bugs" (format_value, order_by) y "Security Considerations" (CSV sanitizer); sección "Tech Debt" (encino-orm).
- `docs/design/10-report.md` — contrato de referencia de la librería.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `encino_rpt/aggregation.py`: `evaluate`, usado en 4 sitios — el patrón de función-threading ya existe, `_sort_key` es el único que pasa `{}`; alinearlo es trivial.
- `encino_rpt/renderers/_sanitize.py`: helpers `is_dangerous` / `sanitize_csv` / `write_excel_cell` ya modularizados — el cambio se limita a `is_dangerous`.
- `_add_thousands` (`_format.py:42-48`): ya tolera overflow con try/except; hay que verificar que `int(int_part)` funcione con precision-completa.

### Established Patterns
- Error messages en español, siempre con el valor ofensor vía `!r` (`ValueError(f"... {name!r}")`) — aplicar a D-05/D-06.
- Convención de no atrapar/silenciar errores: el library solo tiene try/except en los guard de dependencias opcionales. El error de total inexistente debe `raise`, no fallback.

### Integration Points
- `_apply_order` es llamado desde `_build_group` (`aggregation.py:260`) después de construir los hijos; el error de total inexistente se lanzará en tiempo de `run()`, no en declaración.
- `_sort_key` recibe `child` (Group/Detail) — el error debe incluir el nombre del hijo (grupo/fila) además del total para contexto.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-Quick Wins (Corrección low-risk)*
*Context gathered: 2026-09-16*