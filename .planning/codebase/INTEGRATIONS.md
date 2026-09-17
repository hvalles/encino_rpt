# External Integrations

**Analysis Date:** 2026-09-17

## APIs & External Services

**None.**

`encino-rpt` is a self-contained, offline library. It makes **no outbound network calls** and has no HTTP client. The entire `encino_rpt/` package imports only the Python standard library (`ast`, `operator`, `re`, `csv`, `io`, `json`, `html`, `datetime`, `decimal`) and `pydantic` — verified across all modules:

- `encino_rpt/expressions.py:5-6` — `import ast`, `import operator`
- `encino_rpt/template.py:5` — `import re`
- `encino_rpt/renderers/csv.py:5-6` — `import csv`, `import io`
- `encino_rpt/renderers/json.py:5` — `import json`
- `encino_rpt/renderers/_format.py:5-6` — `from datetime import ...`, `from decimal import ...`
- `encino_rpt/models.py:7` — `from pydantic import BaseModel, Field, PrivateAttr`

No `requests`, `httpx`, `boto3`, `stripe`, `supabase`, or any SDK is imported anywhere in `encino_rpt/`. (`requests`/`urllib3`/`certifi` exist in `uv.lock` only as transitive dependencies of the mkdocs docs toolchain.)

## Data Storage

**Databases:**
- None. The library never opens a database connection and ships no DB driver.
- Input contract is `list[dict]` — rows **already materialized** by the caller's query. See `Report.__init__` and README examples (`README.md` lines 10–14). Heavy aggregation is delegated to SQL `ROLLUP`/`CUBE` on the caller side (documented non-goal); the engine itself is in-memory.
- Note: the package `encino-orm` was previously referenced in design docs as the canonical producer of `list[dict]`, but it is **not** a dependency of this project (absent from `pyproject.toml` and `uv.lock`).

**File Storage:**
- None / local filesystem only. Output renderers return in-memory objects or strings; no files are written. `to_pdf`/`to_excel` return `bytes`/`Worksheet` for the caller to persist.

**Caching:**
- None.

## Authentication & Identity

**Auth Provider:**
- None. There is no user/auth concept in the library.

## Monitoring & Observability

**Error Tracking:**
- None.

**Logs:**
- None. No logging framework is used (no `logging` import in `encino_rpt/`); errors propagate as exceptions to the caller.

## CI/CD & Deployment

**Hosting:**
- **GitHub Pages** — documentation site built and deployed via `.github/workflows/docs.yml` (`mkdocs build` → `site/` → `actions/deploy-pages`). Site URL `https://hvalles.github.io/encino_rpt/` (`mkdocs.yml` line 3).
- **PyPI** (package distribution) — `encino-rpt` published via `.github/workflows/publish.yml`.
  - TestPyPI on every push to `main` (`publish.yml` lines 26–40), repository URL `https://test.pypi.org/legacy/`.
  - PyPI on tags matching `v*` (`publish.yml` lines 42–55).

**CI Pipeline:**
- **GitHub Actions** — three workflows under `.github/workflows/`:
  - `ci.yml` — test matrix Python 3.10/3.11/3.12/3.13 on `ubuntu-latest`; `uv sync --all-extras --group dev`, `uv run pytest`, `uv run ruff check`.
  - `docs.yml` — builds and deploys the mkdocs site to GitHub Pages.
  - `publish.yml` — `uv build` + `pypa/gh-action-pypi-publish` to TestPyPI/PyPI.

## Environment Configuration

**Required env vars:**
- None at runtime. The library reads no environment variables.

**Secrets location:**
- GitHub Actions secrets only, used for package publishing:
  - `TEST_PYPI_API_TOKEN` (`publish.yml` line 40)
  - `PYPI_API_TOKEN` (`publish.yml` line 55)
- No `.env` files present in the repo (`.env` is gitignored via `.gitignore` line 23).

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

## External Output Formats (library-level integrations)

The only "external" surfaces are the file formats produced by optional renderers, all behind lazy/guarded imports:

- **Excel (.xlsx)** — `openpyxl` `3.1.5`, guarded import in `encino_rpt/renderers/excel.py:42-46` (extra `excel`).
- **PDF** — `reportlab` `5.0.1`, guarded import in `encino_rpt/renderers/pdf.py:30-41` (extra `pdf`).
- **HTML / CSV / JSON / text** — stdlib-only, no external dependency.

---

*Integration audit: 2026-09-17*
