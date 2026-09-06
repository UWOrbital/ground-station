# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Team context

UW Orbital is a student CubeSat team. The software sub-team splits into **firmware** (runs on the satellite) and **ground station** (everything on the ground). This repo is the ground station codebase — its job is to receive data from the satellite, process it, and let humans act on it. Ground station coordinates with firmware (a separate sub-team, not in this repo) through the shared C interfaces so downlinks decode correctly on both sides.

Ground station has three product surfaces:
- **Backend** (`backend/`) — FastAPI service that ingests downlink data, persists it, and serves both frontends. This is the primary surface in this repo.
- **MCC** — Mission Control Center. An invite-only tool behind Keycloak; experts use it to monitor and command the satellite. Backend lives at `backend/app/api/mcc/*`; the MCC frontend is the operator-facing client.
- **ARO** — Amateur Radio Operator. Public-facing surface for amateur radio operators who want to request actions of the satellite. Backend lives at `backend/app/api/aro/*`.

When summarizing work to the user, frame what changed in terms of the team mission: which surface it affects (MCC operators, ARO amateurs, firmware-integration plumbing) and where it sits in the satellite-to-human pipeline. Don't just list code edits — connect them to who on the team benefits.

## Repository layout

Three-part monorepo for UW Orbital's CubeSat ground station:

- `backend/` — FastAPI service (Python 3.12, packaged as `backend` via setuptools). Imports inside the backend are written as if `backend/` is on `sys.path` (e.g. `from app.api.lifespan import lifespan`, `from app.config.config import settings`). The backend package is installed editable via `uv sync --extra dev`, so the `pyproject.toml` at the repo root configure tooling for the backend only.
- `frontend/aro/` and `frontend/mcc/` — two independent Vite + React 19 + TS apps. ARO (Amateur Radio Operator) is the public-facing app; MCC (Mission Control Center) is the operator app behind Keycloak.

## Common commands

All Python commands assume `uv` is installed and the venv is synced (`uv sync --extra dev` from repo root).

### Backend

```sh
# Run the dev server (from repo root)
uv run fastapi dev backend/main.py

# Seed reference data (callsigns, main commands, telemetries) into the local DB
uv run python backend/migrate.py            # all three
uv run python backend/migrate.py callsigns  # one of: callsigns | commands | telemetries

# DB schema migrations (run from repo root, where alembic.ini lives)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "msg"

# Tests — pytest is configured with testpaths = ["tests"] in pyproject.toml.
# tests/conftest.py spins up a Postgres instance via pytest-postgresql per test
# and runs `alembic upgrade head` inside that DB, so the system needs Postgres + initdb
# on PATH but the dev DB is NOT touched.
uv run pytest                                              # full suite
uv run pytest backend/tests/test_ephemeris.py        # one file
uv run pytest backend/tests/test_ephemeris.py::test_name  # one test
uv run pytest -k "expression"                              # by name

# Type checking and lint (CI runs `mypy .` from the repo root in strict mode)
uv run mypy .
uv run ruff check .
uv run ruff format .
```

### Frontends

Each frontend is an independent npm project — run commands from `frontend/aro/` or `frontend/mcc/`.

```sh
npm install
npm run dev       # vite dev server (aro on 5173, mcc on 5174 in docker compose)
npm run build     # tsc -b && vite build
npm run lint      # eslint .
npm run test      # vitest
```

### Docker dev environment

Keycloak is decoupled into its own `docker-compose.keycloak.yml` (mirrors an external Keycloak). `start.sh` brings Keycloak up, waits for the `mcc` realm to import, then starts the main stack. `docker-compose.yml` brings up backend + both frontends + db. The backend reads `.env` at the repo root (not `backend/.env`). Run from the repo root:

```sh
./start.sh          # keycloak stack, then the main stack
```

`KEYCLOAK_URL` is a single field defaulting to `http://localhost:8080` — right for a host-run backend (`uv run fastapi dev`), the browser, and CI, so no host-file edits there. The dockerized api service overrides it to `http://host.docker.internal:8080` (via `environment:` + `extra_hosts: host.docker.internal:host-gateway`), mirroring `GS_DATABASE_LOCATION`. Only that full-`docker compose up` path needs `127.0.0.1 host.docker.internal` in the browser's `/etc/hosts` (Docker Desktop often adds it already).

## Architecture notes

### FastAPI app composition

`backend/main.py` is intentionally tiny — it instantiates `FastAPI(lifespan=lifespan)` and delegates to `backend/app/api/backend_setup.py`, which wires routers and middleware. To add an endpoint, create a router under `backend/app/api/{aro,mcc}/endpoints/` and register it in `setup_routes` with the correct prefix; the two product surfaces are mounted at `backend/app/api/aro/*` and `backend/app/api/mcc/*`.

Middleware order matters and is enforced in `setup_middlewares`: CORS first, then `SessionMiddleware` (needed for OAuth state), then `AuthMiddleware`, then `LoggerMiddleware`. Don't reorder casually.

The `lifespan` context initializes `fastapi-cache` with an in-memory backend and calls `setup_database(get_db_session())` to create the three Postgres schemas (`main`, `transactional`, `aro_user`). Table DDL is owned by **Alembic** — `setup_database` only creates schemas; the old `_create_tables` path is left as a deprecated comment.

