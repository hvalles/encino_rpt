# Technology Stack

**Analysis Date:** 2026-09-16

## Languages

**Primary:**
- Python `>=3.10` — the entire library is pure Python (`encino_rpt/`). Configured in `pyproject.toml` (`requires-python = ">=3.10"`, line 13). Classifiers declare support for 3.10–3.13.

**Secondary:**
- None detected. No TypeScript/JS, HTML templates are generated as strings inside `encino_rpt/renderers/html.py` (not templated files).

## Runtime

**Environment:**
- CPython. Local dev venv at `.venv/` (gitignored). CI runs on `ubuntu-latest` with Python 3.10/3.11/3.12/3.13 (`.github/workflows/ci.yml`). No `.python-version` or `.nvmrc` file present.
- Library outputs XLSX/PDF are produced at runtime by optional renderers only — no server runtime.

**Package Manager:**
- `uv` — lockfile `uv.lock` (version 1) at repo root.
- Lockfile: present (`uv.lock`). All dependency versions below are pinned there.

## Frameworks

**Core:**
- **pydantic** `2.13.5` — canonical report data model (`ReportResult`, `Group`, `Total`, `Chart`, etc.) in `encino_rpt/models.py`. Declared `pydantic>=2` in `pyproject.toml` line 34. Used for validation and JSON serialization (`model_dump()`).
- **encino-orm** `0.2.6` — declared dependency (`encino-orm>=0.2.1`) but NOT imported anywhere in `encino_rpt/` or `tests/`. Companion package whose `fetch_all`/`fetch_many`/`paginate` output (`list[dict]`) is the library's input contract (per `README.md` and `docs/design/10-report.md`).

**Testing:**
- **pytest** `9.1.1` — dev dependency (`pyproject.toml` line 52). Config in `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = ["."]`.
- Test files: `tests/test_report.py`, `tests/test_report_renderers.py`, `tests/test_security.py`.

**Build/Dev:**
- **hatchling** — build backend declared in `pyproject.toml` `[build-system]` (line 2–3). Wheel packages `["encino_rpt"]`.
- **ruff** `0.16.7` — linter, dev dependency. NO config file detected (no `[tool.ruff]` section in `pyproject.toml`, no `ruff.toml`/`.ruff.toml`) — runs with defaults via `uv run ruff check` in CI.
- **mkdocs** `1.6.1` + **mkdocs-material** `9.7.7` + **mkdocstrings** `1.0.6` — docs toolchain (docs dependency group, `pyproject.toml` lines 56–59), configured in `mkdocs.yml`.

## Key Dependencies

**Critical:**
- **pydantic** `2.13.5` (`pydantic-core` `2.46.5`) — the entire data model in `encino_rpt/models.py` is pydantic v2 (`BaseModel`, `Field`, `PrivateAttr`, `Literal` types). Removing it would require rewriting the model layer.

**Infrastructure:**
- **openpyxl** `3.1.5` — optional extra `excel` (`pyproject.toml` line 38). Imported lazily inside `encino_rpt/renderers/excel.py:41-45` (`Workbook`, `Font` from `openpyxl`). Raises `ImportError` with a hint to install `encino-rpt[excel]` when missing.
- **reportlab** `5.0.1` — optional extra `pdf` (`pyproject.toml` line 39). Imported lazily inside `encino_rpt/renderers/pdf.py:29-38` (`colors`, `pagesizes.A4`, `styles`, `platypus` — `Paragraph`, `SimpleDocTemplate`, `Table`, `TableStyle`). Same guarded-import pattern.
- **pillow** `12.3.0` — transitive dependency in `uv.lock` (pulled in by the docs/render toolchain), not directly used by `encino_rpt/`.
- **encino-orm** `0.2.6` pulls the following DB drivers transitively (see `uv.lock`): `aiomysql` 0.3.1, `aiosqlite` 0.22.1, `asyncpg` 0.31.0, `pymysql` 1.2.0. These are present because encino-orm supports multiple backends; `encino_rpt` itself never queries a database.

## Configuration

**Environment:**
- Single source of truth: `pyproject.toml` (project metadata, dependencies, optional extras `excel`/`pdf`, dev/docs dependency groups, pytest options).
- No `.env`, `.env.*`, or env-var-driven config detected. The library is pure and stateless — no runtime environment variables required.
- Docs config separate: `mkdocs.yml` (site metadata, material theme, mkdocstrings handler with `docstring_style: google`, nav for 5 pages, markdown extensions).

**Build:**
- `pyproject.toml` — hatchling build config, wheel packages `encino_rpt`.
- Existing built artifacts in `dist/`: `encino_rpt-0.2.0-py3-none-any.whl` and `encino_rpt-0.2.0.tar.gz` (gitignored, version behind current 0.2.1).
- Deploy via GitHub Actions only: `uv build` in `.github/workflows/publish.yml`.

## Platform Requirements

**Development:**
- Python 3.10+ installed via `uv python install` (see `.github/workflows/ci.yml`).
- `uv sync --all-extras --group dev` installs the full dev environment (per CI).
- Windows local dev (this repo lives on `win32`), but CI runs Linux — no OS-specific code detected in `encino_rpt/` (pure stdlib + pydantic).

**Production:**
- Distributed as a PyPI package (`encino-rpt`), published via `.github/workflows/publish.yml` to TestPyPI (main branch) and PyPI (tags `v*`). No hosting/deployment of an app — this is a library.

---

*Stack analysis: 2026-09-16*