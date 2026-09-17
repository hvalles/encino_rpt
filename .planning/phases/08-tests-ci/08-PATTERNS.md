# Phase 8: Tests & CI - Pattern Map

**Mapped:** 2026-09-16
**Files analyzed:** 6 (1 config + 1 CI workflow + 1 new test module + 3 modified test modules)
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `pyproject.toml` | config | n/a (static config) | `pyproject.toml` (existing `[dependency-groups] dev`, `[tool.pytest.ini_options]`) | exact |
| `.github/workflows/ci.yml` | config (CI) | batch (CI pipeline) | `.github/workflows/ci.yml` (existing `test` matrix) + `docs.yml` (multi-job `needs`) | exact |
| `tests/test_perf_smoke.py` | test | batch (builder→run→assert) | `tests/test_report.py` (`test_pivot_single_pass`, `test_path_group_deep_no_recursion`) | exact |
| `tests/test_report.py` | test | request-response (builder→`run()`→assert tree) | `tests/test_report.py` (self) | exact |
| `tests/test_report_renderers.py` | test | transform (builder→`run()`→renderer output) | `tests/test_report_renderers.py` (self) | exact |
| `tests/test_security.py` | test | request-response (security mitigation asserts) | `tests/test_security.py` (self) | exact |

## Pattern Assignments

### `pyproject.toml` (config)

**Analog:** `pyproject.toml` — the file itself. New sections slot in after the existing `[dependency-groups]` block. No new runtime deps; everything lands in the `dev` group.

**Existing dev-dependency group** (lines 48-54) — add `mypy` and `pytest-cov` here:
```toml
[dependency-groups]
dev = [
    "pytest>=9.1.1",
    "openpyxl",
    "reportlab",
    "ruff>=0.16.7",
]
```

**Existing pytest config** (lines 44-46) — do NOT add `--cov` here (keeps local runs fast; coverage stays a CI-only flag):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

**New sections** (append after line 59; content from RESEARCH.md lines 250-269):
```toml
[tool.mypy]
plugins = ["pydantic.mypy"]
python_version = "3.10"
check_untyped_defs = true
warn_unused_ignores = true
warn_redundant_casts = true
no_implicit_optional = true

[tool.ruff]
target-version = "py310"
line-length = 88
extend-exclude = [".planning", "docs", "dist", "build", ".venv"]

[tool.ruff.format]
quote-style = "double"

[tool.coverage.run]
source = ["encino_rpt"]
branch = false

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```
**Convention constraint:** `ruff` currently runs with **defaults only** (no `[tool.ruff]` section). Adding `[tool.ruff]` must not change lint behavior — only `target-version`, `line-length`, `extend-exclude`, and the format block. No `select`/`ignore`.

---

### `.github/workflows/ci.yml` (config, batch/CI)

**Analog:** `.github/workflows/ci.yml` (existing `test` matrix job) + `.github/workflows/docs.yml` (multi-job `needs` pattern).

**Existing test matrix job** (lines 8-30) — keep as-is; it already does `uv sync --all-extras --group dev` + `ruff check` + `pytest`:
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --all-extras --group dev

      - name: Run tests
        run: uv run pytest

      - name: Lint
        run: uv run ruff check
```

**Multi-job pattern** (from `docs.yml` lines 16-48 — the `build`/`deploy` split shows `runs-on` + step ordering; `publish.yml` lines 26-45 shows `needs:` for job fan-out):
```yaml
  deploy:
    needs: build
    runs-on: ubuntu-latest
```

**New `quality` job** (singleton, Python 3.13; content from RESEARCH.md lines 302-319). Add as a second entry under `jobs:`, reusing the same `actions/checkout@v4` + `astral-sh/setup-uv@v4` + `uv python install` + `uv sync` step sequence as the existing `test` job:
```yaml
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - name: Set up Python 3.13
        run: uv python install 3.13
      - name: Install dependencies
        run: uv sync --all-extras --group dev
      - name: Type check
        run: uv run mypy encino_rpt
      - name: Format check
        run: uv run ruff format --check .
      - name: Coverage
        run: uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80
```
**Sequencing constraint:** `ruff format --check` must land **only after** a one-time `uv run ruff format encino_rpt tests` normalization commit (verified: format fails today on 40+ files + 17 `.md`). The normalization is scoped to `encino_rpt tests`, never `.`.

---

### `tests/test_perf_smoke.py` (test, batch) — NEW

**Analog:** `tests/test_report.py` — perf-related tests already live there and exercise the same `Report(rows)` → `run()` → assert pattern.

**Imports pattern** (`tests/test_report.py` lines 1-4):
```python
import pytest

