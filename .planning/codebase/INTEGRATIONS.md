# External Integrations

**Analysis Date:** 2026-09-17

## APIs & External Services

**None.**

`encino-rpt` is a self-contained, in-memory reporting library. It makes no outbound network calls, has no HTTP client, and imports no SDKs. Verified: the only third-party imports in `encino_rpt/` are the optional `openpyxl` and `reportlab` (local file-format libraries, not network services), both lazy-imported inside functions.

The library consumes data already materialized as `list[dict]` — the output of queries run elsewhere. It deliberately does **not** connect to databases or APIs to fetch data.

## Data Storage

**Databases:**
- None. No ORM, no DB driver, no connection strings. Input is `list[dict]` passed directly to `Report(rows, ...)` (`encino_rpt/report.py`) or read from files via `Report.read()` (`encino_rpt/report.py:44-90`). Heavy aggregation is a documented non-goal, delegated to SQL `ROLLUP`/`CUBE` in whatever system produces the rows.

**File Storage:**
- Local filesystem only, via the built-in readers. `_FORMAT_BY_EXT` maps file extensions to readers (`encino_rpt/readers.py:318-325`); six built-in readers are registered at import: `csv`, `tsv`, `json`, `jsonl`, `tuples`, `excel` (`encino_rpt/readers.py:375-380`). No cloud object storage (no S3/GCS/Blob).

**Caching:**
- None. Rendering and aggregation are in-memory and recomputed per `run()`.

## Authentication & Identity

**Auth Provider:**
- None. This is a library with no concept of users, sessions, or permissions. There is no auth code anywhere in `encino_rpt/`.

## Monitoring & Observability

**Error Tracking:**
- None. No Sentry/Rollbar/Datadog SDK.

**Logs:**
- None. No `logging` calls in `encino_rpt/` — errors are surfaced as Python exceptions (`ValueError`, `KeyError`, `IndexError`, `TypeError`, `ExpressionError`, `AggregationError`, `ImportError`).

## CI/CD & Deployment

**Hosting:**
- Documentation hosted on **GitHub Pages** (`https://hvalles.github.io/encino_rpt/`, configured in `mkdocs.yml:3` and deployed by `.github/workflows/docs.yml`).

**CI Pipeline:**
- **GitHub Actions** (`.github/workflows/`):
  - `ci.yml` — two jobs. `test`: matrix Python 3.10/3.11/3.12/3.13, `uv sync --all-extras --group dev`, `uv run pytest`, `uv run ruff check`. `quality`: Python 3.13 singleton, `uv run mypy encino_rpt`, `uv run ruff format --check encino_rpt tests`, coverage with `--cov-fail-under=80`.
  - `docs.yml` — `uv sync --group docs`, `uv run mkdocs build`, deploy to GitHub Pages (`actions/configure-pages@v5`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`).
  - `publish.yml` — `uv build` then publishes to **TestPyPI** (on `main` push) and **PyPI** (on `v*` tags) via `pypa/gh-action-pypi-publish@release/v1`.

## Environment Configuration

**Required env vars:**
- None at runtime. The library requires no environment variables.

**Secrets location:**
- GitHub Actions repository secrets only: `TEST_PYPI_API_TOKEN` (`publish.yml:40`) and `PYPI_API_TOKEN` (`publish.yml:55`). No secrets are stored in the repo.

## Webhooks & Callbacks

**Incoming:**
- None. No HTTP endpoints, no webhook receivers.

**Outgoing:**
- None. The library never calls external services.

## Reader Integration Points (extension surface)

While not "external integrations" in the network sense, the library has two pluggable extension points worth noting:

- **Custom readers:** `Report.register_reader(name, reader)` (`encino_rpt/report.py:80-90`) delegates to `register_reader()` which mutates the module-level `_READERS` registry (`encino_rpt/readers.py:38`). A reader is any object implementing the `Reader` `Protocol` (`read(source, **opts) -> list[dict]`, `encino_rpt/readers.py:13`).
- **Optional file-format dependencies:** Excel I/O requires the `excel` extra (`openpyxl>=3.1.5`); PDF output requires the `pdf` extra (`reportlab>=5.0.1`). Both raise `ImportError` with install hints when missing (`encino_rpt/renderers/excel.py:43-46`, `encino_rpt/renderers/pdf.py:45-48`, `encino_rpt/readers.py:297-299`).

---

*Integration audit: 2026-09-17*
