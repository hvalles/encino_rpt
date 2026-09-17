# External Integrations

**Analysis Date:** 2026-09-17

## Summary

`encino-rpt` is a **pure, offline library** with **zero runtime external integrations**. It consumes `list[dict]` (already-materialized query results) and produces a canonical pydantic tree plus optional render output. There are no network calls, no database connections, no HTTP clients, and no auth/identity dependencies anywhere in `encino_rpt/` (verified by searching for `import requests`, `urllib`, `socket`, `urlopen`, `os.environ`/`getenv` — none found).

The only "integrations" are:
1. Optional file-format writers (`openpyxl`, `reportlab`) — local libraries, not services.
2. CI/CD and publishing via GitHub Actions + PyPI (TestPyPI/PyPI) + GitHub Pages.

## APIs & External Services

**Runtime APIs:**
- None. No external API calls, no SDK clients, no HTTP at all in the library.

**Package registry (build/publish only):**
- PyPI (`https://pypi.org`) — release target for tags `v*` via `pypa/gh-action-pypi-publish` in `.github/workflows/publish.yml:52-55`.
  - Auth: `secrets.PYPI_API_TOKEN` (GitHub Actions secret).
- TestPyPI (`https://test.pypi.org/legacy/`) — pre-release target for the `main` branch via `.github/workflows/publish.yml:36-40`.
  - Auth: `secrets.TEST_PYPI_API_TOKEN` (GitHub Actions secret).

**Source/docs hosting:**
- GitHub (`https://github.com/hvalles/encino_rpt`) — declared in `pyproject.toml:41` and `mkdocs.yml:4`.

## Data Storage

**Databases:**
- None. The library is database-agnostic by design: it ingests `list[dict]` (rows already materialized by the caller's SQL/ORM). Heavy aggregates are a documented non-goal, delegated to SQL `ROLLUP`/`CUBE` upstream.

**File Storage:**
- Local filesystem only, and only at the caller's discretion. Renderers return in-memory objects — `HtmlRenderer`/`CsvRenderer`/`TextRenderer`/`JsonRenderer` return `str`, `PdfRenderer` returns `bytes`, `ExcelRenderer` returns an openpyxl `Worksheet` (`encino_rpt/models.py:189-202`). No file I/O is performed by the library itself. `Image.src`/`Link.href` (`encino_rpt/models.py:10-27`) may reference arbitrary URLs/paths but the library never fetches or resolves them.

**Caching:**
- None. No in-memory or external cache.

## Authentication & Identity

**Auth Provider:**
- None. No users, sessions, tokens, or identity in the library.

**Credentials:**
- Only at the CI/publish layer: `PYPI_API_TOKEN` and `TEST_PYPI_API_TOKEN` GitHub Actions secrets referenced in `.github/workflows/publish.yml:40,55`. No secrets live in the repo (`.env` is gitignored and absent; no credential files present).

## Monitoring & Observability

**Error Tracking:**
- None.

**Logs:**
- None. The library has no `logging` usage — errors are raised as exceptions (`ValueError`, `KeyError`, `IndexError`, `ExpressionError`, `AggregationError`, `ImportError`). See `encino_rpt/expressions.py:50`, `encino_rpt/aggregation.py:23`.

## CI/CD & Deployment

**Hosting:**
- PyPI (package distribution) + GitHub Pages (documentation).
  - Docs: `.github/workflows/docs.yml` builds with `mkdocs build` and deploys via `actions/deploy-pages@v4` to `https://hvalles.github.io/encino_rpt/` (`docs.yml:31-48`).

**CI Pipeline:**
- GitHub Actions, three workflows:
  - `ci.yml` — `test` job (matrix Python 3.10/3.11/3.12/3.13: `uv run pytest` + `uv run ruff check`) and `quality` job (singleton Python 3.13: `uv run mypy encino_rpt`, `uv run ruff format --check`, `uv run pytest --cov=encino_rpt --cov-fail-under=80`).
  - `docs.yml` — build + deploy docs on `push` to `main`.
  - `publish.yml` — `uv build`, then publish to TestPyPI (`main`) / PyPI (tags `v*`).

## Environment Configuration

**Required env vars:**
- None for the library at runtime.

**Secrets location:**
- GitHub Actions secrets only: `PYPI_API_TOKEN`, `TEST_PYPI_API_TOKEN` (`.github/workflows/publish.yml:40,55`). No `.env` file, no committed credentials.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None. The library makes no outbound requests. `Link.href` and `Image.src` are data fields only — they are emitted into HTML output (`encino_rpt/renderers/html.py`) but never dereferenced.

---

*Integration audit: 2026-09-17*
