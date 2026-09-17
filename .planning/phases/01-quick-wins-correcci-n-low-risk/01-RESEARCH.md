# Phase 1: Quick Wins (Corrección low-risk) — Research

**Researched:** 2026-09-16
**Domain:** Corrección de precisión numérica (`format_value`), ordenamiento (`order_by`), sanitización de inyección de fórmulas (CSV/Excel) y limpieza de dependencia muerta
**Confidence:** HIGH

## Summary

Fase de correcciones puntuales de bajo riesgo sobre **código existente** — no introduce librerías ni features nuevas. Los cinco bugs fueron **reproducidos y verificados por ejecución directa** (probes) contra el código actual: `format_value(1234567.89, Format())` → `'1.23457e+06'` (CORR-02), `order_by(expression="doblado(monto)")` → `ExpressionError` por no pasar `report._functions` (CORR-04), `order_by(total="inexistente")` → `TypeError` crudo (CORR-05), `is_dangerous(" =1+1")` → `False` (bypass por espacio/BOM, SEC-02), y `encino-orm` declarado como dependencia runtime sin ningún import (DEP-01).

Los tres fixes de código son **cirugía mínima con call sites únicos ya identificados**: (1) `format_value` en `renderers/_format.py:23-29` — reemplazar `f"{abs(num):g}"` por `str(abs(num))`, con **escala percent vía `Decimal`** para evitar el artefacto binario `7.000000000000001%` (verificado por POC); (2) `_apply_order`/`_sort_key` en `aggregation.py:277-307` — pasar `report._functions` como parámetro (patrón ya usado en `aggregation.py:102,174`) y `raise ValueError` con el nombre del total ausente; (3) `is_dangerous` en `renderers/_sanitize.py:8-10` — escanear pasado whitespace+BOM (regex `^[\s\ufeff]+`), que arregla CSV y Excel con **una sola fuente de verdad** (D-08). El fix del sanitizer fue verificado end-to-end: con solo ampliar `is_dangerous`, `sanitize_csv` y `write_excel_cell` pasan a proteger `" =1+1"` y `"\ufeff@evil"` sin tocar ninguna otra línea.

Un hallazgo clave de la investigación: **`str(float)` de CPython usa exactamente los umbrales de notación científica que pide D-02** (`|num| < 1e-4` o `>= 1e16`), por lo que `str()` satisface D-01 y D-02 simultáneamente sin código adicional. El único caso que requiere cuidado adicional es `percent_scale + decimals=None`, donde `str(0.07 * 100)` produce `'7.000000000000001'` (regresión vs. el `'7%'` actual) — la solución Decimal verificada lo elimina. El caso de inyección por whitespace inicial está **corroborado por fuente externa**: el advisory GHSA-xrwp-2gph-985x (EspoCRM, julio 2026) documenta exactamente esta clase de bypass y recomienda el mismo fix decidido en D-07 (recortar whitespace/controles antes del check y prefijar el valor original).

**Primary recommendation:** Cinco tareas pequeñas, cada una con su test de regresión: (1) fix `format_value` con escala percent vía `Decimal`, (2) thread de `report._functions` en `_sort_key`, (3) `raise ValueError` descriptivo en total ausente, (4) widen `is_dangerous` con regex whitespace+BOM, (5) `pyproject.toml` + `uv lock` + audit docs. Sin paquetes nuevos — todo es stdlib.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Precisión de `format_value` (CORR-02)
- **D-01:** Con `decimals=None`, usar `str(num)` (repr de round-trip más corto) en lugar de `f"{abs(num):g}"`. `1234567.89` → `"1234567.89"`, nunca `"1.23457e+06"`.
- **D-02:** Se acepta notación científica solo para magnitudes extremas: `|num| >= 1e16` o `< 1e-4`. No se exige render expandido de magnitudes enormes.
- **D-03:** La precisión debe encadenar correctamente con todas las opciones de `Format`: `percent_scale` (×100), paréntesis para negativos, símbolo prefijo/sufijo, y `_add_thousands` (separador de miles) debe sobrevivir a strings de precisión completa — `1234567.89` con miles → `"1,234,567.89"`, no romper en `e+06`.

#### `order_by` (CORR-04)
- **D-04:** `order_by(expression=...)` evalúa con `report._functions` (y `report._aggregates` donde aplique) — no con `{}`. Consistente con los sitios de evaluación de totales (`aggregation.py:102,174`). No se inyecta el registro `TOTAL()` en el contexto de ordenamiento.

#### `order_by` con total ausente (CORR-05)
- **D-05:** Cuando `order_by(total=...)` referencia un total inexistente, lanzar un error claro en español que nombre el total (estilo `f"total de orden inexistente: {name!r}"`), en lugar de devolver `None` y dejar que `sorted()` falle con `TypeError` crudo.
- **D-06:** El error se lanza en cuanto CUALQUIER hijo carece del total (aunque otros hijos sí lo tengan). Política predecible y ruidosa: error en el primer hijo faltante.

#### Sanitizer CSV/Excel (SEC-02)
- **D-07:** `is_dangerous` debe escanear pasado el whitespace inicial mediante `value.lstrip()` y también el BOM `\ufeff`, antes de comprobar los prefijos peligrosos (`=`, `+`, `-`, `@`).
- **D-08:** Se amplía el `is_dangerous` compartido — el cambio aplica TANTO a `sanitize_csv` (CSV) como a `write_excel_cell` (Excel). Fuente única de verdad; cierra la misma brecha en Excel.

#### Sanitización de salida CSV
- **D-09:** `sanitize_csv` prefija `'` al valor ORIGINAL (con el espacio/BOM intacto), no al valor limpio. `" =1+1"` → `"' =1+1"`. Se conservan los datos del usuario verbatim + prefijo de seguridad.

#### Dependencias (DEP-01)
- **D-10:** Eliminar `encino-orm` de `dependencies` en `pyproject.toml` AND limpiar las referencias a 'companion encino-orm' en README/docs que queden como engañosas. El contrato de entrada permanece `list[dict]`. Regenerar `uv.lock`.

