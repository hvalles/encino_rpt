# Testing Patterns

**Analysis Date:** 2026-09-16

## Test Framework

**Runner:**
- pytest 9.1.1 (dev dependency, `pyproject.toml:51`)
- Config in `pyproject.toml` `[tool.pytest.ini_options]` (`pyproject.toml:45-47`):
  - `testpaths = ["tests"]`
  - `pythonpath = ["."]`
- No `conftest.py`, no `pytest.ini`, no markers, no fixtures, no plugins (no pytest-cov)

**Assertion Library:**
- Plain `assert` (pytest assertion rewriting)

**Run Commands:**
```bash
uv run pytest              # full suite (32 tests, ~0.9s)
uv run pytest -q           # quiet
uv run pytest tests/test_security.py  # single file
uv run ruff check          # linter (CI runs this after tests)
```

**CI:** `.github/workflows/ci.yml` runs `uv sync --all-extras --group dev`, `uv run pytest`, then `uv run ruff check` on a Python 3.10–3.13 matrix (`.github/workflows/ci.yml:10-30`).

## Test File Organization

**Location:**
- All tests live in `tests/`, flat (no subdirectories). Production code is never co-located with tests.

**Naming:**
- Files: `test_<area>.py`
- Functions: `test_<behavior>` (e.g. `test_group_and_totals`)
- No test classes — function-based only

**Structure:**
```
tests/
├── test_report.py           # 16 tests: expressions, builder, aggregation, groups,
│                            #   totals, cumulative, charts/pivots, links/images,
│                            #   formats/styles, KPIs, JSON roundtrip, path groups
├── test_report_renderers.py # 10 tests: format_value, text, CSV, HTML, Excel (×4),
│                            #   PDF
└── test_security.py         # 6 tests: formula injection, expression DoS limits,
                             #   HTML style injection, template param validation
```

## Test Structure

**Suite Organization:**
Tests are grouped into logical areas with `# --- area ---` banner comments in Spanish:

```python
# --- evaluador de expresiones ---
def test_expression_arithmetic():
    ...
```

```python
# --- P1: inyección de fórmulas ---
def test_csv_formula_injection():
    ...
```

**Canonical per-test pattern** (from `tests/test_report.py`):

```python
def test_group_and_totals():
    rows = [
        {"agente": "Ana", "monto": 100},
        {"agente": "Ana", "monto": 50},
        {"agente": "Bob", "monto": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").header("Agente {{agente}}")
    rep.section("por_agente").total("sum", "monto")
    rep.group("global")
    rep.section("global").total("sum", "monto")
    result = rep.run()

    root = result.root
    assert root.name == "global"
    assert root.totals[0].value == 350
    assert len(root.children) == 2
    ana, bob = root.children
    assert ana.key == {"agente": "Ana"}
    assert ana.totals[0].value == 150
    assert ana.header == "Agente Ana"
```

**Patterns:**
- Each test builds its own inline `rows` list of `list[dict]` as the Arrange step — no shared fixtures, no module-level test data
- Fluent chain Arrange: `Report(rows)` → `.group(...)`/`.section(...)`/`.detail(...)` → `result = rep.run()`
- Assert on the canonical tree rather than renderer output for pipeline logic (`.root.children`, `.key`, `.totals[0].value`, `.columns`)
- One or two focused behaviors per test; assertions are direct and specific
- Destruction/unpacking used to name meaningful locals: `ana, bob = root.children`, `chart, pivot = result.root.children[-2], result.root.children[-1]` (`tests/test_report.py:169`)

## Mocking

**Framework:** None. Zero usages of `unittest.mock`, `monkeypatch`, or `pytest-mock`.

**What to Mock:**
- Nothing. The codebase is dependency-light (pydantic + `encino-rpt` package dependency only at runtime) and tests exercise real behavior end to end.
- Optional-dependency-backed tests are guarded with `pytest.importorskip` instead of mocking the optional package:

```python
def test_pdf_renderer():
    pytest.importorskip("reportlab")
    rows = [{"sku": "A", "cantidad": 2}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    result = rep.run()
    pdf = result.to_pdf()
    assert pdf[:5] == b"%PDF-"
```

**What NOT to Mock:**
- Do not mock `openpyxl`/`reportlab` — guard with `pytest.importorskip` (`tests/test_report_renderers.py:67,84,101,113`, `tests/test_security.py:19`) so the test runs when the extra is installed and skips otherwise.
- Do not mock the `Report` builder — drive it with real rows and assert on the real `ReportResult`.

## Fixtures and Factories

**Test Data:**
- Inline per-test `rows` dicts (see pattern above). No fixture module, no factory functions, no `parametrize`.
- Test data uses Spanish business values matching the domain: `{"agente": "Ana", "monto": 100}`, `{"sku": "A", "cantidad": 2, "precio": 10.0}`, `{"pedido_id": 1, "total": 100}`

**Location:**
- N/A — no shared fixtures.

## Coverage

