# Testing Patterns

**Analysis Date:** 2026-09-17

## Test Framework

**Runner:**
- **pytest** `>=9.1.1` (dev dependency group, `pyproject.toml:47`)
- Config in `[tool.pytest.ini_options]` (`pyproject.toml:41-43`):
  - `testpaths = ["tests"]`
  - `pythonpath = ["."]`
- **No `conftest.py`**, no custom fixtures file, no `pytest.ini`/`setup.cfg`/`tox.ini`. All config lives in `pyproject.toml`.

**Coverage:**
- **pytest-cov** `>=7.1.0` (dev group, `pyproject.toml:52`), backed by **coverage** `7.16.1` (transitive)
- Config in `[tool.coverage.run]` / `[tool.coverage.report]` (`pyproject.toml:77-84`):
  - `source = ["encino_rpt"]`, `branch = false`
  - `fail_under = 80`, `show_missing = true`
  - `exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "if __name__ == .__main__.:"]`

**Assertion Library:**
- Built-in `assert` statements only. No `pytest-check`, no `assertpy`, no Hamcrest.

**Run Commands:**
```bash
uv run pytest                                                   # Run all tests
uv run pytest tests/test_report.py                              # Run one file
uv run pytest tests/test_report.py::test_group_and_totals       # Run one test
uv run pytest -k "excel"                                        # Select by keyword
uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80   # Coverage (CI)
uv run pytest --cov=encino_rpt --cov-report=html                # HTML coverage report
```
There is no dedicated watch-mode config; pytest's own `--lf`/`--pdb` are available but not scripted.

## Test File Organization

**Location:**
- Single `tests/` directory at repo root (NOT co-located with source, no `src/` layout). Test discovery is via `testpaths = ["tests"]`.

**Naming:**
- Files: `tests/test_<area>.py` — `test_report.py` (builder/aggregation/expressions), `test_report_renderers.py` (all renderers + `format_value`), `test_security.py` (injection/DoS), `test_readers.py` (multi-format input), `test_perf_smoke.py` (large-input wall-clock smoke)
- Functions: `test_<thing>_<behavior>()`, e.g. `test_order_by_missing_total_raises`, `test_html_css_mode_no_inline_style`, `test_csv_formula_injection`
- Helpers are prefixed `_` so pytest ignores them: `_streaming_report()` (`tests/test_report_renderers.py:509`), class `_MiReader` (`tests/test_readers.py:128`)

**Structure (118 tests, 5 files):**
```
tests/
├── test_report.py             # 36 tests — expressions, builder, aggregation, errors, idempotency, deep paths
├── test_report_renderers.py   # 48 tests — format_value, all 7 renderers, streaming parity, round-trip
├── test_security.py           # 18 tests — formula injection, DoS, HTML/CSS injection
├── test_readers.py            # 15 tests — _coerce, csv/tsv/json/jsonl/tuples/excel readers
└── test_perf_smoke.py         #  1 test  — 50k-row pivot wall-clock bound
```

## Test Structure

**Suite organization — flat functions, no test classes.** Every test is a top-level `def test_*`. There are no `class TestXxx` test containers and no `parametrize`.

**Typical test shape (build → run → assert on the canonical tree):**
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
    assert bob.key == {"agente": "Bob"}
```
(`tests/test_report.py:63-85`)

**Error-test pattern (`pytest.raises` with `match=` for the Spanish message):**
```python
with pytest.raises(ValueError, match="corte ya declarado"):
    rep.group("g", columns="a")

with pytest.raises(
    ValueError, match="total de orden inexistente: 'total_inexistente'"
):
    rep.run()
```
(`tests/test_report.py:357-358`, `231-234`). For context-preserving assertions, capture the exception and assert on its text: `as exc:` + `assert "(hijo 'Detail')" in str(exc.value)` (`tests/test_report.py:261-263`).

**Optional-dependency tests use `pytest.importorskip` at the top of the function:**
```python
def test_excel_renderer():
    pytest.importorskip("openpyxl")
    ...
```
(`tests/test_report_renderers.py:209`, `286` for reportlab). Every Excel/PDF test opens with this guard.

**Setup/teardown:**
- No `setup`/`teardown` methods, no `yield` fixtures. Each test builds its own `Report` from inline `rows` data — fully self-contained.
- File-based tests use the built-in `tmp_path` fixture: `path = tmp_path / "datos.csv"; path.write_text(...)` (`tests/test_readers.py:36-38`).

## Mocking

**Framework:** **None.** There is no `unittest.mock`, no `pytest-mock`, no `responses`, no `betamax`. The library has no network/DB/FS dependencies to mock, so tests run against real objects with in-memory `list[dict]` data.

**The only monkeypatch** is `monkeypatch.setitem(sys.modules, "openpyxl", None)` to simulate the optional `excel` extra being absent and assert the `ImportError` path:
```python
def test_excel_missing_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "openpyxl", None)
    with pytest.raises(ImportError):
        read_rows("datos.xlsx", format="excel")