### the agent's Discretion

- Ninguna — todas las decisiones fueron tomadas por el usuario (DISCUSSION-LOG).

### Deferred Ideas (OUT OF SCOPE)

- Ninguna. La discusión se mantuvo dentro del alcance de la fase.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORR-02 | `format_value` conserva precisión completa con `decimals=None` (sin notación científica ni pérdida de dígitos) | Bug reproducido (`'1.23457e+06'`). Fix verificado por POC: `str(abs(num))` + escala percent vía `Decimal`. `str()` de CPython usa exactamente los umbrales de D-02. `_add_thousands` verificado con precisión completa. |
| CORR-04 | `order_by(expression=...)` evalúa con funciones custom registradas vía `add_function` | Bug reproducido (`ExpressionError: función no permitida: 'doblado'`). `_sort_key` es el único sitio que pasa `{}` (aggregation.py:300); `_apply_order` tiene call site único (aggregation.py:260) — thread trivial de `report._functions`. |
| CORR-05 | `order_by(total=...)` con total inexistente lanza error claro nombrando el total | Bug reproducido (`TypeError: '<' not supported...`). `_sort_key` retorna `None` (aggregation.py:298); reemplazar por `raise ValueError` con `!r`; el raise dentro del key de `sorted()` propaga por `run()`. |
| SEC-02 | Sanitizer CSV detecta caracteres peligrosos precedidos de espacio/BOM | Bug reproducido (`is_dangerous(' =1+1') == False`). Fix verificado end-to-end (CSV + Excel): regex `^[\s\ufeff]+`; BOM `\ufeff` NO es whitespace para `str.lstrip()` (verificado). `sanitize_csv`/`write_excel_cell` no necesitan cambios. Corroborado por GHSA-xrwp-2gph-985x. |
| DEP-01 | Dependencia muerta `encino-orm` eliminada de `pyproject.toml` | Verificado: 0 imports en `encino_rpt/` y `tests/`. `uv.lock`: encino-orm + 5 paquetes transitivos serán podados (aiomysql, aiosqlite, asyncpg, async-timeout, pymysql). Docs: README/index.md mencionan solo la forma de salida (`fetch_all`), no la dependencia; `docs/design/10-report.md` §10/§12 ya dicen "opcional"/"cero dependencias" — audit ligero. |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Formateo de valores (`format_value`, `_add_thousands`) | API / renderers compartidos (`renderers/_format.py`) | — | Es formateo de presentación usado por los 5 renderers; el valor crudo nunca se altera (los cambios son de texto, no de datos). |
| Ordenamiento de hijos (`order_by`) | API / motor de agregación (`aggregation.py` fase C) | Builder (`Section.order_by` valida dirección) | `_apply_order`/`_sort_key` son parte de la fase C post-totales; el builder solo almacena el dict `order_by` en `GroupSpec`. |
| Sanitización de inyección de fórmulas | API / renderers compartidos (`renderers/_sanitize.py`) | Renderers CSV/Excel (consumidores) | `is_dangerous` es la única fuente de verdad (D-08); los renderers solo la invocan. |
| Dependencias del paquete | Build config (`pyproject.toml` + `uv.lock`) | — | DEP-01 es puramente declarativo; el contrato de entrada `list[dict]` vive en `Report.__init__`, no en la dependencia. |

## Standard Stack

