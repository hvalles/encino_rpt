# Phase 1: Quick Wins (Corrección low-risk) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-16
**Phase:** 1-Quick Wins (Corrección low-risk)
**Areas discussed:** format_value precision, order_by fixes, CSV sanitizer scope, DEP-01 encino-orm

---

## format_value precision

| Option | Description | Selected |
|--------|-------------|----------|
| str() repr | Shortest round-trip repr; no artificial truncation; sci only for |num|>=1e16 or <1e-4 | ✓ |
| Decimal-clean | Convert via Decimal to avoid float artifacts, more code | |
| High-precision g | :.10g / :.17g, still has cutoff and can emit sci | |

**User's choice:** str() repr
**Notes:** Also chose "Keep sci for extremes" (magnitudes >=1e16 pueden quedar en notación científica) y "Chain all options" (la precisión debe encadenar con percent_scale, thousands, symbol, negative parens).

---

## order_by fixes

| Option | Description | Selected |
|--------|-------------|----------|
| Thread functions | Pasar report._functions (y aggregates donde aplique) a _apply_order/_sort_key, consistente con aggregation.py:102,174 | ✓ |
| Also inject TOTAL() | Añadir el registro TOTAL() al contexto de ordenamiento | |
| Functions only | Solo funciones, sin aggregates | |

| Option | Description | Selected |
|--------|-------------|----------|
| Raise clear error | ValueError en español nombrando el total inexistente | ✓ |
| Sentinel fallback | Ordenar None como -inf/+inf, silencioso | |
| Aggregate error | Un solo error por nombre distinto | |

| Option | Description | Selected |
|--------|-------------|----------|
| Error on any missing | Error en el primer hijo que carece del total | ✓ |
| Only if none have it | Fallback si al menos un hijo lo tiene | |
| You decide | Dejar la política al implementador | |

**User's choice:** Thread functions + Raise clear error + Error on any missing
**Notes:** El error debe incluir contexto del hijo (grupo/fila) además del total, según la convención de errores en español.

---

## CSV sanitizer scope

| Option | Description | Selected |
|--------|-------------|----------|
| lstrip() + BOM | Escanear pasado whitespace y BOM \ufeff antes del check | ✓ |
| Space + \x0c only | Solo los dos casos citados en el roadmap | |
| Whitespace only | Whitespace pero BOM como preocupación aparte | |

| Option | Description | Selected |
|--------|-------------|----------|
| Widen both | Ampliar is_dangerous compartido (CSV + Excel) | ✓ |
| CSV only | Solo sanitize_csv, Excel se cubre en Phase 2 (SEC-01) | |

| Option | Description | Selected |
|--------|-------------|----------|
| Prefix original value | "'" + valor original con espacio intacto (" =1+1" -> "' =1+1") | ✓ |
| Strip then prefix | Quitar whitespace luego prefijar ("'=1+1") | |
| You decide | Dejar estrategia al implementador | |

**User's choice:** lstrip() + BOM, Widen both, Prefix original value

---

## DEP-01 encino-orm

| Option | Description | Selected |
|--------|-------------|----------|
| Dep + docs cleanup | Eliminar de pyproject.toml + limpiar referencias engañosas en README/docs, regenerar uv.lock | ✓ |
| Dep only | Solo eliminar de pyproject.toml | |
| Move to dev group | Conservar en dev como ejemplo de integración | |

**User's choice:** Dep + docs cleanup

---

## the agent's Discretion

- Ninguna — todas las decisiones fueron tomadas por el usuario.

## Deferred Ideas

- Ninguna. La discusión se mantuvo dentro del alcance de la fase.