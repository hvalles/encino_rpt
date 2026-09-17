# Technology Stack

**Analysis Date:** 2026-09-17

## Languages

**Primary:**
- Python `>=3.10` — the entire library is pure Python. Configured in `pyproject.toml` (`requires-python = ">=3.10"`, line 13). Classifiers declare support for 3.10–3.13 (`pyproject.toml` lines 24–28).

**Secondary:**
- None detected. No TypeScript/JS, no compiled extensions. HTML output is generated as strings inside `encino_rpt/renderers/html.py` (not templated files).

## Runtime

**Environment:**
- CPython only. This is a **library**, not an application/server — there is no server runtime, no web framework, no worker process. Local dev venv at `.venv/` (gitignored). CI runs on `ubuntu-latest` with Python 3.10/3.11/3.12/3.13 (`.github/workflows/ci.yml` lines 10–13). No `.python-version` or `.nvmrc` file present.

**Package Manager:**
- `uv` — lockfile `uv.lock` (version 1) at repo root. All 49 dependency versions are pinned there.
- Lockfile: present (`uv.lock`).

## Frameworks

**Core:**
- **pydantic** `2.13.5` — canonical report data model (`ReportResult`, `Group`, `Total`, `Chart`, `Pivot`, `Kpi`, etc.) in `encino_rpt/models.py`. Declared `pydantic>=2` in `pyproject.toml` line 33 (the **only** runtime dependency). Used for validation and JSON serialization (`model_dump(mode="json")` in `encino_rpt/renderers/json.py:27`).

**Testing:**
- **pytest** `9.1.1` — dev dependency (`pyproject.toml` lines 49–54, `pytest>=9.1.1`). Config in `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = ["."]` (`pyproject.toml` lines 44–46).
- Test files: `tests/test_report.py`, `tests/test_report_renderers.py`, `tests/test_security.py`.

**Build/Dev:**
- **hatchling** — build backend declared in `pyproject.toml` `[build-system]` (lines 1–3). Wheel packages `["encino_rpt"]` (`pyproject.toml` line 6).
- **ruff** `0.16.7` — linter, dev dependency (`pyproject.toml` line 53). NO config section (`[tool.ruff]`) and no `ruff.toml`/`.ruff.toml` — runs with defaults via `uv run ruff check` in CI (`.github/workflows/ci.yml` line 30).
- **mkdocs** `1.6.1` + **mkdocs-material** `9.7.7` + **mkdocstrings** `1.0.6` — docs toolchain (docs dependency group, `pyproject.toml` lines 55–59), configured in `mkdocs.yml`.

## Key Dependencies

**Critical:**
- **pydantic** `2.13.5` (`pydantic-core` `2.46.5`) — the entire data model in `encino_rpt/models.py` is pydantic v2 (`BaseModel`, `Field`, `PrivateAttr`, `Literal`). The recursive `Group.children` reference is resolved with `Group.model_rebuild()` (`encino_rpt/models.py:230`). Removing it would require rewriting the model layer.

**Infrastructure (optional extras):**
- **openpyxl** `3.1.5` — optional extra `excel` (`pyproject.toml` line 37). Imported lazily inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:42-46`): `Workbook`, `Font` (plus `get_column_letter`, chart classes and `styles.Font` imported per-method). Raises `ImportError` with a Spanish hint to install `encino-rpt[excel]` when missing.
- **reportlab** `5.0.1` — optional extra `pdf` (`pyproject.toml` line 38). Imported lazily inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:30-41`): `colors`, `pagesizes.A4`, `styles.getSampleStyleSheet`, `platypus` (`Paragraph`, `SimpleDocTemplate`, `Table`, `TableStyle`). Same guarded-import pattern.

**Transitive (not imported by `encino_rpt/`):**
- **pillow** `12.3.0` — pulled in by the docs/render toolchain (mkdocs-material), not used directly.
- **requests** / **urllib3** / **certifi** / **idna** / **charset-normalizer** — transitive dependencies of the mkdocs docs toolchain (ghp-import, mkdocs), present in `uv.lock` but never imported by the library itself.
- **jinja2** / **markdown** / **pygments** / **pymdown-extensions** / **babel** — mkdocs/mkdocs-material transitive deps.

## Configuration

**Single source of truth:** `pyproject.toml` (project metadata, runtime dependency `pydantic>=2`, optional extras `excel`/`pdf`, dev/docs dependency groups, pytest options).

**Environment:**
- No `.env`, `.env.*`, or env-var-driven config detected. The library is pure and stateless — no runtime environment variables required. `.env` is listed in `.gitignore` (line 23) but no such file exists.

**Build:**
- `pyproject.toml` — hatchling build config, wheel packages `encino_rpt`.
- `mkdocs.yml` — docs config (material theme, `language: es`, mkdocstrings handler with `docstring_style: google`, 5-page nav).
- `.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `.github/workflows/publish.yml` — CI/docs/publish pipelines.

**Artifacts:**
- Existing built artifacts in `dist/`: `encino_rpt-0.2.0-py3-none-any.whl` and `encino_rpt-0.2.0.tar.gz` (gitignored; version 0.2.0, behind the current `version = "0.2.1"` in `pyproject.toml` line 10). Deploy via GitHub Actions only: `uv build` in `.github/workflows/publish.yml` line 19.

## Platform Requirements

**Development:**
- Python 3.10+ installed via `uv python install` (see `.github/workflows/ci.yml` line 21).
- `uv sync --all-extras --group dev` installs the full dev environment (`uv.lock`, `.github/workflows/ci.yml` line 24).
- `uv run pytest` runs the suite; `uv run ruff check` lints.

**Production:**
- Distributed as a PyPI package (`encino-rpt`), published via `.github/workflows/publish.yml` to TestPyPI (main branch) and PyPI (tags `v*`). No hosting/deployment of an app — this is a library.
- Windows local dev (this repo lives on `win32`) but CI runs Linux; no OS-specific code detected in `encino_rpt/` (pure stdlib + pydantic).

---

*Stack analysis: 2026-09-17*
