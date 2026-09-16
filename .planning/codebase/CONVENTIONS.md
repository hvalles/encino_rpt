# Coding Conventions

**Analysis Date:** 2026-09-16

## Overview

Single-package Python library (`encino_rpt`) implementing a fluent report builder
over `list[dict]` rows. Code is written in **Spanish** (module docstrings, class
docstrings, comments, and error messages), with **English** identifiers for code
symbols except in test/sample data. All modules start with `from __future__
import annotations`.

## Naming Patterns

**Files:**
- `snake_case.py` for modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`
- Leading-underscore for internal modules: `_specs.py` (builder dataclasses), `renderers/_format.py`, `renderers/_sanitize.py`
- Leading-underscore for internal helpers: `renderers/_format.py`, `renderers/_sanitize.py`
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`

**Classes:**
- PascalCase: `Report`, `Section`, `ReportResult`, `Group`, `HtmlRenderer`, `FieldSpec`, `ExpressionError`
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `PdfRenderer`, `TextRenderer` (in `encino_rpt/renderers/`)
- Spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (in `encino_rpt/_specs.py`)

**Functions:**
- `snake_case`: `add_function`, `build_chart`, `format_value`, `sanitize_csv`, `evaluate`
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_apply_order`, `_compute_totals_into`, `_enrich`, `_esc`, `_walk`
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the only cross-module abbreviations

**Variables:**
- `snake_case`: `rows`, `visible_set`, `child_pairs`, `deferred`
- Private instance attributes prefixed `_` and set in `__init__`:
  `self._rows`, `self._fields`, `self._groups`, `self._formats` (`encino_rpt/report.py`),
  `self._spec` (`encino_rpt/section.py`), `self._ws`, `self._row` (`encino_rpt/renderers/excel.py`)
- Pydantic `PrivateAttr` for non-serialized context: `_first_row`, `_header_tpl`, `_footer_tpl` (`encino_rpt/models.py:124-126`)

**Constants:**
- `UPPER_SNAKE`, module-level, usually private: `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`encino_rpt/expressions.py:45-47`), `_TOKEN` regex (`encino_rpt/template.py:7`), `_DANGEROUS_PREFIXES` (`encino_rpt/renderers/_sanitize.py:5`)
- Private module-level constant dicts map operator strings to lambdas: `_OPS`, `_COLOR_OPS` (`encino_rpt/renderers/excel.py:9`, `encino_rpt/renderers/html.py:11`), `_BINOPS`, `_UNARY`, `_CMP`, `_FUNCTIONS` (`encino_rpt/expressions.py:9-42`)

**Types:**
- Prefer `str | None` over `Optional[str]`; PEP 604 unions and builtin generics (`list[dict]`, `dict[str, Any]`) everywhere, enabled by `from __future__ import annotations`
- `Any` used for untyped row data: `dict[str, Any]`, `value: Any`, `format: Any`

## Code Style

**Formatting:**
- No formatter (no black/ruff-format) and **no ruff config section** — CI runs `uv run ruff check` with defaults (`.github/workflows/ci.yml:29-30`)
- One notable outlier: `encino_rpt/__init__.py` aligns import-list items to column 21 inside `from .models import (...)`; ruff does not flag it but it is inconsistent with `encino_rpt/renderers/__init__.py`, which uses one-item-per-line at 4-space indent

**Linting:**
- Ruff, installed as a dev dependency (`pyproject.toml:54`), version 0.16.7 in the lockfile
- Only rule set: ruff defaults. No `select`/`ignore` pinned. The suite is currently clean (verified `ruff check` exit 0)

**Imports:**
- Order: `from __future__ import annotations` first, blank line, then stdlib, blank line, third-party, blank line, relative imports. Examples:
  - `encino_rpt/report.py`: `from __future__` → `from typing import Any` → relative `from ._specs import ...`
  - `encino_rpt/aggregation.py`: `from __future__` → relative imports only (`.models`, `.pivot`, ...)
  - `encino_rpt/renderers/excel.py`: `from __future__` → `from ..models import ...` → `from ._format import ...`
  - `encino_rpt/expressions.py`: `import ast`, `import operator`, `from typing import Any` (stdlib group) — absolute stdlib first
- Small internal security helper imported into renderers: `from ._sanitize import sanitize_csv` (`encino_rpt/renderers/csv.py:10`)
- No path aliases; all intra-package imports are relative (`from .`, `from ..`, `from .renderers.`)

## Import Organization

**Order:**
1. `from __future__ import annotations` (every module, line 1 after the module docstring)
2. Standard library
3. Third-party (pydantic only, plus optional deps imported lazily — see Module Design)
4. Local relative imports

**Path Aliases:**
- None. Intra-package imports are always relative.

## Error Handling