Esta fase **no introduce ninguna librería nueva**. Todo el trabajo usa stdlib de Python 3.10+ y el stack existente del proyecto.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `str()` / `repr()` nativos | Python 3.1+ (repr corto round-trip) | Formateo de precisión completa con `decimals=None` (CORR-02) | Es la representación canónica de float de CPython: el repr más corto que hace round-trip exacto; usa exactamente los umbrales de sci de D-02 (`< 1e-4`, `>= 1e16`) — verificado en 3.11 y 3.14. `[VERIFIED: probe]` |
| `decimal.Decimal` | stdlib (ya importado en `_format.py:6`) | Escala exacta `×100` en `percent_scale` con `decimals=None` | Evita el artefacto binario `0.07*100 == 7.000000000000001`; `format(d.normalize(), 'f')` da `'7'`, `'29'`, `'25.6'` limpios — verificado por POC. `[VERIFIED: probe]` |
| `re` (`^[\s\ufeff]+`) | stdlib (ya usado en `template.py:7`) | Recorte de whitespace+BOM inicial en `is_dangerous` (SEC-02) | `\s` cubre todo el whitespace Unicode (incl. `\x0c` y `\x0b`); `\ufeff` se añade explícito porque NO es whitespace para `str.lstrip()` — verificado. `[VERIFIED: probe]` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | 9.1.1 (dev, ya en el proyecto) | Tests de regresión para cada fix | Cada fix nuevo requiere su test (ver Validation Architecture); no se añade infraestructura. `[VERIFIED: uv.lock]` |
| `ruff` | 0.16.7 (dev, ya en el proyecto) | Lint CI | `uv run ruff check` debe seguir limpio tras cada cambio. `[VERIFIED: uv run ruff --version]` |
| `pydantic` | 2.13.5 (runtime, única dependencia que permanece) | Modelo canónico (sin cambios) | Tras DEP-01 queda como única dependencia runtime, que es el contrato del proyecto. `[VERIFIED: uv.lock]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `str(num)` (D-01) | `f"{num:.10g}"` / `:.17g` | D-01 fue decidido por el usuario; `.17g` tiene cutoff arbitrario y aún emite sci en magnitudes medias. |
| `str(num)` (D-01) | `Decimal(str(num))` siempre | Conversión Decimal de todos los valores añade código sin beneficio; solo se necesita para la escala percent (única operación aritmética en el formateo). |
| Regex `^[\s\ufeff]+` | Tres `lstrip()` encadenados | Ambos funcionan (verificado); el regex expresa la intención "saltar espacios y BOM" en una sola línea y cubre intercalaciones cualquier orden. |
| `raise ValueError` en `_sort_key` (D-05) | Centinela `-inf` / fallback silencioso | D-05/D-06 decididos por el usuario: error ruidoso en el primer hijo faltante, no fallback silencioso. |

**Installation:** No hay instalación de paquetes nuevos en esta fase. La única operación de entorno es la **eliminación** de `encino-orm`:

```bash
# Editar pyproject.toml (quitar "encino-orm>=0.2.1" de dependencies)
uv lock        # regenera uv.lock (podará encino-orm y 5 transitivos)
uv sync        # poda el venv local
```

**Version verification:** No aplica paquetes nuevos que verificar. Versiones del entorno verificadas el 2026-09-16: Python 3.14.7 (sistema) / 3.11.13 (venv uv), uv 0.8.22, pytest 9.1.1, ruff 0.16.7, openpyxl 3.1.5, reportlab 5.0.1, pydantic 2.13.5. `[VERIFIED: probes]`

## Package Legitimacy Audit

> Esta fase **no instala ningún paquete externo** — sólo elimina uno (`encino-orm`). El protocolo de legitimidad aplica a paquetes nuevos; no hay ninguno. `slopcheck` no se ejecuta por no haber instalaciones.

| Package | Registry | Disposition | Notas |
|---------|----------|-------------|-------|
| `encino-orm` (REMOVED) | PyPI | Eliminado — DEP-01 | Declarado `>=0.2.1` en `pyproject.toml:33`, 0 imports en `encino_rpt/` y `tests/` `[VERIFIED: grep]`. Elimina además 5 transitivos del lock: `aiomysql`, `aiosqlite`, `asyncpg`, `async-timeout`, `pymysql` `[VERIFIED: uv.lock]`. |

**Packages removed due to slopcheck [SLOP] verdict:** none (no installs)
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```text
                      ┌────────────────────────────────────────────────────────┐
                      │                     encino_rpt                          │
                      │                                                        │
 entrada list[dict]   │   builder (report.py/section.py)                       │
 ───────────────────► │      │                                                 │
                      │      ▼                                                 │
                      │   build() aggregation.py                               │
                      │      ├── _enrich (evaluate + report._functions)  ◄─ CORR-04: _sort_key pasa {} hoy
                      │      ├── _build_group → _apply_order/_sort_key  ◄─ CORR-04/CORR-05 (fase C)
                      │      └── _compute_totals_into (evaluate)        ◄─ patrón referencia (funciones)
                      │      │                                                 │
                      │      ▼                                                 │
                      │   ReportResult (modelos pydantic)                      │
                      │      │                                                 │
                      │      ▼                                                 │
                      │   renderers: html excel csv text pdf                   │
                      │       │        │      │                                │
                      │       │        │      └─ format_value ◄─ CORR-02 (_format.py:29 bug)
                      │       │        │                                      │
                      │       │        └── sanitize_csv  ─┐                    │
                      │       │                          ├─ is_dangerous ◄─ SEC-02 (_sanitize.py:8 bug)
                      │       └────────── write_excel_cell┘                    │
                      └────────────────────────────────────────────────────────┘

 pyproject.toml + uv.lock  ◄─ DEP-01: eliminar encino-orm (línea 33) + regenerar lock