### Configuration

`backend/app/config/config.py` builds a single `settings` object by composing `CORSConfig`, `LoggerConfig`, `DatabaseConfig`, `KeycloakConfig`, `AROAuthConfig`, and `EmailConfig`. Each pulls from env vars via pydantic-settings. `python-dotenv`'s `load_dotenv()` runs at import time — when running from the repo root it finds `backend/.env` via the working dir; the docker compose backend service injects env from the repo-root `.env` plus an override (`GS_DATABASE_LOCATION=host.docker.internal`).

`template.env` documents every variable the backend needs. `KEYCLOAK_CLIENT_SECRET`, ARO Google OAuth, and SMTP secrets are not in the template and must be filled in locally; the Keycloak client secret lives inside `backend/mcc_keycloak/mcc-realm.json`.

### Data layer

- `backend/app/data/tables/` — SQLModel table classes split across three Postgres schemas: `main_tables.py` (reference data), `transactional_tables.py` (e.g. `CommsSession`), `aro_user_tables.py`, `mcc_user_tables.py`. Schema names are module-level constants (e.g. `MAIN_SCHEMA_NAME`) and are referenced by both `engine.py` and Alembic.
- `backend/app/data/data_wrappers/` — repository-style wrappers around SQLModel. New table accessors should extend `abstract_wrapper.py`; tests monkeypatch `data.data_wrappers.abstract_wrapper.get_db_session` (see `conftest.py`).
- `backend/migrations/` — Alembic migrations. `tests/conftest.py` runs `alembic upgrade head` inside the per-test Postgres instance, so any new table needs both a SQLModel class and a migration or the tests will fail.

### Auth

Two distinct flows:
- **MCC**: Keycloak (OIDC). Realm definition is checked in at `backend/app/mcc_keycloak/mcc-realm.json` and auto-imported by the keycloak compose service.
- **ARO**: Google OAuth via Authlib, JWT-signed sessions. Config in `backend/app/config/aro_auth_config.py`.

`backend/app/api/middleware/auth_middleware.py` enforces both. Session cookies are protected by `SessionMiddleware` keyed on `settings.auth.jwt_secret_key`.

### Sample data

Sample data can be found in `backend/references/`.

## Testing conventions

- pytest is verbose by default (`-v` in `pyproject.toml`).
- `backend/tests/conftest.py` autouses a fixture that swaps `get_db_session` to point at a per-test Postgres DB, so wrappers under test must call `get_db_session()` (not hold a cached engine).
- The dummy env vars in `conftest.py` are set with `setdefault` *before* importing the engine module, so test-only env never leaks into dev. Don't reorder those imports.
- mypy runs in `strict` mode and excludes `tests/*`.
- Ruff is scoped to `backend/` only (frontend, `tests`, and `migrations` are excluded) and enforces docstrings on classes/functions/methods (rules `D101 D102 D103 D105` plus `D213`).

## Pre-commit

`.pre-commit-config.yaml` runs whitespace fixers + `ruff-check --fix` + `ruff-format`. The hooks deliberately skip `libs/`, `hal/`, and `backend/references/csvs/callsigns.csv` from the large-file check. After cloning, run `uv run pre-commit install`.

## Code style rules (enforced)

- **Type hints required on every function parameter and return type.** No untyped `def foo(x):` — write `def foo(x: int) -> str:`. mypy strict mode will reject missing annotations anyway, but apply this in test code too (which mypy doesn't check).
- **Docstrings required on every function, method, and class you write or modify.** Ruff is configured with `D101 D102 D103 D105` + `D213`, so this is enforced for `backend/*.py`. Format: triple-quoted, summary line on the same opening line (`D213`), then a `:param <name>:` line for **every** parameter the function takes and a `:return:` line whenever the function returns a value. Don't skip params even if the name looks self-explanatory — the team enforces the full block. Example:

  ```python
  def pack_command(cmd_id: int, payload: bytes) -> bytes:
      """Serialize a command into the OBC wire format.

      :param cmd_id: numeric command identifier from the shared command table.
      :param payload: raw command body; must already match the struct layout.
      :return: framed bytes ready for AX.25 encoding.
      """
  ```
- **Tests required for new code.** Any new or modified Python under `backend/` ships with a matching pytest in `backend/tests/` — covering the golden path and at least the edge cases the change introduces. CI runs the full suite; untested behavior won't pass review. If a change is genuinely untestable (e.g. wiring a third-party SDK), say so explicitly in the PR.

## Maintaining this file

**Hard cap: `CLAUDE.md` must stay under 250 lines.** If an edit would push it past that, compact first — merge related bullets, drop anything rederivable from `pyproject.toml`, `package.json`, or a quick grep, and prefer one tight sentence over a paragraph. Re-check `wc -l CLAUDE.md` after any addition.

## Conventions called out by the team

- Branch naming: `<developer_name>/<feature_description>` (e.g. `danielg/implement-random-device-driver`).
- A PR template enforces required details; PRs expect ≥3 reviewers including a software lead.

