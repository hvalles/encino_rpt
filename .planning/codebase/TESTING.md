# Testing Patterns

**Analysis Date:** 2026-09-17

## Test Framework

**Runner:**
- **pytest** `9.1.1` (dev group, `pyproject.toml:47`)
- Config: `[tool.pytest.ini_options]` (`pyproject.toml:41-43`): `testpaths = ["tests"]`, `pythonpath = ["."]`. No `addopts`, no custom markers registered.

**Assertion Library:**
- Plain `assert` statements (no `unittest` assertions, no pytest plugins like `pytest-check` or `pytest-approx`). Assertions use direct equality, `is True`/`is None`, `isinstance`, and substring `in` checks on rendered output.

**Coverage:**
- **pytest-cov** `7.1.0` (dev group, `pyproject.toml:52`), backed by **coverage** `7.16.1`.
- Config `[tool.coverage.run]`/`[tool.coverage.report]` (`pyproject.toml:77-84`): `source = ["encino_rpt"]`, `branch = false`, `fail_under = 80`, `show_missing = true`, `exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "if __name__ == .__main__.:"]`.
- Current: **129 tests passing, 91.13% coverage** (gate is 80%).

**Run Commands:**
```bash
uv run pytest                                          # Run all tests
uv run pytest tests/test_report.py                     # Run a single file
uv run pytest tests/test_report.py::test_group_and_totals  # Run a single test
uv run pytest -k "excel"                               # Keyword filter
uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80  # Coverage (CI)
```

There is no watch mode configured; `uv run pytest` is the standard invocation.

## Test File Organization

**Location:**
- Centralized in a single top-level `tests/` directory (no co-located `__init__.py`-less test dirs, no tests inside `encino_rpt/`).

**Naming:**
- Files: `tests/test_<area>.py`
- Functions: `test_<behavior>` — descriptive snake_case names describing the behavior under test (e.g. `test_order_by_missing_total_raises`, `test_csv_formula_injection`).
- Private test helpers prefixed `_`: `_streaming_report()`, `_chart_pivot_report()`, `_deep_dict(n)` (`tests/test_report_renderers.py:509,584,656`), and `_MiReader` (`tests/test_readers.py:128`).

**Structure:**
```
tests/
├── test_report.py            # builder, aggregation engine, expressions, models
├── test_report_renderers.py  # format_value + all 7 renderers, serialization round-trip
├── test_security.py          # formula injection, AST DoS, HTML/CSS injection, template param
├── test_readers.py           # multi-format readers (csv/tsv/json/jsonl/tuples/excel/custom)
└── test_perf_smoke.py        # wall-clock performance smoke gate (50k rows)
```

**Test file contents summary:**
- `tests/test_report.py` (584 lines) — expression evaluator, builder/aggregation, groups, totals, deferred `TOTAL(...)`, cumulative, charts/pivots, order/top/suppress, links/images, formats/styles, KPIs, roundtrip, path groups, idempotency, error context, multi-dataset regressions
- `tests/test_report_renderers.py` (706 lines) — `format_value` precision, all 7 renderers, streaming `iter_*` parity, `file=` writes, JSON versioning, deep-tree `RecursionError` handling, model `Literal` validation, Decimal/datetime serialization
- `tests/test_security.py` (189 lines) — CSV/Excel formula injection, leading-space/BOM sanitization, expression DoS limits (pow/complexity/float exponent/arithmetic), HTML/CSS injection, template param validation
- `tests/test_readers.py` (174 lines) — `_coerce` type detection, CSV/TSV/JSON/JSONL/tuples/excel readers, auto-detection, custom reader registration, missing-extra error
- `tests/test_perf_smoke.py` (31 lines) — 50k-row pivot build under a 10s wall-clock gate

## Test Structure

**Suite Organization:**
- No classes, no fixtures file, no `conftest.py`. Tests are flat module-level functions grouped by `# --- area ---` banner comments.