```

Trazado del caso primario: `list[dict]` → builder → `run()`/`build()` (enriquecimiento + árbol + fase C que **incluye el ordenamiento**) → `ReportResult` → renderers que aplican `format_value` y el sanitizer compartido. Los tres fixes tocan puntos de la tubería sin cambiar su arquitectura (entry point, fases A/B/C, contrato del árbol intactos).

### Recommended Project Structure

No se crean archivos nuevos. Cambios acotados (call sites únicos verificados `[VERIFIED: grep]`):

```
encino_rpt/
├── aggregation.py            # _apply_order/_sort_key: +param functions, +raise (líneas 277-307) + call site 260
├── renderers/
│   ├── _format.py            # format_value: branch decimals=None con str() + escala Decimal percent (23-29)
│   └── _sanitize.py          # is_dangerous: recorte whitespace+BOM (8-10); import re
pyproject.toml                # quitar línea 33 (encino-orm)
uv.lock                       # regenerar con `uv lock`
tests/
├── test_report.py            # +tests CORR-04/CORR-05 (sección order_by)
├── test_report_renderers.py  # +tests CORR-02 (sección format_value)
└── test_security.py          # +tests SEC-02 (banner P5)
docs/security.md              # actualizar descripción del sanitizer (líneas 30-41)
```

### Pattern 1: Fuente única de verdad para detección (D-08)

**What:** Ampliar `is_dangerous` (el detector compartido) en lugar de tocar los consumidores. Como `sanitize_csv` (línea 15) y `write_excel_cell` (línea 26) ya llaman a `is_dangerous`, el fix de detección cubre CSV y Excel con un solo cambio.
**When to use:** Siempre que un control de seguridad compartido tenga una brecha; nunca duplicar el check en cada renderer.
**Verificación:** Probado end-to-end con `is_dangerous` ampliado por monkeypatch: `to_csv()` emite `' =1+1` y `'\ufeff@evil` (valores originales + prefijo), y `to_excel()` produce `data_type='s'` en ambas celdas — **sin tocar `sanitize_csv` ni `write_excel_cell`**. `[VERIFIED: probe]`

### Pattern 2: Threading de funciones (CORR-04)

**What:** `_sort_key` es el único sitio de evaluación que pasa `{}` como funciones (`aggregation.py:300`); los demás (102, 174) pasan `report._functions`. Alinear = pasar `functions` a `_apply_order`/`_sort_key` desde `_build_instance` (que ya recibe `report`).
**When to use:** Consistencia con el patrón existente de función-threading; no inyectar `TOTAL()` en el contexto de orden (D-04 explícito).
**Call sites verificados:** `_apply_order` solo se llama en `aggregation.py:260`; `_sort_key` solo en `aggregation.py:281`. `[VERIFIED: grep]`

### Pattern 3: Formato de precisión con escala Decimal (CORR-02/D-03)

**What:** Con `decimals=None`: `str(abs(num))` para el caso general (repr round-trip corto), y escala `×100` exacta vía `Decimal(str(abs(num))) * 100` con `format(d.normalize(), 'f')` para `percent_scale` (única operación aritmética del formateo).
**When to use:** Formateo de presentación; el flujo de signo/paréntesis/miles no cambia (operaciones sobre el texto ya producido).

### Anti-Patterns to Avoid

- **Multiplicar percent en float y formatear con `str()`:** `str(0.07 * 100)` → `'7.000000000000001'` — regresión vs. el `'7%'` actual. Verificado. Requiere la escala Decimal.
- **Recortar antes de prefijar en `sanitize_csv`:** D-09 exige prefijar el valor ORIGINAL (`"' =1+1"`, no `"'=1+1"`). El código actual ya lo hace — **no tocarlo**.
- **Usar `value.lstrip()` solo (sin BOM):** `'\ufeff=1+1'.lstrip()` devuelve `'\ufeff=1+1'` (BOM no es whitespace para CPython) — el check seguiría roto. Verificado. `[VERIFIED: probe]`
- **Capturar/fallback el error de total inexistente:** Convención del proyecto: raise, no fallback (CONTEXT §code_context). D-05/D-06 exigen error ruidoso.
- **Mover `order_by` a otro sitio:** El fix se hace en `_sort_key`/`_apply_order`; nada de tocar `Section.order_by` (117-138) ni `GroupSpec.order_by` — solo almacenan el dict.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Representación decimal corta de floats | Formateo manual con `%f`/`.10g`/`.17g` | `str()`/`repr()` nativo | Es el algoritmo canónico de repr corto round-trip de CPython (estable desde 3.1); cualquier reimplementación introduce cutoffs o artefactos. |
| Escala exacta ×100 sin artefactos binarios | `num * 100` en float + redondeo manual | `decimal.Decimal` (stdlib) | `0.07*100 == 7.000000000000001` (verificado); `round()` recupera `.0` espurio. Decimal+normalize+`format('f')` es correcto y ya está importado. |
| Detección de whitespace/BOM inicial | Chequeo manual del primer byte | `str.lstrip()` + regex `^[\s\ufeff]+` (stdlib) | El bypass por primer-byte es exactamente la vulnerabilidad (GHSA-xrwp-2gph-985x); el recorte estándar de stdlib cubre todo el whitespace Unicode en cualquier orden. |
| Fix de ordenamiento con funciones | Reescribir el evaluador o duplicar el contexto | Thread `report._functions` (patrón existente) | El patrón ya existe en `aggregation.py:102,174`; `_sort_key` es el único sitio divergente. |

**Key insight:** Ninguno de estos problemas es nuevo en el dominio — son correcciones de código existente usando stdlib. La fase no introduce una sola dependencia nueva; el riesgo está en no romper comportamiento actual (percent `'7%'`) y en no introducir regresiones de formato (ver Pitfalls).

## Runtime State Inventory

> Fase de corrección + eliminación de dependencia: no hay renames de strings en datos, pero DEP-01 toca estado de build/instalación y referencias documentales.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None** — el paquete es stateless (sin BD, sin estado runtime; verificado en STACK.md "no env-var-driven config"). | none |
| Live service config | **None** — no hay servicios con configuración externa; publish usa `uv build` (CI, no afectado). `[VERIFIED: publish.yml]` | none |
| OS-registered state | N/A — librería Python sin servicios registrados. | none |
| Secrets/env vars | **None** — el proyecto no usa variables de entorno. | none |
| Build artifacts | `uv.lock` (líneas 315-337, 362): declara `encino-orm` como dependencia y `requires-dist`. | **Regenerar con `uv lock`** (podará encino-orm + aiomysql/aiosqlite/asyncpg/async-timeout/pymysql); luego `uv sync` para podar el `.venv` local. `[VERIFIED: uv.lock]` |
| Build artifacts (históricos) | `dist/encino_rpt-0.2.0.whl` (gitignored) todavía arrastra la dependencia. | **Ninguna** — artefacto histórico; el próximo `uv build` no la incluirá. |
| Docs generadas por GSD | `.planning/codebase/STACK.md:27,47`, `.planning/codebase/INTEGRATIONS.md:10,15`, `AGENTS.md` (derivado) describen `encino-orm` como dependencia declarada. | Quedan obsoletas tras el fix; son snapshots de análisis con marcadores GSD — **regenerar/ignorar** (no editarlas a mano; se refrescan con el próximo escaneo). |
| Docs de usuario | `README.md:3-4`, `docs/index.md:4` mencionan "la salida de `fetch_all`/`fetch_many`/`paginate`" (forma de los datos, no la dependencia); `docs/design/10-report.md` §10/§12 ya dicen "opcional"/"cero dependencias". | **Audit + opcional** re-fraseo neutro a "salida de consultas ya materializadas (`list[dict]`)" para evitar cualquier implicación de dependencia (ver Open Questions). |

## Common Pitfalls

### Pitfall 1: Artefacto binario en `percent_scale` con `decimals=None`
**What goes wrong:** `str(0.07 * 100)` → `'7.000000000000001'`; el formato actual emite `'7%'`. Una implementación ingenua de D-01 rompe el percentaje.
**Why it happens:** `0.07 * 100` en punto flotante binario da `7.000000000000001`; `:g` ocultaba el artefacto por redondeo a 6 sig. dígitos.
**How to avoid:** Escala vía `Decimal(str(abs(num))) * 100` + `format(d.normalize(), 'f')` — verificado: `0.07→'7'`, `0.29→'29'`, `0.256→'25.6'`, `0.1→'10'`. `[VERIFIED: probe]`
**Warning signs:** Test de regresión que afirme `format_value(0.07, Format(kind="percent", percent_scale=True)) == "7%"`.

### Pitfall 2: BOM `\ufeff` NO es whitespace para `str.lstrip()`
**What goes wrong:** `'\ufeff=1+1'.lstrip()` → `'\ufeff=1+1'` (sin recorte) — implementación con solo `lstrip()` deja el bypass BOM abierto.
**Why it happens:** `'\ufeff'.isspace()` → `False` (verificado); el BOM no está en el set de whitespace de CPython.
**How to avoid:** Regex `^[\s\ufeff]+` (recorta whitespace y BOM en cualquier orden, incl. `' \ufeff =1+1'`, `'\ufeff\t=1+1'` — todos verificados) o tres lstrips encadenados.
**Warning signs:** Test SEC-02 con BOM: `is_dangerous('\ufeff=1+1') == True` y `"'\ufeff=1+1"` en CSV.

### Pitfall 3: Cambio de formato visible en floats enteros (`.0`)
**What goes wrong:** Con `decimals=None` y `Format()`, `format_value(2.0, Format())` pasa de `'2'` (`:g`) a `'2.0'` (`str`). Es el comportamiento decidido en D-01 (repr round-trip), no un bug.
**Why it happens:** `repr(2.0)` es `'2.0'` — un float 2.0 es distinto de int 2.
**How to avoid:** Documentar; no "arreglar" con redondeo. Los tests existentes no dependen de este caso (`test_format_value_number` usa `decimals=2` o `fmt=None`).
**Warning signs:** Reviewer que considere `.0` una regresión.

### Pitfall 4: `raise` dentro del key de `sorted()`
**What goes wrong:** Si el error se lanzara fuera del key (p. ej. pre-validando solo el primer hijo), no se cumpliría D-06 ("error en el primer hijo faltante").
**Why it happens:** `sorted()` evalúa el key de cada elemento ANTES de comparar; el raise en `_sort_key` para el primer hijo sin el total propaga naturalmente (D-06 ✓).
**How to avoid:** El raise debe estar en el branch `total` de `_sort_key`, con el nombre del total y contexto del hijo (ver Code Examples). Nota: si el total existe pero su `value` es `None` (p. ej. avg sin filas), el TypeError persiste — fuera del alcance de D-05 (el total no es "inexistente"; ver Open Questions).
**Warning signs:** Test CORR-05 con `pytest.raises(ValueError, match="total de orden inexistente")`.

### Pitfall 5: `_add_thousands` ante notación científica
**What goes wrong:** `int('1e+16')` lanza `ValueError` → el fallback devuelve `'1e+16'` sin separador de miles. No rompe, pero el separador no aplica a magnitudes extremas.
**Why it happens:** El try/except existente (`_format.py:44-47`) ya cubre esto.
**How to avoid:** Aceptar (alineado con D-02: sci permitida en extremos). Verificado: `_add_thousands('1234567.89')` → `'1,234,567.89'` ✓ (D-03), `_add_thousands('1e+16')` → `'1e+16'` ✓, `_add_thousands(str(10**20))` → `'100,000,000,000,000,000,000'` ✓.
**Warning signs:** Test CORR-02 que afirme el miles con precisión completa.

### Pitfall 6: Regeneración de `uv.lock` con efectos colaterales
**What goes wrong:** `uv lock` podría tocar más de lo esperado por versiones flotantes (`pydantic>=2`).
**Why it happens:** El lock resuelve el grafo completo; al quitar encino-orm se podan exactamente `encino-orm`, `aiomysql`, `aiosqlite`, `asyncpg`, `async-timeout`, `pymysql` (verificado contra el listado de paquetes — el resto es compartido con mkdocs/dev).
**How to avoid:** Revisar el `git diff uv.lock` tras `uv lock`; esperar solo esas 6 entradas + el `requires-dist` de `encino-rpt`. Ejecutar `uv sync` después para podar el venv y confirmar `uv run pytest` sigue verde.
**Warning signs:** Diff del lock con paquetes no relacionados (mkdocs, pytest, etc.).

### Pitfall 7: `order_by(expression=...)` sobre hijos `Detail`
**What goes wrong:** Para hijos `Detail`, `getattr(child, "_first_row", {})` es `{}` → la expresión evaluada contra fila vacía lanza `ExpressionError` si referencia campos.
**Why it happens:** Solo los `Group` reciben `_first_row` (aggregation.py:212,241); los `Detail` no. Es diseño pre-existente (order_by por expresión ordena GRUPOS por su primera fila + funciones).
**How to avoid:** Fuera de alcance (D-04 solo pide funciones custom). El test de CORR-04 debe ordenar por `expression=` sobre hijos de tipo `Group`.
**Warning signs:** Test CORR-04 que use un reporte sin grupos (hijos Detail) — se espera el comportamiento pre-existente.

### Pitfall 8: Falsos positivos del sanitizer con negativos
**What goes wrong:** `sanitize_csv("-123")` ya produce `"'-123"` hoy (el prefijo `-` está en `_DANGEROUS_PREFIXES`); el widen no cambia este caso pero un test podría asumir que "los negativos no se tocan".
**Why it happens:** OWASP lista `-` como prefijo peligroso; el comportamiento es pre-existente y consistente.
**How to avoid:** No modificar `_DANGEROUS_PREFIXES`; no escribir tests que afirmen negativos sin prefijo en CSV. Verificado: CSV actual `A,'-123`.
**Warning signs:** Test SEC-02 que afirme `sanitize_csv("-123") == "-123"`.