**Requirements:** None enforced. No `[tool.coverage]` config, no `pytest-cov` in dev dependencies, no coverage step in `.github/workflows/ci.yml`. `.coverage`/`htmlcov/` are gitignored (`gitignore:18-19`) in case a local tool is ever pointed at the repo.

**pragma: no cover:**
- Exactly two sites, both optional-dependency `ImportError` branches that cannot run in a fully-installed environment:
  - `encino_rpt/renderers/excel.py:44` — `except ImportError as exc:  # pragma: no cover - depende del entorno`
  - `encino_rpt/renderers/pdf.py:39` — same pattern
- Keep this convention for any new optional-dependency guards.

## Test Types

**Unit Tests:** The entire suite is unit-level. `tests/test_report.py` covers the expression evaluator and the aggregation pipeline; `tests/test_report_renderers.py` covers formatters and the five renderers; `tests/test_security.py` covers the security mitigations (formula injection, DoS limits, HTML escaping, template param bounds).

**Integration Tests:** None beyond renderer output assertions (e.g. verifying `ws["A1"].value == "sku"` against a real openpyxl sheet at `tests/test_report_renderers.py:76-80`). These are closer to unit tests since the optional deps are real.

**E2E Tests:** Not used.

## Common Patterns

**Async Testing:**
- Not applicable — no async code in the codebase.

**Error Testing:**
```python
def test_expression_rejects_unsafe():
    with pytest.raises(ExpressionError):
        evaluate("__import__('os')", {})
    with pytest.raises(ExpressionError):
        evaluate("(lambda: 1)()", {})
    with pytest.raises(ExpressionError):
        evaluate("x.__class__", {"x": 1})
```
(`tests/test_report.py:32-38`, and the multipleraises variant in `tests/test_security.py:31-41`)
- Use `pytest.raises(<Exception>)` with the exact domain exception class (`ExpressionError`, `IndexError`, `ValueError`); also used for param bounds (`tests/test_security.py:58-63`)

**Optional-Dependency Guard Pattern:**
```python
def test_excel_formulas():
    pytest.importorskip("openpyxl")
    ...
```
- Verify derivation scope is narrow: the `pytest.importorskip` call is the **first** statement of the test, before any behavior (e.g. `tests/test_report_renderers.py:84-91`)

**Formatting/Edge-Case Testing:**
```python
def test_format_value_number():
    assert format_value(1.234, Format(decimals=2)) == "1.23"
    assert format_value(None, Format()) == ""
    assert format_value(5, None) == "5"
```
(`tests/test_report_renderers.py:19-22`)
- Multiple `assert`s on the same function with different inputs instead of `parametrize`; `None` and degenerate inputs tested explicitly

**Security Testing Pattern:**
- One banner per threat with a numbered ID (`P1`–`P4` in `tests/test_security.py`), each test asserts the mitigation output:
  - Formula injection: assert CSV output is prefixed `'=1+1,2` (`tests/test_security.py:15`) and Excel cell `data_type == "s"` (`tests/test_security.py:27`)
  - DoS: huge chained exponent and 2000-term expression both raise `ExpressionError` (`tests/test_security.py:31-41`)
  - HTML style injection: crafted `color='red" onmouseover="x'` must not appear escaped in output (`tests/test_security.py:49-54`)
  - Template params: `render("{{param.0}}", {}, params=["a", "b"]) == "a"`, out-of-range raises `IndexError`, malformed raises `ValueError` (`tests/test_security.py:59-63`)

**Roundtrip Testing:**
```python
data = result.model_dump()
assert data["root"]["type"] == "group"
restored = ReportResult.model_validate(data)
assert restored.columns == ["sku", "cantidad"]
```
(`tests/test_report.py:235-243`)

**Renderer Output Assertions:**
- Excel: direct cell inspection — `ws["A1"].value`, `ws["A2"].number_format`, formula detection via `isinstance(c.value, str) and c.value.startswith("=")` (`tests/test_report_renderers.py:93-97`)
- PDF: magic-byte check `pdf[:5] == b"%PDF-"` (`tests/test_report_renderers.py:119`)
- HTML/CSV/text: `in` substring assertions on rendered strings (`tests/test_report_renderers.py:37-40,49-50,61-63`)

## Guidelines for Adding Tests

- Add to the matching file by area: expression/builder/aggregation → `tests/test_report.py`; formatting or a renderer → `tests/test_report_renderers.py`; a security mitigation → `tests/test_security.py`, and give it a numbered banner (`# --- P5: ... ---`)
- Mirror the Arrange style: inline `rows = [...]`, fluent builder calls, `result = rep.run()`, assert on the canonical tree
- Group related assertions in one test rather than fragmenting into many
- If the new test hits a new optional dependency, guard with `pytest.importorskip` as the first statement
- If a code path cannot run in CI (optional extra absent), mark the branch `# pragma: no cover`
- Run locally: `uv run pytest` — the suite must stay fast (~1s) and lint-clean (`uv run ruff check`)

---

*Testing analysis: 2026-09-16*