from encino_rpt import Chart, Detail, Group, Pivot, Report, ReportResult
from encino_rpt.expressions import ExpressionError, evaluate
```
For the perf module, the minimal import set is `import time` + `from encino_rpt import Report` (RESEARCH.md lines 275-277). No `pytest.importorskip` needed — pivot is pure Python.

**Large-input + wall-clock + correctness pattern** (mirrors `test_path_group_deep_no_recursion` at `tests/test_report.py` lines 418-436, which builds a 1100-deep path and asserts a concrete value):
```python
# tests/test_perf_smoke.py
import time

from encino_rpt import Report


def test_pivot_50k_rows_smoke():
    n = 50_000
    rows = [
        {"region": f"r{i % 50}", "product": f"p{i % 200}", "amount": i % 100}
        for i in range(n)
    ]
    rep = Report(rows)
    rep.group("global")
    rep.section("global").pivot("region", "product", operator="sum", value_column="amount")

    t0 = time.perf_counter()
    result = rep.run()
    elapsed = time.perf_counter() - t0

    pivot = result.root.children[-1]
    assert len(pivot.rows) == 50
    assert len(pivot.columns) == 200
    assert pivot.row_totals[0] == sum((i % 100) for i in range(n) if i % 50 == 0)
    assert elapsed < 10.0, f"pivot 50k tardó {elapsed:.2f}s (límite 10s)"
```
**Assertion convention:** assert a concrete value (dimensions + a computable total), never just "didn't crash" — matches the existing suite's style (`test_pivot_single_pass` asserts `pivot.row_totals == [3, 3]`, `tests/test_report.py` lines 393-415).

---

### `tests/test_report.py` (test, request-response) — modified

**Analog:** itself. Regression additions (gaps #1, #2, #3, #4, #6, #8, #11) follow the file's existing `Report(rows)` → `rep.run()` → assert-on-tree pattern.

**Core builder pattern** (`tests/test_report.py` lines 42-60):
```python
def test_basic_report_and_hidden_fields():
    rows = [
        {"sku": "A", "cantidad": 2, "precio": 10.0},
        {"sku": "B", "cantidad": 1, "precio": 5.0},
    ]
    rep = Report(rows)
    rep.add_field("total", "cantidad * precio", after="precio")
    rep.detail("sku", "cantidad", "precio", "total")
    result = rep.run()
    assert result.columns == ["sku", "cantidad", "precio", "total"]
    assert result.root.name == "global"
    assert result.root.children[0].row["total"] == 20.0
```

**Error-context assertion pattern** (for gap #11 chart/pivot error context; analog `test_aggregation_error_context` lines 362-370):
```python
def test_aggregation_error_context():
    from encino_rpt.aggregation import AggregationError

    rows = [{"monto": 0}]
    rep = Report(rows)
    rep.group("global")
    rep.section("global").total("sum", expression="1 / monto")
    with pytest.raises(AggregationError, match="grupo 'global'"):
        rep.run()
```

**Documenting-current-behavior convention** (gaps #2, #3, #4, #6, #8, #11): use plain `pytest.raises(TypeError)` / value asserts, with a Spanish comment marking the known bug. The existing suite's comment style is inline Spanish: `# oculto: no aparece en las columnas ni en el detalle` (`test_report.py` line 58). New regression tests should carry `# regresión documenta bug conocido — ver CONCERNS.md`.

**Section-banner grouping** (existing convention, `tests/test_report.py`): group new tests under `# --- ... ---` banners mirroring existing ones (`# --- errores con contexto ---`, `# --- rendimiento ---`).

---

### `tests/test_report_renderers.py` (test, transform) — modified