**Patterns (actual from `tests/test_report.py:42-60`):**
```python
# --- builder / agregación ---
def test_basic_report_and_hidden_fields():
    rows = [
        {"sku": "A", "cantidad": 2, "precio": 10.0},
        {"sku": "B", "cantidad": 1, "precio": 5.0},
    ]
    rep = Report(rows)
    rep.add_field("total", "cantidad * precio", after="precio")
    rep.add_field("es_doble", "IF(cantidad > 1)")  # oculto
    rep.detail("sku", "cantidad", "precio", "total")
    result = rep.run()

    assert result.columns == ["sku", "cantidad", "precio", "total"]
    assert result.root.name == "global"
    assert len(result.root.children) == 2
    assert result.root.children[0].row["total"] == 20.0
```

**Patterns:**
- **Arrange-Act-Assert**: build `rows = [...]` inline → declare the report via the fluent builder → `result = rep.run()` → assert on the canonical tree (`result.root`, `result.columns`, `result.formats`, `result.kpis`, etc.).
- **Inline test data**: `list[dict]` literals defined directly in each test (no shared fixtures/factories). Rows use realistic Spanish finance keys (`monto`, `agente`, `sku`, `total`, `cuenta`).
- **Comment banners** group tests by concern: `# --- evaluador de expresiones ---`, `# --- idempotencia ---`, `# --- errores con contexto ---`, `# --- rendimiento ---`, `# --- regresiones TEST-01 ---`.
- **Regression traceability**: inline comments reference ticket/PRD IDs — `# CORR-08`, `# CORR-11`, `# CORR-12`, `# TEST-01`, `# TMPL-01`, `# TMPL-02`, `# PRD-01`, `# P1`, `# P2`, `# JSON-01`, `# FEAT-02`.

## Mocking

**Framework:** No mocking library (`unittest.mock`/`mock`/`pytest-mock` are NOT used). Two native pytest mechanisms cover the only isolation needs:

**Patterns (actual from `tests/test_readers.py:160-163`):**
```python
def test_excel_missing_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "openpyxl", None)
    with pytest.raises(ImportError):
        read_rows("datos.xlsx", format="excel")
```

**Optional-dependency skipping (actual from `tests/test_security.py:19-20`):**
```python
def test_excel_formula_injection():
    pytest.importorskip("openpyxl")
    ...
```

**What to Mock:**
- Simulate a missing optional dependency by stubbing `sys.modules` with `monkeypatch.setitem(sys.modules, "openpyxl", None)` to assert the `ImportError` guard.

**What NOT to Mock:**
- The engine, renderers, models, and readers are never mocked — tests exercise the real implementation end-to-end (integration-style through the public `Report`/`ReportResult` API).
- Optional deps (`openpyxl`, `reportlab`) are NOT mocked; tests that need them use `pytest.importorskip` to skip gracefully when the extra is absent (they are installed in CI via `--all-extras`).

## Fixtures and Factories

**Test Data:**
- No `@pytest.fixture` definitions and no factory functions for report rows. Test data is inline `list[dict]` literals.

**Shared setup helpers** (private, non-fixture):
```python
# tests/test_report_renderers.py:509-515
def _streaming_report():
    rows = [{"sku": "A", "cantidad": 2}, {"sku": "B", "cantidad": 1}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    rep.group("global")
    rep.section("global").total("sum", "cantidad")
    return rep.run()
```

**Built-in pytest fixtures used:**
- `tmp_path` — for file-based reader tests (`tests/test_readers.py:36`, `tests/test_readers.py:143`)
- `monkeypatch` — for `sys.modules` stubbing (`tests/test_readers.py:160`)

**Location:** All helper functions live in the same test file they serve; there is no `conftest.py` and no `tests/fixtures/` directory.

## Coverage

**Requirements:**
- Enforced gate: ≥80% (`fail_under = 80` in `pyproject.toml:82`; CI runs `--cov-fail-under=80` in `.github/workflows/ci.yml:53`).
- Current actual: **91.13%**.

**Renderer-specific coverage (current):**
- excel: 87%, markdown: 90%, pdf: 92%, text: 88%

**View Coverage:**
```bash
uv run pytest --cov=encino_rpt --cov-report=term-missing
```