**Custom exceptions:**
- Define domain exceptions as subclasses of builtins: `class ExpressionError(ValueError)` (`encino_rpt/expressions.py:50`)
- `ExpressionError` raised for unknown names, disallowed operators, too-complex/deep expressions, oversized exponents, keyword args on calls (`encino_rpt/expressions.py:59,65,73,77,81,87,93,101,104,106,108,109`)

**Raise patterns:**
- `ValueError` for invalid config values, always with a Spanish message including the offending value via `!r`:
  - `f"operador desconocido: {operator!r}"` (`encino_rpt/aggregation.py:45`)
  - `f"dirección de orden inválida: {direction!r}"` (`encino_rpt/section.py:131`)
  - `` "`columns` y `path` son excluyentes" `` (`encino_rpt/report.py:248`)
  - `f"índice de parámetro inválido: {token!r}"` (`encino_rpt/template.py:23`)
- `KeyError` for unknown named lookups: `f"corte no declarado: {name!r}"` (`encino_rpt/report.py:275`)
- `IndexError` for out-of-range param access: `f"parámetro {index} fuera de rango (hay {len(params)})"` (`encino_rpt/template.py:26`)
- Optional-dependency guards re-raise `ImportError` with `from exc` and a Spanish installation hint: `raise ImportError("openpyxl no está instalado; instala el extra `excel`") from exc` (`encino_rpt/renderers/excel.py:45`, `encino_rpt/renderers/pdf.py:40`)

**Do not:** wrap/return errors silently. Methods raise; the library never logs or swallows exceptions. There is no try/except anywhere in the codebase except the two optional-dependency guards.

## Logging

**Framework:** None. The library is silent — no `logging` module, no `print`. All failures surface as exceptions.

## Comments

**When to Comment:**
- Module docstring in every module (one line, Spanish): `"""Agregación: enriquece renglones, construye el árbol de grupos y resuelve totales."""` (`encino_rpt/aggregation.py:1`)
- Google-style docstrings (Spanish) on every public class and method with `Args:`, `Returns:`, `Raises:` sections — see `Report.group` (`encino_rpt/report.py:224-246`)
- Section banner comments inside longer modules: `# --- funciones / campos ---` (`encino_rpt/report.py:41`), `# --- árbol de grupos ---` (`encino_rpt/aggregation.py:116`), `# --- fase B ---` (`encino_rpt/aggregation.py:329`)
- Inline comments explain non-obvious invariants, in Spanish: `# None -> raíz (una sola partición)` (`encino_rpt/_specs.py:80`), `# children: subgrupos o detalle` (`encino_rpt/aggregation.py:245`), `# Contexto interno (no serializado)...` (`encino_rpt/models.py:123`)
- `# pragma: no cover - depende del entorno` on optional-dependency import guards (`encino_rpt/renderers/excel.py:44`, `encino_rpt/renderers/pdf.py:39`)
- Comments in source are Spanish; avoid English comments in new code.

**JSDoc/TSDoc:** n/a (Python). Use Google-style `Args:`/`Returns:`/`Raises:`.

## Function Design

**Size:** No hard cap, but single-responsibility private helpers are the norm; `aggregation.py` decomposes into 15+ small `_`-prefixed helpers (`_partition`, `_build_instance`, `_make_path_node`, ...) rather than one large function. `build()` (`encino_rpt/aggregation.py:381-406`) is the orchestration entry point and stays readable.

**Parameters:**
- Keyword-only args after the first positional(s), marked `*`: e.g. `def set_format(self, column: str, *, kind: str = "number", decimals: int | None = None, ...)` (`encino_rpt/report.py:68-72`)
- Optional params default to `None` and are stored/checked explicitly: `columns: str | None = None`, `title: str | None = None`
- `format=None` is the one place a shadowed builtin name is used as a parameter (avoids importing `Format` in the public builder API) — `encino_rpt/report.py:127`

**Return Values:**
- Fluent builder methods return `self` typed as the class: `-> Report` (`encino_rpt/report.py:42,55,68,...`), `-> Section` (`encino_rpt/section.py:14,26,40,...`)
- `Report.run()` returns the canonical `ReportResult` (`encino_rpt/report.py:278-286`), lazily importing `build`
- Renderers return plain data: `str` (`render_html`, `to_csv`, `to_text`), `Worksheet` (`to_excel`), `bytes` (`to_pdf`) — `encino_rpt/models.py:150-214`

## Module Design

**Exports:**
- Public API surface defined in `encino_rpt/__init__.py`: exports the models (`Chart`, `ConditionalRule`, ..., `Total`) and `Report` with an explicit `__all__`. Note `Section` is intentionally **not** exported (reachable via `Report.group()` / `Report.section()` return values).
- `encino_rpt/renderers/__init__.py` re-exports all five renderers with `__all__ = ["CsvRenderer", "ExcelRenderer", "HtmlRenderer", "PdfRenderer", "TextRenderer"]`.
- Internal modules (`_specs.py`, `aggregation.py`, `expressions.py`, `template.py`, `pivot.py`, `charts.py`, `renderers/_format.py`, `renderers/_sanitize.py`) are not exported.