**Analog:** itself. Regression additions (gaps #5 deep-tree JSON, #7 Excel dead params) follow the renderer-output assert pattern.

**Imports + optional-dep guard pattern** (`tests/test_report_renderers.py` lines 1-5 and `test_excel_renderer` line 95):
```python
import pytest

from encino_rpt import Report
from encino_rpt.models import Format
from encino_rpt.renderers._format import format_value
```
```python
def test_excel_renderer():
    pytest.importorskip("openpyxl")
```

**JSON round-trip pattern** (gap #5 analog, `test_json_renderer_roundtrip` lines 281-298):
```python
def test_json_renderer_roundtrip():
    import json
    from encino_rpt import ReportResult

    rows = [{"sku": "A", "cantidad": 2}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    rep.group("global")
    rep.section("global").total("sum", "cantidad")
    result = rep.run()

    data = json.loads(result.to_json())
    assert data["schema_version"] == "1.0"
    assert data["root"]["type"] == "group"

    restored = ReportResult.model_validate(data)
    assert restored.root.totals[0].value == 2
```

**Excel worksheet assert pattern** (gap #7 analog, `test_excel_total_column_position` lines 231-242):
```python
def test_excel_total_column_position():
    pytest.importorskip("openpyxl")
    ...
    ws = result.to_excel()
    assert ws["A3"].value == "sum"
    assert ws["B3"].value is None
    assert ws["C3"].value == 100
```

---

### `tests/test_security.py` (test, request-response/security) — modified

**Analog:** itself. Regression additions (gaps #9 null-byte, #10 formula-mode no user injection) follow the security-mitigation assert pattern.

**Imports + evaluator assert pattern** (`tests/test_security.py` lines 1-6, 61-65):
```python
import pytest

from encino_rpt import Report
from encino_rpt.expressions import ExpressionError, evaluate
from encino_rpt.renderers._sanitize import is_dangerous, sanitize_csv
from encino_rpt.template import render
```
```python
def test_expression_pow_limit():
    with pytest.raises(ExpressionError):
        evaluate("9 ** 9 ** 9 ** 9 ** 9", {})
```

**Formula-injection assert pattern** (gap #10 analog, `test_excel_formula_injection` lines 19-28):
```python
def test_excel_formula_injection():
    pytest.importorskip("openpyxl")
    rows = [{"sku": "=1+1"}]
    rep = Report(rows)
    rep.detail("sku")
    result = rep.run()
    ws = result.to_excel()
    cell = ws["A2"]
    assert cell.value == "=1+1"
    assert cell.data_type == "s"
```

---

## Shared Patterns

### Pytest test structure (all 4 test files)
**Source:** `tests/test_report.py`, `tests/test_security.py`, `tests/test_report_renderers.py`
**Apply to:** `tests/test_perf_smoke.py` and all modified test files
- Top-level `import pytest` first, then `from encino_rpt import ...` (absolute import, relies on `pythonpath = ["."]` in `pyproject.toml:46`).
- Tests are plain functions (`def test_*`) with no classes, no fixtures for the happy path, no `conftest.py` present.
- Optional deps guarded inline with `pytest.importorskip("openpyxl")` / `pytest.importorskip("reportlab")` — never at module level (each optional-dependent test guards itself).
- Section banner comments `# --- área ---` group related tests; comments are Spanish.

### Error-context assertion convention
**Source:** `tests/test_report.py:362-381`
**Apply to:** gaps #11 (`test_chart_pivot_error_context`) and any new error-context test
```python
with pytest.raises(AggregationError, match="grupo 'global'"):
    rep.run()
```

### CI step bootstrap (shared across jobs)
**Source:** `.github/workflows/ci.yml:15-24`
**Apply to:** the new `quality` job
```yaml
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v4
      - name: Set up Python ...
        run: uv python install ...
      - name: Install dependencies
        run: uv sync --all-extras --group dev
```
Use `actions/checkout@v4` and `astral-sh/setup-uv@v4` exactly as the existing `test` job does; pin action versions to match (`@v4`).

### Optional-dependency isolation
**Source:** `pyproject.toml:36-38` (`[project.optional-dependencies] excel/pdf`), `uv.lock`
**Apply to:** `pyproject.toml` — `mypy` and `pytest-cov` go in the `dev` group only, NOT `dependencies` (which stays `["pydantic>=2"]`). This preserves the "pydantic is the only runtime dependency" invariant from `PROJECT.md`.

## No Analog Found

None — every target file has an exact in-repo analog. The only novel *content* is the config blocks and the `quality` job, which come verbatim from RESEARCH.md (already verified against official ruff/coverage/pydantic-mypy docs) and slot into the existing `pyproject.toml` / `ci.yml` structure.

## Metadata

**Analog search scope:** `pyproject.toml`, `.github/workflows/` (ci/docs/publish), `tests/` (3 files)
**Files scanned:** 7 (pyproject, 3 workflows, 3 test files)
**Pattern extraction date:** 2026-09-16