**Exclusions:**
- `exclude_lines` (`pyproject.toml:84`) exempts: `pragma: no cover`, `if TYPE_CHECKING:`, `if __name__ == .__main__.:`.
- Optional-dep import guards use inline `# pragma: no cover - depende del entorno` (e.g. `encino_rpt/renderers/excel.py:45`, `pdf.py:47`).

## Test Types

**Unit Tests:**
- Direct function-level tests of pure helpers: `evaluate(...)` (`tests/test_report.py:8-38`), `format_value(...)` (`tests/test_report_renderers.py:8-54`), `_coerce(...)` (`tests/test_readers.py:14-33`), `is_dangerous(...)`/`sanitize_csv(...)` (`tests/test_security.py:32-42`), `render(...)` (`tests/test_security.py:88-98`).
- Import internal helpers directly when testing a leaf function: `from encino_rpt.readers import _coerce`, `from encino_rpt.renderers._sanitize import is_dangerous`.

**Integration Tests:**
- The dominant style: build a report via the fluent `Report` API and assert on the materialized `ReportResult` tree or rendered output (`result.run()` → assert on `root`, `columns`, `totals`, `kpis`; `result.to_csv()`/`render_html()` → substring asserts). This exercises the full engine + renderer pipeline.
- Round-trip tests: `data = result.to_dict()` → `ReportResult.from_dict(data)` → `assert restored.to_dict() == data` (`tests/test_report_renderers.py:419-447`).
- Streaming parity tests: `assert list(result.iter_csv()) == result.to_csv().splitlines()` (`tests/test_report_renderers.py:518-544`).
- `file=` write tests: `assert result.to_csv(file=buf) is None` + `buf.getvalue() == result.to_csv()` (`tests/test_report_renderers.py:523-529`).

**E2E Tests:**
- Not used. There is no application/server layer — this is a library, so integration-through-public-API is the highest level.

**Performance Smoke Tests:**
- `tests/test_perf_smoke.py` gates a 50k-row pivot under a 10s wall-clock budget using `time.perf_counter()`, NOT `pytest-benchmark`:
```python
t0 = time.perf_counter()
result = rep.run()
elapsed = time.perf_counter() - t0
...
assert elapsed < 10.0, f"pivot 50k tardó {elapsed:.2f}s (límite 10s)"
```
- Algorithmic assertions also guard against O(n²) regressions: `assert len(processed) == 3 + 2 + 2` and `assert sum(processed) == len(rows) * 3` (`tests/test_report.py:401-423`); deep path groups (1100 levels) assert no recursion blow-up (`tests/test_report.py:426-448`).

## Common Patterns

**Async Testing:**
- Not applicable. The library is synchronous and single-threaded; no `async`/`await` anywhere.

**Error Testing:**
```python
# tests/test_report.py:219-234
def test_order_by_missing_total_raises():
    rows = [{"agente": "Ana", "total": 100}, {"agente": "Bob", "total": 300}]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "total", name="total_agt")
    rep.group("global")
    rep.section("global").order_by(total="total_inexistente")

    with pytest.raises(ValueError, match="total de orden inexistente: 'total_inexistente'"):
        rep.run()
```
- `pytest.raises(ExceptionType, match="regex")` is the standard pattern; the regex is a fragment of the Spanish error message and often anchors with `!r`-quoted values (`match="corte ya declarado"`).
- Error-context assertions use `as exc` to inspect the message for inner context: `assert "(hijo 'Detail')" in str(exc.value)` (`tests/test_report.py:261-263`).
- Imported exceptions are referenced directly: `from encino_rpt.aggregation import AggregationError` inside the test that needs it (`tests/test_report.py:371,382`).

**Optional-dependency testing:**
```python
def test_pdf_renderer():
    pytest.importorskip("reportlab")
    ...
    assert result.to_pdf()[:5] == b"%PDF-"
```

**Excel worksheet assertion idiom:**
```python
vals = [c.value for row in ws.iter_rows() for c in row]
assert "pie Ventas" in vals
```
Formula-mode assertions filter by `c.data_type == "f"` (live formulas) vs `c.data_type == "s"` (sanitized text) (`tests/test_security.py:173-189`).

---

*Testing analysis: 2026-09-17*
