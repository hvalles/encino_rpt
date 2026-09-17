# External Integrations

**Analysis Date:** 2026-09-17

## APIs & External Services

**Runtime (library code):**
- **None.** A full import scan of `encino_rpt/` found zero references to `urllib`, `requests`, `socket`, `http`, `httpx`, `aiohttp`, or any network I/O. The library is pure, stateless, and side-effect-free — it neither makes nor receives network calls.

**Build/publish (CI only):**
- **PyPI** (`https://pypi.org/`) and **TestPyPI** (`https://test.pypi.org/legacy/`) — package distribution targets only, contacted during CI via `pypa/gh-action-pypi-publish` (`pyproject.toml:37-39` lists Repository/Documentation URLs; `.github/workflows/publish.yml:36-55`).
- **GitHub Pages** (`https://hvalles.github.io/encino_rpt/`) — docs hosting target, deployed from `.github/workflows/docs.yml`.

## Data Storage

**Databases:**
- **None.** No DB client, ORM, or connection code. By design, `encino_rpt` consumes already-materialized rows (`list[dict]`); heavy aggregation is a documented non-goal delegated to the caller's SQL (`ROLLUP`/`CUBE`). Input comes via the reader layer in `encino_rpt/readers.py` (csv/tsv/json/jsonl/tuples/excel/custom).

**File Storage:**
- **Local filesystem only**, and only as an *input* source: readers accept file paths / file-likes (`encino_rpt/readers.py:350-371`). No remote/blob storage, no write-back of files except optional renderer `write(result, file)` to a user-supplied file-like object.

**Caching:**
- **None.** No in-memory or external cache. There is a single module-level reader registry `_READERS` (`encino_rpt/readers.py:35`), populated at import and via `register_reader` — it is a registry, not a cache.

## Authentication & Identity

**Auth Provider:**
- **None.** No authentication, identity, or session handling anywhere in `encino_rpt/`. The only credential-bearing concern is PyPI publishing tokens in CI secrets (see below).

## Monitoring & Observability

**Error Tracking:**
- **None.** No Sentry, no exception reporting.

**Logs:**
- **None.** No `logging` imports in `encino_rpt/`. Errors surface strictly as exceptions (`ValueError`, `KeyError`, `IndexError`, `TypeError`, `ImportError`, `ExpressionError`, `AggregationError`). The library is pure and side-effect-free — no `print`, no runtime logging.

## CI/CD & Deployment

**Hosting:**
- PyPI (`encino-rpt` wheel/sdist) + GitHub Pages (docs). No application server.

**CI Pipeline:**
- **GitHub Actions** (three workflows):
  - `.github/workflows/ci.yml` — `test` job (Python 3.10–3.13 matrix: `pytest` + `ruff check`) and `quality` job (Python 3.13: `mypy`, `ruff format --check`, coverage ≥80%).
  - `.github/workflows/docs.yml` — builds `mkdocs` site and deploys to GitHub Pages via `actions/deploy-pages@v4`.
  - `.github/workflows/publish.yml` — `uv build`, then publishes to TestPyPI on `main` and to PyPI on `v*` tags.

## Environment Configuration

**Required env vars:**
- **None at runtime.** The library requires no environment variables.

**Secrets location:**
- GitHub Actions repository secrets, referenced in `.github/workflows/publish.yml`:
  - `TEST_PYPI_API_TOKEN` (`.github/workflows/publish.yml:40`)
  - `PYPI_API_TOKEN` (`.github/workflows/publish.yml:55`)
- No `.env` file present (`.env` is gitignored via `.gitignore`).

## Webhooks & Callbacks

**Incoming:**
- **None.**

**Outgoing:**
- **None.**

---

*Integration audit: 2026-09-17*
