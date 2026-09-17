# Testing Patterns

**Analysis Date:** 2026-09-17

## Test Framework

**Runner:**
- **pytest** `9.1.1` (dev dependency group, `pyproject.toml:50`)
- Config: `pyproject.toml` `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = ["."]` (lines 44-46)
- No `pytest.ini`, `conftest.py`, `tox.ini`, or `setup.cfg` present.

**Assertion Library:**
- Plain `assert` statements — no `pytest` assertion helpers beyond `pytest.raises`.

**Run Commands:**
```bash
uv run pytest          # run all tests
uv run pytest -q       # quiet output
uv run pytest tests/test_report.py              # single file
uv run pytest tests/test_report.py::test_kpi    # single test
uv run pytest -x      # stop on first failure (fast feedback)
uv run ruff check     # lint (run alongside tests in CI)
```

## Test File Organization

**Location:**
- Flat `tests/` directory at repo root (no nested per-package layout). Three files total:
  - `tests/test_report.py` (437 lines) — expression evaluator, builder, aggregation, idempotency, errors, performance
  - `tests/test_report_renderers.py` (315 lines) — value formatting, all six renderers, links/images, layout, JSON round-trip
  - `tests/test_security.py` (151 lines) — formula injection, DoS limits, HTML/CSS style injection, template validation

**Naming:**
- Files: `test_<area>.py`
- Functions: `test_<behavior>` in `snake_case`, e.g. `test_phase_b_percentage`, `test_excel_formulas_no_double_count`, `test_expression_pow_limit`
- No test classes — all tests are module-level functions grouped by `# --- section ---` banner comments

**Structure:**
```
tests/
├── test_report.py            # engine + builder behavior
├── test_report_renderers.py  # renderers + formatting
└── test_security.py          # injection/DoS mitigations
```

**No fixtures:** there is no `conftest.py` and no `@pytest.fixture`. Each test is self-contained: it builds a local `rows` list-of-dicts inline and constructs a fresh `Report(rows)`.

## Test Structure

**Suite organization** — flat functions grouped by banner comments (Spanish):
```python
# --- evaluador de expresiones ---
def test_expression_arithmetic():
    row = {"cantidad": 3, "precio": 10}
    assert evaluate("cantidad * precio", row) == 30
```
(`tests/test_report.py:7-10`)

**Standard builder test shape** — build a `Report`, declare cuts/totals, `run()`, then assert on the canonical tree:
```python
def test_group_and_totals():
    rows = [
        {"agente": "Ana", "monto": 100},
        {"agente": "Ana", "monto": 50},
        {"agente": "Bob", "monto": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "monto")
    rep.group("global")
    rep.section("global").total("sum", "monto")
    result = rep.run()
    assert root.totals[0].value == 350
```
(`tests/test_report.py:63-85`)

**Exception assertion pattern** — `pytest.raises` with `match=` on the Spanish message (partial regex match):
```python
with pytest.raises(ValueError, match="total de orden inexistente: 'total_inexistente'"):
    rep.run()
```
(`tests/test_report.py:227-228`)

**Error-context assertions** — assert the wrapped message contains context:
```python
with pytest.raises(AggregationError, match="grupo 'global'"):
    rep.run()
```
(`tests/test_report.py:369-370`)

**Render-output assertions** — build the result, call the render method, assert on substring:
```python
html_out = result.render_html()
assert "<table>" in html_out
assert "color:red" in html_out
```
(`tests/test_report_renderers.py:88-91`)

## Mocking

**Framework:** None. No `unittest.mock`, no `pytest-mock`, no `monkeypatch`, no test doubles.

**Patterns:** Tests exercise the real library against small in-memory `rows` (`list[dict]`). No database or external service is ever touched — the input contract is already-materialized `list[dict]`.

**What to Mock (future guidance):** There is no established mocking convention. If a test ever needs to isolate a dependency, prefer `pytest.MonkeyPatch` or a lambda injected via the existing hooks (`Report.add_function(name, fn)` at `encino_rpt/report.py:42-53`, `Report.add_aggregate(name, fn)` at `encino_rpt/report.py:55-66`) rather than introducing a mocking framework.

**What NOT to Mock:**
- The canonical `ReportResult` tree — assert on real output (e.g. `result.root.totals[0].value`)
- `pydantic` models — build them directly (`Format(kind="currency", symbol="$", ...)` in `tests/test_report_renderers.py:9`)
- The expression evaluator — call `evaluate(...)` directly (`tests/test_report.py:8-38`)

## Fixtures and Factories

**Test Data:** inline list-of-dicts literals, declared at the top of each test:
```python
rows = [
    {"agente": "Ana", "monto": 100},
    {"agente": "Ana", "monto": 50},
    {"agente": "Bob", "monto": 200},
]
```