## Code Examples

Patrones verificados (probes ejecutadas el 2026-09-16 contra Python 3.11/3.14):

### 1. `format_value` — branch de precisión (CORR-02 + D-03)
```python
# encino_rpt/renderers/_format.py — dentro de format_value (reemplaza líneas 23-29)
if fmt.decimals is not None:
    num = value
    if fmt.percent_scale:
        num = num * 100
    text = f"{abs(num):.{fmt.decimals}f}"
elif fmt.percent_scale:
    # escala exacta sin artefactos binarios: 0.07*100 -> "7", nunca "7.000000000000001"
    d = (Decimal(str(abs(value))) * 100).normalize()
    text = format(d, "f")
else:
    # repr round-trip corto; sci solo en |num|>=1e16 o <1e-4 (D-02)
    text = str(abs(value))
# ... el resto (thousands, %, symbol, negative) NO cambia
```
Resultados verificados `[VERIFIED: probe]`: `format_value(1234567.89, Format())` → `'1234567.89'`; con `thousands=True` → `'1,234,567.89'`; `0.07` percent → `'7%'`; `0.29` → `'29%'`; `0.256` → `'25.6%'`; `-1234567.89` con `$`+miles+paren → `'($1,234,567.89)'`; `10**20` con miles → `'100,000,000,000,000,000,000'`; `1e16` → `'1e+16'` (sci aceptado); `0.00001` → `'1e-05'` (sci aceptado).

