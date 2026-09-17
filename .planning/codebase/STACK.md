# Technology Stack

**Analysis Date:** 2026-09-17

## Languages

**Primary:**
- Python `>=3.10` — the entire library is pure Python (stdlib only). Declared via `requires-python = ">=3.10"` in `pyproject.toml:13`. Classifiers declare support for 3.10–3.13 (`pyproject.toml:24-28`). No compiled extensions, no C/Rust wheels.

**Secondary:**
- None detected. No TypeScript/JS, no templated source files. HTML/Markdown/CSV/JSON/text/PDF output is generated programmatically inside `encino_rpt/renderers/`. Markdown is used only for docs (`docs/*.md`).

## Runtime

**Environment:**
- CPython only. This is a **library**, not an application/server — no server runtime, no web framework, no worker process, no async loop. Local dev venv at `.venv/` (gitignored via `.gitignore`). CI runs on `ubuntu-latest`.

**Package Manager:**
- `uv` (Astral). Lockfile `uv.lock` (lockfile version 1, ~300 KB) at repo root. All dependency versions are pinned there. No `requirements.txt` — `pyproject.toml`-only.
- Lockfile: present (`uv.lock`).

## Frameworks

**Core:**
- **None — zero runtime dependencies.** The package ships no mandatory third-party runtime deps. `[project]` has no `dependencies` key at all (`pyproject.toml:8-31`).
- The canonical data model (`ReportResult`, `Group`, `Detail`, `Total`, `Chart`, `Pivot`, `Kpi`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`) is implemented as stdlib `@dataclass` classes in `encino_rpt/models.py` (pydantic removed entirely). Mutable defaults use `field(default_factory=...)`.
- JSON serialization is a custom stdlib module `encino_rpt/_serialize.py` (`to_jsonable`, `_build`, `_coerce`, `from_dict`) replacing `model_dump(mode="json")` / `model_validate`. It converts `Decimal`→`str`, `datetime/date/time`→`isoformat()`, `Enum`→`.value`, and dispatches the recursive `Group.children` union on the `type` discriminator via `_NODES` (`_serialize.py:17-22`).

**Testing:**
- **pytest** `9.1.1` — dev group (`pyproject.toml:47`). Config `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `pythonpath = ["."]` (`pyproject.toml:41-43`).
- **pytest-cov** `7.1.0` — dev group (`pyproject.toml:52`). Backed by **coverage** `7.16.1` (transitive). Config in `[tool.coverage.run]`/`[tool.coverage.report]` (`pyproject.toml:77-84`) and enforced in CI via `--cov-fail-under=80` (`.github/workflows/ci.yml:53`). Current measured coverage: **91%** (129 tests).

**Build/Dev:**
- **hatchling** — build backend declared in `[build-system]` (`pyproject.toml:1-3`). Wheel packages `["encino_rpt"]` (`pyproject.toml:6`).
- **mypy** `2.3.1` — dev group (`pyproject.toml:51`). Config `[tool.mypy]` (`pyproject.toml:60-67`): `python_version = "3.10"`, `check_untyped_defs`, `warn_unused_ignores`, `warn_redundant_casts`, `no_implicit_optional`, and `disable_error_code = ["import-untyped"]` (openpyxl/reportlab have no typed stubs). **No `pydantic.mypy` plugin.**
- **ruff** `0.16.7` — linter + formatter, dev group (`pyproject.toml:50`). `[tool.ruff]` (`pyproject.toml:69-72`): `target-version = "py310"`, `line-length = 88`, `extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`; `[tool.ruff.format]` (`pyproject.toml:74-75`): `quote-style = "double"`.
- **mkdocs** `1.6.1` + **mkdocs-material** `9.7.7` + **mkdocstrings** `1.0.6` — docs toolchain (docs group, `pyproject.toml:54-58`), configured in `mkdocs.yml`.

## Key Dependencies

**Critical:**
- **None.** The library has zero mandatory runtime dependencies. It runs on Python stdlib alone (`dataclasses`, `typing`, `json`, `csv`, `io`, `math`, `pathlib`, `ast`, `decimal`, `datetime`, `enum`, `operator`, `re`, `html`, `collections.abc`, `types`). Verified via full import scan: no `urllib`, `requests`, `socket`, `http`, or any third-party import at module level in `encino_rpt/`.

**Infrastructure (optional extras):**
- **openpyxl** `3.1.5` — optional extra `excel` (`pyproject.toml:34`, `openpyxl>=3.1.5`). Imported lazily inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:40-46`) and `ExcelReader.read` (`encino_rpt/readers.py:296-299`). Raises `ImportError` with a Spanish hint to install `encino-rpt[excel]` when missing.
- **reportlab** `5.0.1` — optional extra `pdf` (`pyproject.toml:35`, `reportlab>=5.0.1`). Imported lazily inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:35-48`). Same guarded-import pattern. Pulls **pillow** `12.3.0` (transitive).

**Dev/docs (dependency groups, PEP 735):**
- dev group (`pyproject.toml:45-53`): pytest, openpyxl, reportlab, ruff, mypy, pytest-cov
- docs group (`pyproject.toml:54-58`): mkdocs, mkdocs-material, mkdocstrings[python]

## Configuration

**Environment:**
- No `.env`, `.env.*`, or env-var-driven config detected. The library is pure and stateless — no runtime environment variables required. `.env` is listed in `.gitignore` but no such file exists.

**Build:**
- `pyproject.toml` — hatchling build config, project metadata (name `encino-rpt`, version `0.3.0`), optional-dependency extras (`excel`, `pdf`), dependency groups (dev/docs), and tool configs for pytest/mypy/ruff/coverage.
- `mkdocs.yml` — docs config (material theme, `language: es`, mkdocstrings handler with `docstring_style: google`, 5-page nav).
- `.github/workflows/ci.yml` — CI with two jobs: `test` (matrix 3.10–3.13, runs `pytest` + `ruff check`) and `quality` (singleton 3.13, runs `mypy encino_rpt` + `ruff format --check` + coverage `--cov-fail-under=80`).
- `.github/workflows/docs.yml` — builds docs with `uv sync --group docs` + `mkdocs build`, deploys to GitHub Pages.
- `.github/workflows/publish.yml` — `uv build`, publishes to TestPyPI (main) and PyPI (tags `v*`).

## Platform Requirements

**Development:**
- Python 3.10+ installed via `uv python install` (`.github/workflows/ci.yml:21`).
- `uv sync --all-extras --group dev` installs the full dev environment (`.github/workflows/ci.yml:24`).
- `uv run pytest` runs the suite (129 tests); `uv run ruff check` lints; `uv run ruff format --check encino_rpt tests` checks formatting; `uv run mypy encino_rpt` type-checks; `uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80` enforces ≥80% coverage (currently 91%).

**Production:**
- Distributed as a PyPI package (`encino-rpt`), published via `.github/workflows/publish.yml`. Docs hosted on GitHub Pages (`https://hvalles.github.io/encino_rpt/`). No application hosting — this is a library. Version `0.3.0` in `pyproject.toml:10`.
- Windows local dev (this repo lives on `win32`) but CI runs Linux; no OS-specific code detected in `encino_rpt/` (pure stdlib + optional openpyxl/reportlab).

---

*Stack analysis: 2026-09-17*
