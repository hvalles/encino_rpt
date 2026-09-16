# External Integrations

**Analysis Date:** 2026-09-16

## APIs & External Services

**Direct API calls:** None. The library `encino_rpt/` makes zero network or HTTP requests — no `requests`, `httpx`, `urllib`, or socket usage detected. All modules (`report.py`, `section.py`, `aggregation.py`, `charts.py`, `pivot.py`, `template.py`, `expressions.py`, `models.py`, `_specs.py`, `renderers/*.py`) are pure in-memory processing of `list[dict]`.

**Companion package relationship:**
- [encino-orm](https://github.com/hvalles/encino_rpt) (declared dependency) — the library's input contract is "rows materialized by `Db.fetch_all` / `fetch_many` / `paginate`" per `README.md` and `docs/design/10-report.md`. No import or runtime coupling; rows flow in as plain `list[dict]`.

## Data Storage

**Databases:**
- None queried by `encino_rpt` itself. However, `uv.lock` pins DB drivers as transitive dependencies of the `encino-orm` companion, so they exist in the lockfile:
  - `asyncpg` 0.31.0 (PostgreSQL)
  - `aiomysql` 0.3.1 and `pymysql` 1.2.0 (MySQL/MariaDB)
  - `aiosqlite` 0.22.1 (SQLite)
- The report tree is serializable to JSON via pydantic `model_dump()` (`README.md` quick start, `ReportResult` in `encino_rpt/models.py`) — this is the "output" format, not a database.

**File Storage:**
- Local filesystem only. Renderers produce in-memory artifacts: CSV strings (`encino_rpt/renderers/csv.py`), openpyxl `Worksheet` objects (`encino_rpt/renderers/excel.py`), bytes PDFs via `io.BytesIO` (`encino_rpt/renderers/pdf.py:45`), HTML strings (`encino_rpt/renderers/html.py`). No file/S3/blob storage integration.

**Caching:**
- None.

## Authentication & Identity

**Auth Provider:**
- Not applicable. The library has no user concept, no auth, no sessions.

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Bugsnag/etc.).

**Logs:**
- None in library code; no `logging` module usage detected in `encino_rpt/`. Errors are raised as typed exceptions (`ExpressionError` in `encino_rpt/expressions.py:50`, `ImportError` for missing optional extras).

## CI/CD & Deployment

**Hosting:**
- GitHub Actions (`.github/workflows/`). Three pipelines:
  - `ci.yml` — matrix tests on Python 3.10–3.13 (`uv sync --all-extras --group dev`, `uv run pytest`, `uv run ruff check`).
  - `docs.yml` — builds mkdocs site (`uv run mkdocs build`) and deploys to **GitHub Pages** via `actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`. Triggered on push to `main`.
  - `publish.yml` — `uv build`, uploads `dist/` artifact, publishes to **TestPyPI** (`https://test.pypi.org/legacy/`) on `main` pushes and to **PyPI** on `v*` tags.

**CI Pipeline Secrets (GitHub Actions secrets):**
- `TEST_PYPI_API_TOKEN` — TestPyPI publish (`publish.yml:40`), referenced for `main` branch.
- `PYPI_API_TOKEN` — PyPI publish (`publish.yml:54`), referenced for `v*` tags.

## Environment Configuration

**Required env vars:**
- None at runtime.
- CI-only: `TEST_PYPI_API_TOKEN`, `PYPI_API_TOKEN`, plus GitHub Pages `id-token`/`pages` permissions granted in `docs.yml`.

**Secrets location:**
- No `.env` files in the repo (`publish.yml` / `docs.yml` use GitHub Actions secrets). `.gitignore` excludes `.env` (line 23).

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

## Security Boundary Notes

**Formula injection protection (OWASP):**
- `encino_rpt/renderers/_sanitize.py` guards Excel/CSV output against formula injection: prefixes `=`, `+`, `-`, `@`, `\t`, `\r` are detected (`is_dangerous`, line 8) and neutralized — CSV values get a leading `'` (`sanitize_csv`, line 13), Excel cells are forced to string type (`write_excel_cell`, line 20). This is an internal, destination-side mitigation rather than an external integration, but it affects how output feeds downstream spreadsheet tools (Excel/Google Sheets/LibreOffice).

**Expression evaluation sandbox:**
- `encino_rpt/expressions.py` implements a safe expression evaluator (AST whitelist, no `eval`) with anti-DoS limits (`_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000`, lines 45–47). Docs: `docs/security.md`.

---

*Integration audit: 2026-09-16*