### 2. `is_dangerous` — recorte whitespace + BOM (SEC-02)
```python
# encino_rpt/renderers/_sanitize.py — reemplaza is_dangerous (líneas 8-10)
import re

_LEADING_TRIM = re.compile(r"^[\s\ufeff]+")

def is_dangerous(value) -> bool:
    """True si Excel/Calc podría tratar `value` como fórmula tras ignorar espacios/BOM iniciales."""
    return isinstance(value, str) and _LEADING_TRIM.sub("", value).startswith(_DANGEROUS_PREFIXES)
```
Verificado end-to-end `[VERIFIED: probe]` — con solo este cambio:
- `sanitize_csv(" =1+1")` → `"' =1+1"` (valor original verbatim + prefijo, D-09)
- `sanitize_csv("\ufeff@evil")` → `"'\ufeff@evil"`
- Excel: `write_excel_cell` fija `data_type='s'` para ambos (D-08, sin cambios en `write_excel_cell`)
- `is_dangerous('\x0c=1+1')` → `True` (form feed); `is_dangerous('normal')` → `False`

### 3. `_sort_key` — threading de funciones + error de total ausente (CORR-04/CORR-05)
```python
# encino_rpt/aggregation.py
def _apply_order(spec, children, functions):
    if spec.order_by:
        ob = spec.order_by
        reverse = ob.get("direction") == "desc"
        children = sorted(children, key=lambda c: _sort_key(c, ob, functions), reverse=reverse)
    # ... suppress_zero / top_n sin cambios

def _sort_key(child, ob, functions):
    total = ob.get("total")
    expression = ob.get("expression")
    column = ob.get("column")
    if total:
        for t in getattr(child, "totals", []):
            if t.name == total:
                return t.value
        child_desc = getattr(child, "name", None) or getattr(child, "key", None)
        raise ValueError(f"total de orden inexistente: {total!r} (hijo {child_desc!r})")
    if expression:
        return evaluate(expression, getattr(child, "_first_row", {}), functions)   # era {}
    # ... column / 0 sin cambios

# call site (aggregation.py:260) — _build_instance ya recibe `report`:
node.children = _apply_order(spec, node.children, report._functions)
```
`Decimal` ya está importado en `_format.py:6`; `re` se añade en `_sanitize.py`. El import de `evaluate` ya existe en `aggregation.py:7`.