**Barrel Files:** Exactly two: the two `__init__.py` files above.

**Layer separation:**
- Public fluent facade: `encino_rpt/report.py` (`Report`) + `encino_rpt/section.py` (`Section`) — mutate internal spec dataclasses
- Internal specs: `encino_rpt/_specs.py` (dataclasses, `field(default_factory=list)` for mutable defaults)
- Canonical output model: `encino_rpt/models.py` (pydantic `BaseModel`, `Field(default_factory=...)` for mutable defaults, `PrivateAttr` for non-serialized context, `Group.model_rebuild()` at module end for the recursive `children: list[Detail | Group | Chart | Pivot]` reference)
- Pipeline: `encino_rpt/aggregation.py` (build tree) → `encino_rpt/charts.py` / `encino_rpt/pivot.py` (extras) → `encino_rpt/expressions.py` (safe evaluator) / `encino_rpt/template.py` (`{{token}}` rendering)
- Renderers: `encino_rpt/renderers/` — each implements a `_walk` visitor over the canonical tree (visitor pattern per `encino_rpt/renderers/__init__.py:1`)

**Lazy imports (convention):**
- Optional extras imported inside methods, not at module top: `openpyxl` inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:42-44`), `reportlab` inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:30-39`), plus per-helper imports (`from openpyxl.styles import Font` inside `_full_row`, `encino_rpt/renderers/excel.py:126-127`)
- Even required internal modules are lazily imported to avoid cycles: `from .aggregation import build` inside `Report.run()` (`encino_rpt/report.py:284`), and `from .renderers.html import HtmlRenderer` inside `ReportResult.render_html` (`encino_rpt/models.py:160`)

**Cross-module data access (current convention, with caveats):**
- `aggregation.py` reaches into `Report` internals directly: `report._rows`, `report._datasets`, `report._fields`, `report._functions`, `report._groups`, `report._order` (`encino_rpt/aggregation.py:91,96,102,117-121,128,385-397`). This couples the pipeline to the builder's private state; new code should prefer adding accessor methods on `Report` if the coupling grows.

## Patterns to Follow

- Fluent builder: methods validate immediately (raise early) and return `self`
- "Truthiness coalescing" for label fallbacks: `label = t.label or t.name or t.operator` (`encino_rpt/renderers/excel.py:86`, also `html.py:58`, `csv.py:42`, `text.py:35`, `pdf.py:85`)
- Dict `or` fallback for user-supplied config: `self.styles = styles or {}`, `self.classes = classes or {}`
- Row access via `row.get(col)` with `None` fallbacks, never `row[col]`
- Module-level `_OPS`-style dispatch dicts instead of if/else chains for operator lookup
- Preserve insertion order explicitly where dicts don't: `_ordered_unique` (`encino_rpt/pivot.py:46-52`), `order` list parallel to `index` dict in `_partition` (`encino_rpt/aggregation.py:143-153`)

## Anti-Patterns

### No-op statement left in renderer

**What happens:** `self._row += 0` in `ExcelRenderer._chart` (`encino_rpt/renderers/excel.py:174`) — dead code under a `if not node.series:` guard.
**Why it's wrong:** Misleading; suggests the row counter changed when it did not.
**Do this instead:** Delete the line; the branch intentionally renders nothing and no adjustment is needed.

### `.__init__.py` import alignment

**What happens:** `encino_rpt/__init__.py` aligns the `from .models import (...)` items to column 21 with 21-space indents; `encino_rpt/renderers/__init__.py` uses standard 4-space indents.
**Why it's wrong:** Inconsistent; the aligned style is fragile when names grow.
**Do this instead:** Use the 4-space, one-name-per-line style from `encino_rpt/renderers/__init__.py`.

### Cross-module private attribute access

**What happens:** `encino_rpt/aggregation.py` reads `report._rows`, `report._fields`, etc. across module boundaries.
**Why it's wrong:** Brittle — any rename in the builder silently breaks the pipeline; the public surface (`ReportResult`) stays stable but the builder internals are effectively a second API.
**Do this instead:** If the coupling grows, add accessor methods (`report.row_sets()`, `report.field_specs()`) and keep `_`-prefixed attributes private to `report.py`.

## Cross-Cutting Conventions

**Spanish language:** module/class/method docstrings, comments, error messages, and test data values are Spanish. Keep new code consistent (e.g. error messages: `raise ValueError(f"operador desconocido: {operator!r}")`).

**Type hints:** mandatory on public signatures; `|` unions and builtin generics; `Any` for untyped row payloads. Internal helpers also hinted where cheap.

**Validation:** validate at declaration time (builder methods raise immediately), not at `run()` time — see `Report.group` columns/path exclusivity (`encino_rpt/report.py:247-248`) and `Section.order_by` direction check (`encino_rpt/section.py:130-131`).

---

*Convention analysis: 2026-09-16*