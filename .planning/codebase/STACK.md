# Technology Stack

**Analysis Date:** 2026-09-17

## Languages

**Primary:**
- Python `>=3.10` — the entire library is pure Python. Declared via `requires-python = ">=3.10"` in `pyproject.toml:13`. Classifiers declare support for 3.10–3.13 (`pyproject.toml:25-28`). No compiled extensions.

**Secondary:**
- None detected. No TypeScript/JS, no templated files. HTML output is generated as strings inside `encino_rpt/renderers/html.py`. Markdown is used only for docs (`docs/*.md`).

## Runtime

**Environment:**
- CPython only. This is a **library**, not an application/server — no server runtime, no web framework, no worker process. Local dev venv at `.venv/` (gitignored). CI runs on `ubuntu-latest`.

**Package Manager:**
- `uv` (Astral). Lockfile `uv.lock` (lockfile version 1) at repo root. All dependency versions are pinned there. No `requirements.txt`, `pyproject`-only.
- Lockfile: present (`uv.lock`, ~338 KB).

## Frameworks

**Core:**
- **pydantic** `2.13.5` (`pydantic-core` `2.46.5`) — canonical report data model (`ReportResult`, `Group`, `Total`, `Chart`, `Pivot`, `Kpi`, etc.) in `encino_rpt/models.py`. Declared `pydantic>=2` in `pyproject.toml:33` — the **only** runtime dependency. Used for validation and JSON serialization (`model_dump(mode="json")` in `encino_rpt/renderers/json.py:27`).

**Testing:**
- **pytest** `9.1.1` — dev group (`pyproject.toml:50`, `pytest>=9.1.1`). Config `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `pythonpath = ["."]` (`pyproject.toml:44-46`).
- **pytest-cov** `7.1.0` — dev group (`pyproject.toml:55`). Backed by **coverage** `7.16.1` (transitive). Enforced in the CI `quality` job via `--cov-fail-under=80` (`.github/workflows/ci.yml:53`).

**Type Checking:**
- **mypy** `2.3.1` — dev group (`pyproject.toml:54`). Config `[tool.mypy]` (`pyproject.toml:63-71`): `plugins = ["pydantic.mypy"]`, `python_version = "3.10"`, `check_untyped_defs`, `warn_unused_ignores`, `warn_redundant_casts`, `no_implicit_optional`, and `disable_error_code = ["import-untyped"]` (openpyxl/reportlab have no typed stubs).

**Build/Dev:**
- **hatchling** — build backend declared in `[build-system]` (`pyproject.toml:1-3`). Wheel packages `["encino_rpt"]` (`pyproject.toml:6`). Not version-pinned in `uv.lock` (build backend, not a project dependency).
- **ruff** `0.16.7` — linter + formatter, dev group (`pyproject.toml:53`). Config now present: `[tool.ruff]` (`pyproject.toml:73-76`) sets `target-version = "py310"`, `line-length = 88`, `extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`; `[tool.ruff.format]` (`pyproject.toml:78-79`) sets `quote-style = "double"`.
- **mkdocs** `1.6.1` + **mkdocs-material** `9.7.7` + **mkdocstrings** `1.0.6` — docs toolchain (docs group, `pyproject.toml:58-60`), configured in `mkdocs.yml`.

## Key Dependencies

**Critical:**
- **pydantic** `2.13.5` — the entire data model in `encino_rpt/models.py` is pydantic v2 (`BaseModel`, `Field`, `PrivateAttr`, `Literal`). The recursive `Group.children` reference is resolved with `Group.model_rebuild()` (`encino_rpt/models.py:232`). Removing it would require rewriting the model layer.

**Optional extras (file-format writers, not network services):**
- **openpyxl** `3.1.5` — optional extra `excel` (`pyproject.toml:37`). Imported lazily inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py`). Raises `ImportError` with a Spanish hint to install `encino-rpt[excel]` when missing.
- **reportlab** `5.0.1` — optional extra `pdf` (`pyproject.toml:38`). Imported lazily inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py`). Same guarded-import pattern.

**Docs toolchain (transitive, not imported by the library):**
- **pillow** `12.3.0` — pulled in by mkdocs-material.
- **requests** / **urllib3** / **certifi** / **idna** / **charset-normalizer** — transitive deps of mkdocs (ghp-import). Never imported by `encino_rpt/` (verified: no network imports anywhere in the package).
- **jinja2** / **markdown** / **pygments** / **pymdown-extensions** / **babel** — mkdocs/mkdocs-material transitive deps.

## Configuration

**Environment:**
- No `.env`, `.env.*`, or env-var-driven config detected. The library is pure and stateless — no runtime environment variables required. `.env` is listed in `.gitignore:23` but no such file exists. Secrets for publishing live only in GitHub Actions (`TEST_PYPI_API_TOKEN`, `PYPI_API_TOKEN`).

**Build:**
- `pyproject.toml` — hatchling build config, project metadata, dependency groups, and tool configs for pytest/mypy/ruff/coverage.
- `mkdocs.yml` — docs config (material theme, `language: es`, mkdocstrings handler with `docstring_style: google`, 5-page nav).
- `.github/workflows/ci.yml` — CI with two jobs: `test` (matrix 3.10–3.13) and `quality` (singleton 3.13).
- `.github/workflows/docs.yml` — builds docs and deploys to GitHub Pages.
- `.github/workflows/publish.yml` — builds wheel/sdist and publishes to TestPyPI (main) and PyPI (tags `v*`).
- Existing built artifacts in `dist/`: `encino_rpt-0.2.0-py3-none-any.whl` and `encino_rpt-0.2.0.tar.gz` (gitignored; version 0.2.0, behind the current `version = "0.2.1"` in `pyproject.toml:10`). Deploy via GitHub Actions only: `uv build` in `.github/workflows/publish.yml:19`.

## Platform Requirements

**Development:**
- Python 3.10+ installed via `uv python install` (`.github/workflows/ci.yml:21`).
- `uv sync --all-extras --group dev` installs the full dev environment (`.github/workflows/ci.yml:24`).
- `uv run pytest` runs the suite; `uv run ruff check` lints; `uv run ruff format --check encino_rpt tests` checks formatting; `uv run mypy encino_rpt` type-checks; `uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80` enforces ≥80% coverage.

**Production:**
- Distributed as a PyPI package (`encino-rpt`), published via `.github/workflows/publish.yml`. Docs hosted on GitHub Pages (`https://hvalles.github.io/encino_rpt/`). No application hosting — this is a library.
- Windows local dev (this repo lives on `win32`) but CI runs Linux; no OS-specific code detected in `encino_rpt/` (pure stdlib + pydantic).

---

*Stack analysis: 2026-09-17*