### 4. Behavior actual del evaluador (referencia para CORR-04)
```python
# D-04 NO inyecta TOTAL() en el contexto de orden (LOCKED): el dict de funciones
# que recibe _sort_key es report._functions solamente.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `f"{abs(num):g}"` (6 sig. dígitos, sci prematura) | `str(num)` — repr round-trip corto (D-01) | Esta fase (CORR-02) | Precisión completa en números grandes; `.0` visible en floats enteros; sci solo en extremos (D-02). |
| Escala percent en float (`num * 100`) | Escala vía `Decimal` con `decimals=None` (Corrección de D-03) | Esta fase (CORR-02) | Elimina el artefacto binario `7.000000000000001%`; el resto del flujo (miles/símbolo/paren) no cambia. |
| Sanitizer de primer byte (`value.startswith(...)`) | Sanitizer post-recorte (`^[\s\ufeff]+`) (D-07) | Esta fase (SEC-02) | Cierra el bypass por espacio/BOM/control (`" =1+1"`, `"\x0c=1+1"`) — la misma clase de vulnerabilidad que GHSA-xrwp-2gph-985x (EspoCRM, 2026-07) documenta. |
| `evaluate(expr, row, {})` en `_sort_key` | `evaluate(expr, row, report._functions)` (D-04) | Esta fase (CORR-04) | Alinea el único sitio divergente con los otros 3 sites; `order_by(expression=...)` soporta funciones custom. |
| `return None` en total ausente → `TypeError` crudo | `raise ValueError` nombrando el total (D-05/D-06) | Esta fase (CORR-05) | Error claro en español con contexto del hijo, en tiempo de `run()`. |
| `encino-orm` como dependencia runtime declarada | Solo `pydantic>=2` (D-10) | Esta fase (DEP-01) | Instalación limpia; se podan 6 paquetes del lock; el contrato `list[dict]` no cambia. |

**Deprecated/outdated:**
- `f"{num:g}"` para `decimals=None`: cutoff a 6 sig. dígitos y sci prematura — reemplazado por `str()`.
- Chequeo de primer byte en `is_dangerous`: insuficiente contra whitespace/BOM inicial — reemplazado por chequeo post-recorte.
- `encino-orm` como dependencia runtime: muerta (0 imports) — eliminada.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `str(float)` produce los mismos umbrales de notación científica en toda la matriz CI (3.10-3.13) que en los pythons locales probados (3.11, 3.14) | Standard Stack / Pitfall 1 | Bajo — el algoritmo de repr corto es estable desde Python 3.1 `[CITED: docs.python.org repr round-trip, conocimiento de formación]`; el CI lo confirmará. |
| A2 | El mensaje de error CORR-05 puede incluir contexto del hijo además del nombre del total (DISCUSSION-LOG lo pide; D-05 da el estilo base) | Code Examples | Bajo — el requisito funcional es "nombra el total y es claro, en español, con `!r`"; el formato exacto es discreción de implementación. |
| A3 | Alcance de la limpieza documental DEP-01: README/index.md solo necesitan audit (no nombran la dependencia); `docs/design/10-report.md` §10/§12 se conservan (ya dicen "opcional"/"cero dependencias"); los `.planning/codebase/*.md` + AGENTS.md se regeneran, no se editan a mano | Runtime State Inventory / Open Questions | Medio — si el usuario espera re-fraseo literal de README ("salida de `fetch_all`..."), el plan debe incluirlo; si se editan los snapshots GSD, se rompe la convención de regeneración. Confirmar en planificación. |
| A4 | El `data_type='s'` de openpyxl es mitigación suficiente para valores con espacio/BOM inicial en Excel (la misma clase de bypass que en CSV) | Summary / SEC-02 | Bajo — OWASP advierte que no hay estrategia universal; el comportamiento verificado (celda como texto) es el control estándar del proyecto y el decidido (D-08). |
| A5 | Los prefijos `\t` y `\r` en `_DANGEROUS_PREFIXES` quedan redundantes tras el recorte (un valor `"\t=1+1"` se detecta por el `=` post-recorte), pero mantenerlos es inofensivo | Code Examples | Bajo — solo afecta legibilidad; no cambiar el tuple minimiza el diff y conserva la lista OWASP documentada. |
| A6 | `format_value` con `Decimal('nan')`/`Decimal('Infinity')` en el camino percent podría lanzar `decimal.InvalidOperation` | Common Pitfalls | Muy bajo — valores no-finitos en reportes financieros; si ocurre, fallback `str()` cubre (puede quedar como nota). |

## Open Questions

1. **Alcance exacto de la limpieza documental en DEP-01 (A3)**
   - What we know: No hay doc de usuario que declare a `encino-orm` como dependencia; el diseño §10/§12 es explícito en "opcional/cero dependencias"; README/index.md referencian `fetch_all`/`paginate` como forma de los datos.
   - What's unclear: ¿El usuario quiere re-fraseo neutro de esas menciones ("salida de consultas ya materializadas") o basta el audit?
   - Recommendation: El plan debe incluir el audit + un micro-edit opcional de README/index.md con fraseo neutro; dejar `docs/design/10-report.md` intacto (es el contrato de diseño); NO editar los snapshots GSD a mano.
2. **Total declarado pero con `value=None` en `order_by(total=...)`**
   - What we know: D-05 cubre "total inexistente"; un total declarado con `value=None` (p. ej. `avg` sin filas) seguiría produciendo `TypeError` en la comparación de `sorted()`. `[VERIFIED: code read]`
   - What's unclear: ¿Se considera "inexistente" (cubierto por la política ruidosa) o queda fuera de alcance?
   - Recommendation: Interpretar D-05 literalmente (nombre sin match); documentar el caso None-value como limitación conocida y candidata a Phase 3 (CORR-06 errores con contexto). No ampliar el fix sin confirmación.
3. **comportamiento esperado del `.0` en floats enteros (Pitfall 3)**
   - What we know: `format_value(2.0, Format())` pasará de `'2'` a `'2.0'` (consecuencia directa de D-01).
   - What's unclear: Si algún usuario de la librería depende del `'2'` sin sufijo.
   - Recommendation: Aceptar (decisión D-01 es explícita); añadir un test que documente el nuevo comportamiento como intencional.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.14.7 (sistema), 3.11.13 (venv uv) | — |
| uv | Lock sync (`uv lock`/`uv sync`) | ✓ | 0.8.22 | pip + manual lock no aplica (proyecto usa uv) |
| pytest | Suite de tests | ✓ | 9.1.1 | — |
| ruff | Lint CI (`uv run ruff check`) | ✓ | 0.16.7 (vía uv run) | no está en PATH global — usar `uv run ruff` |
| openpyxl | Extra `excel` (tests Excel) | ✓ | 3.1.5 | — |
| reportlab | Extra `pdf` (tests PDF) | ✓ | 5.0.1 | — |
| pydantic | Runtime | ✓ | 2.13.5 | — |
| mkdocs | Docs build (NO requiere esta fase) | ✓ (grupo docs) | 1.6.1 | la fase solo edita markdown; no se construye el sitio |
| encino-orm | Nada (se elimina) | — | — | DEP-01: `uv lock && uv sync` lo poda |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** `ruff` fuera del PATH global — usar `uv run ruff check` (como hace CI).

## Validation Architecture

> `workflow.nyquist_validation: true` en `.planning/config.json` — sección requerida.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (dev, pin en `uv.lock`) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["."]`) |
| Quick run command | `uv run pytest -q` (suite actual: 32 tests, 0.37s) |
| Full suite command | `uv run pytest` + `uv run ruff check` (igual que CI) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CORR-02 | `format_value(1234567.89, Format()) == "1234567.89"`; miles `"1,234,567.89"`; percent `"7%"`/`"29%"`/`"25.6%"`; sci en extremos `'1e+16'`/`'1e-05'` | unit | `uv run pytest tests/test_report_renderers.py -x` | ❌ nuevo test (pendiente de implementación) |
| CORR-04 | `order_by(expression="doblado(monto)")` con `add_function("doblado", ...)` ordena sin `ExpressionError` | unit | `uv run pytest tests/test_report.py -x` | ❌ nuevo test |
| CORR-05 | `order_by(total="inexistente")` → `pytest.raises(ValueError, match="total de orden inexistente")` | unit | `uv run pytest tests/test_report.py -x` | ❌ nuevo test |
| SEC-02 | `sanitize_csv(" =1+1") == "' =1+1"`; `"\ufeff=1+1"` saneado; Excel `data_type=='s'` con espacio/BOM (guard `pytest.importorskip("openpyxl")`) | unit | `uv run pytest tests/test_security.py -x` | ❌ nuevo test (banner `# --- P5: ... ---` por convención TESTING.md) |
| DEP-01 | `uv lock` regenera; `grep encino-orm pyproject.toml uv.lock` → sin matches; `uv run pytest` verde tras `uv sync` | smoke/CI | no-test (verificación de comando) | — |

### Sampling Rate
- **Per task commit:** `uv run pytest -q` (suite completa < 1s; corriendo los 3 archivos basta para la fase)
- **Per wave merge:** `uv run pytest && uv run ruff check`
- **Phase gate:** Suite completa verde + `ruff check` limpio antes de `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_report_renderers.py` — añadir tests de precisión CORR-02 (sin infraestructura nueva: mismo patrón `assert format_value(...)`)
- [ ] `tests/test_report.py` — añadir tests order_by CORR-04/CORR-05 (patrón `pytest.raises(ValueError, ...)` ya usado)
- [ ] `tests/test_security.py` — añadir banner `# --- P5: inyección de fórmulas con espacio/BOM ---` con los casos SEC-02
- [ ] No se requiere conftest, fixtures ni plugins — la infraestructura existente cubre todo (TESTING.md: convención sin fixtures, `importorskip` para openpyxl)

## Security Domain

> `security_enforcement` no está deshabilitado en config — sección requerida.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A — librería, sin sesiones de usuario |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation / Output Encoding | **sí** | Sanitización de inyección de fórmulas (CWE-1236): `is_dangerous` + prefijo `'` (CSV) / `data_type='s'` (Excel) — extendido en esta fase a whitespace/BOM inicial; control ya existente en `_sanitize.py` |
| V6 Cryptography | no | N/A |

### Known Threat Patterns for {stack}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Inyección de fórmulas en CSV/XLSX (CWE-1236) con prefijos `= + - @` | Tampering / ejecución en la máquina del usuario (DDE/gadgets en Excel legacy) | Detección post-recorte de whitespace/BOM (D-07, regex `^[\s\ufeff]+`); prefijo `'` sobre el valor original (D-09); tipo de celda forzado a texto en Excel (D-08). Clase de bypass documentada en GHSA-xrwp-2gph-985x (EspoCRM, 2026-07) y OWASP CSV Injection. `[CITED: GHSA-xrwp-2gph-985x, owasp.org/www-community/attacks/CSV_Injection]` |
| Bypass por leading whitespace/control (`" =1+1"`, `"\t=1+1"`, `"\x0c=1+1"`) — Excel recorta whitespace antes de decidir si es fórmula | Tampering | Recorte estándar stdlib antes del chequeo; verificado para espacio, tab, form feed y BOM. `[VERIFIED: probe]` |
| Falsos positivos en negativos (`-123` → `'-123` en CSV) | Disponibilidad (usabilidad) | Comportamiento pre-existente y consistente con la lista OWASP; no se modifica en esta fase (Pitfall 8). |
| DoS del evaluador (exponentes/nesting) | DoS | Fuera de alcance (Phase 3, SEC-04); los guards `_MAX_*` existentes no se tocan. |

## Sources

### Primary (HIGH confidence)
- **Código fuente verificado por lectura directa:** `encino_rpt/aggregation.py` (277-307, 102, 174, 260), `encino_rpt/renderers/_format.py` (23-29, 42-48), `encino_rpt/renderers/_sanitize.py` (5-27), `encino_rpt/renderers/csv.py`, `encino_rpt/renderers/excel.py`, `encino_rpt/section.py` (117-138), `encino_rpt/models.py` (Format), `pyproject.toml`, `uv.lock`, `.github/workflows/*.yml` — topics: call sites, firmas, estado actual.
- **Probes de ejecución (2026-09-16, Python 3.11.13/3.14.7):** reproducción de los 5 bugs; umbrales de sci de `str()`; comportamiento de `lstrip()` con BOM; POC completo de `format_value` con escala Decimal; POC end-to-end del sanitizer ampliado por monkeypatch (CSV + Excel); `_add_thousands` con precisión completa; suite actual 32 tests verdes.
- **Contexto del proyecto:** `.planning/phases/01-quick-wins-correcci-n-low-risk/01-CONTEXT.md` (decisiones D-01..D-10), `01-DISCUSSION-LOG.md`, `.planning/codebase/CONCERNS.md` (Known Bugs/Security), `.planning/codebase/TESTING.md` (convenciones de test), `.planning/ROADMAP.md` (success criteria).

### Secondary (MEDIUM confidence)
- **OWASP CSV Injection** — `https://owasp.org/www-community/attacks/CSV_Injection` — prefijos peligrosos `= + - @` + tab/CR/LF y mitigación estándar (prefijo `'`); advertencia de que no hay estrategia universal. `[CITED: owasp.org, verificado 2026-09-16 vía WebSearch]`
- **GitHub Security Advisory GHSA-xrwp-2gph-985x** (EspoCRM, publicado 2026-07-14) — documenta el bypass por whitespace/control de primer byte y el fix "recortar antes de chequear + prefijar el valor original", idéntico a D-07/D-09. `[CITED: github.com/espocrm/espocrm/security/advisories, verificado 2026-09-16 vía WebSearch]`

### Tertiary (LOW confidence)
- Ninguna claim crítica depende de fuentes terciarias.

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — no hay librerías nuevas; la única "elección" (str/Decimal/re) está verificada por probes en los pythons relevantes.
- Architecture: **HIGH** — call sites únicos verificados por grep; el fix de sanitizer fue probado end-to-end; el POC de format_value produce los outputs exactos que exige ROADMAP.
- Pitfalls: **HIGH** — los 8 pitfalls están reproducidos o deducidos de código leído línea a línea (los 3 críticos — artifact percent, BOM, propagación del raise — verificados por ejecución).

**Research date:** 2026-09-16
**Valid until:** 2026-10-16 (código estable, sin dependencias en movimiento; los hallazgos de stdlib de CPython son estables)