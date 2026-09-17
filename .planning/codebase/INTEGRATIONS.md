# External Integrations

**Analysis Date:** 2026-09-17

## APIs & External Services

**Runtime (in-library):**
- None. The library makes **no network calls** at runtime. Verified: no `urllib`/`requests`/`httpx`/`socket`/`aiohttp`/`http` imports anywhere in `encino_rpt/`. All data flows through the caller-supplied `list[dict]` (or the readers below).

**Data Input (local readers):**
- `encino_rpt/readers.py` — multi-format readers (no external service, purely local parsing):
  - `csv` / `tsv` — `_DelimitedReader` using stdlib `csv.DictReader` (`readers.py:157-186`)
  - `json` — `JsonReader` using stdlib `json.loads` (`readers.py:189-215`)
  - `jsonl` — `JsonLinesReader` (`readers.py:218-244`)
  - `tuples` — `TuplesReader` (`readers.py:247-274`)
  - `excel` — `ExcelReader` using `openpyxl.load_workbook` (optional extra `excel`, `readers.py:277-315`)
- Entry point `Report.read(source, format=None, ...)` (`encino_rpt/report.py:44-78`) delegates to `readers.read()` and resolves the reader by file extension via `_FORMAT_BY_EXT` (`readers.py:318-325`). Custom readers are registered via `register_reader` (`readers.py:38-45`) / `Report.register_reader` (`report.py:80-90`).

**Build/CI-time network:**
- **PyPI / TestPyPI** — package distribution targets. Published via `pypa/gh-action-pypi-publish@release/v1` in `.github/workflows/publish.yml:37,53`. TestPyPI repository URL `https://test.pypi.org/legacy/` (`publish.yml:39`).
- **GitHub Pages** — docs hosting. Deployed via `actions/deploy-pages@v4` in `.github/workflows/docs.yml:48`; site URL `https://hvalles.github.io/encino_rpt/` (`mkdocs.yml:3`).

## Data Storage

**Databases:**
- None. No ORM, no DB client, no connection strings. The library is explicitly database-agnostic: it consumes already-materialized `list[dict]` and delegates heavy aggregation to SQL (`ROLLUP`/`CUBE`) as a documented non-goal.

**File Storage:**
- Local filesystem only. Readers accept paths (`str`/`Path`), file-like objects (`.read()`), or raw strings (`encino_rpt/readers.py:103-154`). No cloud/object storage, no S3/GCS/Azure SDKs.

**Caching:**
- None. No Redis/memcached, no in-process cache beyond per-request local variables in `build()` (`encino_rpt/aggregation.py`).

## Authentication & Identity

**Auth Provider:**
- None. No user auth, no OAuth/JWT, no session management. The library is a pure function-like transform (`rows` → `ReportResult`).

## Monitoring & Observability

**Error Tracking:**
- None. No Sentry/DataDog/OpenTelemetry instrumentation.

**Logs:**
- No logging framework. Errors propagate as exceptions (`ExpressionError`, `AggregationError`, `ValueError`, `ImportError`) rather than log lines. See `encino_rpt/expressions.py:51`, `encino_rpt/aggregation.py:30`.

## CI/CD & Deployment

**Hosting:**
- GitHub Actions (runners `ubuntu-latest`). Three workflows:
  - `.github/workflows/ci.yml` — `test` (matrix Python 3.10–3.13) and `quality` (singleton 3.13) jobs; installs via `uv sync --all-extras --group dev`.
  - `.github/workflows/docs.yml` — builds mkdocs and deploys to GitHub Pages (`actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`).
  - `.github/workflows/publish.yml` — `uv build`, then `pypa/gh-action-pypi-publish` to TestPyPI (branch `main`) and PyPI (tags `v*`).

**CI Pipeline:**
- GitHub Actions (see above). Uses `astral-sh/setup-uv@v4` for uv install. Tests run with `uv run pytest`; coverage gate `--cov-fail-under=80`.

## Environment Configuration

**Required env vars:**
- None at runtime. The library requires no environment variables.

**Secrets location:**
- GitHub Actions secrets only: `TEST_PYPI_API_TOKEN` (`.github/workflows/publish.yml:40`) and `PYPI_API_TOKEN` (`.github/workflows/publish.yml:55`). No `.env` file, no local secret files (`.gitignore` lists `.env` at line 23 as a precaution only).

## Webhooks & Callbacks

**Incoming:**
- None. No HTTP endpoints, no webhook receivers.

**Outgoing:**
- None. No webhook dispatches, no outbound notifications. The only outbound network activity is at CI time (PyPI publish, GitHub Pages deploy), not in library code.

## Optional Dependency Isolation

- **openpyxl** (extra `excel`) — imported lazily only in `encino_rpt/renderers/excel.py` and `encino_rpt/readers.py:296`; raises `ImportError` with install hint if missing.
- **reportlab** (extra `pdf`) — imported lazily only in `encino_rpt/renderers/pdf.py`; raises `ImportError` with install hint if missing.
- This keeps the base install dependency-free except pydantic, so importing `encino_rpt` never triggers a network or optional-module import.

---

*Integration audit: 2026-09-17*