**Custom callbacks** for isolation/performance tests are defined as local closures:
```python
def value_fn(group):
    processed.append(len(group))
    return sum(r["v"] for r in group)

pivot = build_pivot(spec, rows, value_fn)
```
(`tests/test_report.py:404-409`)

**Location:** no shared fixtures/factories exist. Data lives in each test. If a shared builder helper is ever needed, put it in a `tests/conftest.py` fixture (currently absent) rather than importing across test modules.

## Coverage

**Requirements:** None enforced. There is no `pytest-cov`, no `--cov` invocation, no `.coveragerc`, and no CI coverage gate. `.gitignore` already excludes `.coverage` and `htmlcov/` (`.gitignore:19-20`).

**View Coverage (not currently configured):** install `pytest-cov` and run:
```bash
uv run pytest --cov=encino_rpt --cov-report=term-missing
```
Note this is a recommendation, not the existing convention.

## Test Types

**Unit Tests:**
- Scope: individual functions (`evaluate`, `format_value`, `sanitize_csv`, `render`, `build_pivot`, `is_dangerous`) and builder/engine behavior
- Approach: direct function calls and `Report(...).run()` assertions

**Integration Tests:**
- Scope: renderers consume the canonical tree end-to-end (`result.to_csv()`, `result.render_html()`, `result.to_excel()`, `result.to_pdf()`, `result.to_json()`)
- JSON round-trip verified: `ReportResult.model_validate(json.loads(result.to_json()))` (`tests/test_report_renderers.py:281-298`) and `model_dump()`/`model_validate()` (`tests/test_report.py:295-303`)

**Optional-dependency tests** guarded with `pytest.importorskip` (skip, not fail, when extra is missing):
```python
def test_excel_renderer():
    pytest.importorskip("openpyxl")
    ...
```
- `pytest.importorskip("openpyxl")` for Excel tests (`tests/test_report_renderers.py:95,112,129,157,193,232`; `tests/test_security.py:20,46,127,144`)
- `pytest.importorskip("reportlab")` for PDF (`tests/test_report_renderers.py:169`)

**E2E Tests:** Not used. No browser/selenium/Playwright tests; HTML/CSV/Excel/PDF output is asserted as strings/objects, not rendered.

## Common Patterns

**Security testing** (dedicated `tests/test_security.py`), grouped by mitigation ID:
- Formula injection: assert `result.to_csv()` prefixes dangerous cells with `'` (`tests/test_security.py:10-16`); assert Excel cells have `data_type == "s"` (`tests/test_security.py:19-28`)
- DoS limits: assert `evaluate` raises `ExpressionError` on oversized exponents/complexity (`tests/test_security.py:61-71,102-111`)
- HTML/CSS injection: assert injected style values are stripped from `render_html()` output (`tests/test_security.py:75-84,115-122`)

**Idempotency test** — assert two `run()` calls produce identical output:
```python
first = rep.run()
second = rep.run()
assert first.model_dump() == second.model_dump()
```
(`tests/test_report.py:332-342`)

**Performance/regression tests** — assert algorithmic behavior, not timing:
- Single-pass pivot: assert `value_fn` is called exactly `rows + nrows + ncols` times (`tests/test_report.py:393-415`)
- Deep `path` group without recursion: build a 1100-segment path and assert depth (`tests/test_report.py:418-436`, `tests/test_report_renderers.py:301-314`)

**Rounding/precision tests** — assert exact string output of `format_value` for floats, percentages, and scientific-notation thresholds (`tests/test_report_renderers.py:25-50`)

**Excel formula tests** — assert exact `=SUM(...)` strings, including that the global total does NOT double-count subtotal rows:
```python
assert "=SUM(B2:B3)" in formulas
assert "=SUM(B2:B6)" not in formulas
```
(`tests/test_report_renderers.py:128-153`)

**`pytest.fail` after a loop scan** when asserting "some cell matches":
```python
for row in ws.iter_rows():
    for cell in row:
        if cell.value == "=1+1":
            assert cell.data_type == "s"
            return
pytest.fail("no se encontró la celda de total")
```
(`tests/test_security.py:135-140`)

## CI

- `.github/workflows/ci.yml` runs `uv run pytest` and `uv run ruff check` on a Python matrix `["3.10", "3.11", "3.12", "3.13"]` (`ci.yml:11-30`)
- Dependencies installed with `uv sync --all-extras --group dev` — both optional extras (`openpyxl`, `reportlab`) are installed, so `importorskip` never skips in CI.

---

*Testing analysis: 2026-09-17*