```
(`tests/test_readers.py:160-163`)

**What to mock (if ever needed):** only third-party optional deps (`openpyxl`/`reportlab`) to simulate their absence — and prefer `monkeypatch.setitem(sys.modules, ...)` for that.

**What NOT to mock:** anything in `encino_rpt` itself. The engine, readers, and renderers are exercised end-to-end on real data. Custom behavior (e.g. a custom reader) is tested with a real minimal implementation: class `_MiReader` with a `read(self, source, **opts)` method (`tests/test_readers.py:128-139`).

## Fixtures and Factories

**Test data:** inline literals in each test. Rows are `list[dict]` literals, never imported from a shared factory or JSON fixture file. There are no `.json`/`.csv`/`.yaml` fixture files in the repo.

**Built-in fixtures used:** `tmp_path` (writable temp dir, `tests/test_readers.py:36,143`) and `monkeypatch` (`tests/test_readers.py:160`). No other fixtures.

**Shared helper (not a fixture):** `_streaming_report()` returns a ready `ReportResult` for the streaming-parity tests (`tests/test_report_renderers.py:509-515`).

**Location:** test data lives inline; no `tests/fixtures/` directory exists.

## Coverage

**Requirements:** `fail_under = 80` enforced in CI via `--cov-fail-under=80` (`.github/workflows/ci.yml:53`). Local `.coverage` data file is gitignored (`.gitignore:18`).

**Exclusions:**
- `# pragma: no cover` marks environment-dependent branches (optional-dep import guards: `encino_rpt/renderers/excel.py:43`, `pdf.py:45`, `readers.py:297`)
- `if TYPE_CHECKING:` and `if __name__ == "__main__":` are auto-excluded via `exclude_lines` (`pyproject.toml:84`)

**View Coverage:**
```bash
uv run pytest --cov=encino_rpt --cov-report=term-missing   # per-line missing
uv run pytest --cov=encino_rpt --cov-report=html            # htmlcov/ (gitignored)
```

## Test Types

**Unit tests** (pure functions, no `Report`): expression evaluator (`test_expression_arithmetic`, `test_expression_functions`, `test_expression_rejects_unsafe` in `tests/test_report.py:8-38`), `_coerce` type auto-detection (`tests/test_readers.py:14-32`), `format_value`/`excel_number_format` (`tests/test_report_renderers.py:8-54`), `is_dangerous`/`sanitize_csv` (`tests/test_security.py:32-42`), `render` template (`tests/test_security.py:88-98`).

**Integration tests** (full `Report(...) → run() → render` pipeline): the bulk of `test_report.py`, `test_report_renderers.py`, and `test_readers.py`. These build a `Report`, declare detail/groups/totals/charts/pivots, call `run()`, and assert on both the canonical tree (`result.root.children`, `.totals`, `.columns`) and rendered output strings.

**Security tests** (`test_security.py`, 18 tests): formula-injection (`=1+1`, leading space/BOM/`@`), DoS limits in the expression evaluator (`**` exponent, node count), HTML/CSS attribute injection, template `param.N` validation. Tagged `# P1`–`# P5`.

**Round-trip / serialization tests:** `test_report_result_roundtrip` (`tests/test_report.py:303`), `test_roundtrip_full_tree` (`test_report_renderers.py:419`), `test_json_renderer_roundtrip` (`test_report_renderers.py:399`), `test_from_dict_missing_keys_use_defaults` (`test_report_renderers.py:557`) — verify `to_dict`/`from_dict` and `to_json`/`from_json` symmetry.

**Idempotency test:** `test_run_is_idempotent` (`tests/test_report.py:340`) asserts `first.to_dict() == second.to_dict()` across two `run()` calls.

**Deep-recursion / robustness tests:** `test_path_group_deep_no_recursion` and `test_deep_path_renders_iteratively` build 1100-level `path` hierarchies to prove iterative (non-recursive) traversal (`tests/test_report.py:426`, `tests/test_report_renderers.py:450`); `test_deep_tree_to_json` asserts the controlled `ValueError` instead of `RecursionError` (`test_report_renderers.py:467`).

**Performance smoke tests** (`test_perf_smoke.py`): wall-clock gate using `time.perf_counter()` with an explicit bound (`elapsed < 10.0`) — no `pytest-benchmark`, no `pytest.mark`:
```python
t0 = time.perf_counter()
result = rep.run()
elapsed = time.perf_counter() - t0
...
assert elapsed < 10.0, f"pivot 50k tardó {elapsed:.2f}s (límite 10s)"
```
(`tests/test_perf_smoke.py:23-31`). A single-pass pivot assertion also lives in `test_pivot_single_pass` (`tests/test_report.py:401-423`), which counts `value_fn` invocations to verify `O(rows)` behavior.

**E2E tests:** not used (this is a library, not an app/server).

## Common Patterns

**Async Testing:** none — the library is synchronous, single-threaded.

**Error Testing:** always `pytest.raises(ExceptionType, match="...")` with the exact Spanish substring; use `as exc:` + `str(exc.value)` when asserting extra context beyond a single match.

**Streaming-parity tests** assert `iter_*` == `render`/`to_*` split:
```python
assert list(result.iter_csv()) == result.to_csv().splitlines()
assert "".join(result.iter_html()) == result.render_html()
assert "\n".join(result.iter_markdown()) == result.to_markdown()
```
(`tests/test_report_renderers.py:518-544`)

**File-write tests** assert `to_*(file=...)` returns `None` and writes matching bytes/str:
```python
buf = io.StringIO()
assert result.to_csv(file=buf) is None
assert buf.getvalue() == result.to_csv()
```
(`tests/test_report_renderers.py:523-529`, `547-554`)

**Optional-dep guard idiom:**
```python
pytest.importorskip("openpyxl")   # or "reportlab"
```
Always the first statement of any test touching Excel/PDF.

**Regression tags:** tests that close a known issue carry a `# CORR-NN` / `# TMPL-NN` / `# JSON-01` / `# TEST-01` comment (e.g. `tests/test_report.py:452,471,487,499,513,528,539,551`; `tests/test_report_renderers.py:467`; `tests/test_security.py:166,173`).

---

*Testing analysis: 2026-09-17*
