---
phase: 01-quick-wins-correcci-n-low-risk
reviewed: 2026-09-16T19:15:00Z
depth: deep
files_reviewed: 3
files_reviewed_list:
  - encino_rpt/renderers/_format.py
  - encino_rpt/renderers/_sanitize.py
  - encino_rpt/aggregation.py
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues
---

# Phase 01: Code Review Report

**Reviewed:** 2026-09-16T19:15:00Z
**Depth:** deep
**Files Reviewed:** 3
**Status:** issues

## Summary

Reviewed the phase-01 production diff (`git diff 1026557..HEAD -- encino_rpt/`): the `format_value` precision rework (CORR-02), the `is_dangerous` whitespace/BOM trim (SEC-02), and the `order_by` function-threading + missing-total ValueError (CORR-04/CORR-05). Plans 01-01/01-02/01-03 and their acceptance criteria were cross-checked; the test suite (43 passed) and `ruff check` are green; the three planned fixes are implemented faithfully and the acceptance criteria are met.

The CORR-02 and SEC-02 fixes are sound: `str(abs(value))` reproduces CPython's documented sci thresholds for floats (probed: `1e16 → "1e+16"`, `1e-5 → "1e-05"`, `2.0 → "2.0"`, negative-paren and thousands chains intact), the percent-`Decimal` path avoids the `0.07*100` binary artifact (probed `` `7%`/`29%`/`25.6%` ``), and the `^[\s\ufeff]+` trim closes the CWE-1236 whitespace/BOM bypass without dropping any previously-dangerous prefix (sweep of `\v/\f/\xa0/multi-BOM` all => `True`; bare-whitespace strings are now correctly non-dangerous). No `eval`, no AST changes, no new attack surface.

Two warnings remain, both in `aggregation.py` `_sort_key`: the CORR-05 raise has collateral crashes on previously-tolerated public-API inputs, and the adjacent `column` branch still leaks the same raw `TypeError` from `sorted()` that CORR-05 was meant to eliminate.

## Warnings

### WR-01: `order_by(total=...)` now crashes on children that structurally cannot carry the total, with an uninformative message

**File:** `encino_rpt/aggregation.py:298-299`
**Issue:** The new raise fires whenever *any* evaluated child lacks the total, not only on a typo'd total name. Two previously-tolerated (silent) usages of the public API now abort `run()`:

1. A section whose children are `Detail` rows — `rep.section("global").order_by(total="total_g")` where global's children are details (no groups): `Detail` has no `totals`, so every key evaluates to a raise. Old behavior: `sorted()` with all-`None` keys (stable no-op). Probed: `ValueError: total de orden inexistente: 'total_g' (hijo None)`.
2. Heterogeneous sibling groups where only some subgroups declare the ordered total: previously sorted with `None` key (children without the total sink to the end in `asc`), now hard-crashes. Probed: `ValueError: total de orden inexistente: 'total_agt' (hijo 'sin_total')`.

Additionally, for `Detail` children `child_desc` evaluates to `None` (no `name`/`key` fields), so the error message gives the user no context about which section or child is at fault. The plan locked D-06 (raise on first child lacking the total) and the regression test covers the typo case, but the detail-child and mixed-subgroup consequences were not analyzed and the message quality gap remains.

**Fix:**
```python
if total:
    for t in getattr(child, "totals", []):
        if t.name == total:
            return t.value
    if isinstance(child, Group):
        child_desc = child.name or repr(child.key)
    else:
        child_desc = f"renglón de detalle (sección sin totales)"
    raise ValueError(
        f"total de orden inexistente: {total!r} (hijo {child_desc!r}); "
        f"los renglones de detalle no tienen totales"
    )
```
(Or, if detail/no-total children should sort as before, return `None` for non-`Group` children and reserve the raise for `Group` children missing the total.)

### WR-02: `_sort_key` column branch still leaks the raw `TypeError` from `sorted()` that CORR-05 was meant to eliminate

**File:** `encino_rpt/aggregation.py:302-307`
**Issue:** The `column` branch of the *same modified function* still returns `None` for rows missing the column (`child.row.get(column)`), so `order_by(column=...)` over rows where one row lacks the column crashes with `TypeError: '<' not supported between instances of 'NoneType' and 'int'` — the exact raw-`TypeError` defect class the plan summary cites as fixed by CORR-05. The fix created an inconsistency inside one function: missing total => clear `ValueError`; missing column value => raw `TypeError`. Probed with rows `[{"agente": "Ana", "total": 100}, {"agente": "Bob"}]` + `order_by(column="total")`.

**Fix:**
```python
if column:
    if isinstance(child, Group):
        v = child.key.get(column) if child.key else None
    elif isinstance(child, Detail):
        v = child.row.get(column)
    else:
        v = None
    if v is None:
        raise ValueError(f"columna de orden inexistente: {column!r} (hijo {child_desc!r})")
    return v
```

## Info

### IN-01: percent_scale + decimals=None renders full fixed-point expansion at any magnitude

**File:** `encino_rpt/renderers/_format.py:28-31`
**Issue:** `format(d, "f")` never uses scientific notation, so percent values at extreme magnitudes produce unbounded fixed-point strings: probed `format_value(1e-300, Format(kind="percent", percent_scale=True))` → 301-character `"0.000…001%"` (old `:g` path gave `"1e-298%"`) and `1e20` → `"10000000000000000000000%"`. Harmless for realistic finance ranges, but the string length now grows linearly with the exponent magnitude.
**Fix:** Optional: clip magnitudes via the same sci-threshold logic as the non-percent branch (`if abs(d) >= 1e16 or abs(d) < 1e-4: text = str(d)` before the fixed expansion), or leave as documented behavior.

### IN-02: Inconsistent missing-total semantics between `_sort_key` and `_is_zero`

**File:** `encino_rpt/aggregation.py:314-318`
**Issue:** The phase-C block now treats a missing total as a hard error in `_sort_key` (raise) but `_is_zero` (used by `suppress_zero`) still silently returns `False` for a missing total, keeping the child. Same condition, opposite philosophies, in adjacent lines of the same block. Not changed in this phase, but worth aligning (e.g., a `suppress_zero(total=...)` on a typo'd name looks like a no-op instead of failing loudly per the project's raise-don't-silence convention).
**Fix:** Decide one policy for missing totals in phase C: either validate both `order_by(total=...)` and `suppress_zero(total=...)` up front in `Report.run()`/`build()`, or raise in both `_sort_key` and `_is_zero`.

---

## Verification notes (probes run)

- `format_value`: `1234567.89 → "1234567.89"`; thousands `"1,234,567.89"`; currency-paren `"($1,234,567.89)"`; `2.0 → "2.0"` (D-01); `1e16 → "1e+16"`, `1e-5 → "1e-05"` (D-02 thresholds preserved — both old `:g` and new `str()` use the same repr thresholds for floats); percent `7%/29%/25.6%`, negative percent `"-7%"`, `Decimal('1.10')` unchanged at `"1.10"`.
- `is_dangerous` sweep: `\v/\f/\ufeff/\xa0/multi-BOM` prefixes all detected; bare whitespace correctly non-dangerous; `=/- /@` unchanged; `sanitize_csv` prefixes the original value verbatim (D-09).
- `_apply_order`/`_sort_key`: single call site, signature threading consistent with the 4 canonical `report._functions` sites; `evaluate` does not mutate the dict (`{**_FUNCTIONS, **(functions or {})}`).
- Full suite: `uv run pytest -q` → 43 passed; `uv run ruff check` → clean.

---

_Reviewed: 2026-09-16T19:15:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_