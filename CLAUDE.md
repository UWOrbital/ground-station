# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Team context

UW Orbital is a student CubeSat team. The software sub-team splits into **firmware** (runs on the satellite) and **ground station** (everything on the ground). This repo is the ground station codebase — its job is to receive data from the satellite, process it, and let humans act on it. Ground station coordinates with firmware (a separate sub-team, not in this repo) through the shared C interfaces in `backend/interfaces/` so downlinks decode correctly on both sides.

Ground station has three product surfaces:
- **Backend** (`backend/`) — FastAPI service that ingests downlink data, persists it, and serves both frontends. This is the primary surface in this repo.
- **MCC** — Mission Control Center. An invite-only tool behind Keycloak; experts use it to monitor and command the satellite. Backend lives at `/api/v1/mcc/*`; the MCC frontend is the operator-facing client.
- **ARO** — Amateur Radio Operator. Public-facing surface for amateur radio operators who want to request actions of the satellite. Backend lives at `/api/v1/aro/*`.

When summarizing work to the user, frame what changed in terms of the team mission: which surface it affects (MCC operators, ARO amateurs, firmware-integration plumbing) and where it sits in the satellite-to-human pipeline. Don't just list code edits — connect them to who on the team benefits.

## Repository layout

Three-part monorepo for UW Orbital's CubeSat ground station:

- `backend/` — FastAPI service (Python 3.12, packaged as `backend` via setuptools). Imports inside the backend are written as if `backend/` is on `sys.path` (e.g. `from api.lifespan import lifespan`, `from config.config import settings`). The backend package is installed editable via `uv sync --extra dev`, so the `backend.egg-info` and `pyproject.toml` at the repo root configure tooling for the backend only.
- `frontend/aro/` and `frontend/mcc/` — two independent Vite + React 19 + TS apps. ARO (Amateur Radio Operator) is the public-facing app; MCC (Mission Control Center) is the operator app behind Keycloak.
- `backend/interfaces/` — git submodule (`https://github.com/UWOrbital/interfaces.git`) containing C sources shared with the flight firmware. Built with CMake into `libobc-gs-interface.so`; the Python `obc_gs_interface/` package wraps it via `ctypes`/cffi. Always clone with `--recursive` or run `git submodule update --init --recursive`.

## Common commands

All Python commands assume `uv` is installed and the venv is synced (`uv sync --extra dev` from repo root).

### Backend

```sh
# Run the dev server (from repo root)
uv run fastapi dev backend/main.py

# Seed reference data (callsigns, main commands, telemetries) into the local DB
uv run python backend/migrate.py            # all three
uv run python backend/migrate.py callsigns  # one of: callsigns | commands | telemetries

# DB schema migrations (run from backend/, since alembic.ini lives there)
cd backend && uv run alembic upgrade head
cd backend && uv run alembic revision --autogenerate -m "msg"

# Tests — pytest is configured with testpaths = ["python_test"] in pyproject.toml.
# python_test/conftest.py spins up a Postgres instance via pytest-postgresql per test
# and runs `alembic upgrade head` inside that DB, so the system needs Postgres + initdb
# on PATH but the dev DB is NOT touched.
uv run pytest                                              # full suite
uv run pytest backend/python_test/test_ephemeris.py        # one file
uv run pytest backend/python_test/test_ephemeris.py::test_name  # one test
uv run pytest -k "expression"                              # by name

# Type checking and lint (CI runs `mypy .` from the repo root in strict mode)
uv run mypy .
uv run ruff check .
uv run ruff format .

# Build the native interfaces library (required before any test that exercises packing,
# AX.25, AES, FEC, or telemetry — the Python wrappers dlopen libobc-gs-interface.so):
cd backend/interfaces && mkdir -p build && cd build && cmake .. && make -j
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

`docker-compose.yml` at the repo root brings up backend + Keycloak + both frontends. The backend service reads `.env` at the repo root (not `backend/.env`). Run from the repo root:

```sh
docker compose up --build
```

### Keycloak realm sync

`scripts/dev/kc-sync.sh` pulls the live MCC realm/clients/roles out of a running Keycloak (admin `mcc-admin` / `uworbital`) and writes them back to `backend/mcc_keycloak/mcc-realm.json`, which is the source-controlled realm that compose imports on boot. Run it from `scripts/dev/` after changing realm settings in the Keycloak UI; commit the resulting JSON.

## Architecture notes

### FastAPI app composition

`backend/main.py` is intentionally tiny — it instantiates `FastAPI(lifespan=lifespan)` and delegates to `api/backend_setup.py`, which wires routers and middleware. To add an endpoint, create a router under `backend/api/v1/{aro,mcc}/endpoints/` and register it in `setup_routes` with the correct prefix; the two product surfaces are mounted at `/api/v1/aro/*` and `/api/v1/mcc/*`.

Middleware order matters and is enforced in `setup_middlewares`: CORS first, then `SessionMiddleware` (needed for OAuth state), then `AuthMiddleware`, then `LoggerMiddleware`. Don't reorder casually.

The `lifespan` context initializes `fastapi-cache` with an in-memory backend and calls `setup_database(get_db_session())` to create the three Postgres schemas (`main`, `transactional`, `aro_user`). Table DDL is owned by **Alembic** — `setup_database` only creates schemas; the old `_create_tables` path is left as a deprecated comment.

### Configuration

`backend/config/config.py` builds a single `settings` object by composing `CORSConfig`, `LoggerConfig`, `DatabaseConfig`, `KeycloakConfig`, and `AROAuthConfig`. Each pulls from env vars via pydantic-settings. `python-dotenv`'s `load_dotenv()` runs at import time — when running from the repo root it finds `backend/.env` via the working dir; the docker compose backend service injects env from the repo-root `.env` plus an override (`GS_DATABASE_LOCATION=host.docker.internal`).

`template.env` documents every variable the backend needs. `KEYCLOAK_CLIENT_SECRET` and ARO Google OAuth secrets are not in the template and must be filled in locally; the Keycloak client secret lives inside `backend/keycloak/mcc-realm.json`.

### Data layer

- `backend/data/tables/` — SQLModel table classes split across three Postgres schemas: `main_tables.py` (reference data), `transactional_tables.py` (e.g. `CommsSession`), `aro_user_tables.py`, `mcc_user_tables.py`. Schema names are module-level constants (e.g. `MAIN_SCHEMA_NAME`) and are referenced by both `engine.py` and Alembic.
- `backend/data/data_wrappers/` — repository-style wrappers around SQLModel. New table accessors should extend `abstract_wrapper.py`; tests monkeypatch `data.data_wrappers.abstract_wrapper.get_db_session` (see `conftest.py`).
- `backend/migrations/` — Alembic migrations. `python_test/conftest.py` runs `alembic upgrade head` inside the per-test Postgres instance, so any new table needs both a SQLModel class and a migration or the tests will fail.

### Auth

Two distinct flows:
- **MCC**: Keycloak (OIDC). Realm definition is checked in at `backend/keycloak/mcc-realm.json` and auto-imported by the keycloak compose service.
- **ARO**: Google OAuth via Authlib, JWT-signed sessions. Config in `config/aro_auth_config.py`.

`api/middleware/auth_middleware.py` enforces both. Session cookies are protected by `SessionMiddleware` keyed on `settings.auth.jwt_secret_key`.

### Native interfaces and Python wrappers

`backend/interfaces/` is a submodule and the C sources are compiled into a shared library. The Python `obc_gs_interface/` package and `backend/obc_utils/command_packaging.py` call into that library via ctypes. If you change a struct in the C side, you need to rebuild (`cmake .. && make`) and update the Python wrapper to match — there is no codegen.

`backend/sun/ephemeris*.py` use Skyfield (SGP4) for orbit propagation; sample data ships in `backend/data/resources/`.

## Testing conventions

- pytest is verbose by default (`-v` in `pyproject.toml`).
- `python_test/conftest.py` autouses a fixture that swaps `get_db_session` to point at a per-test Postgres DB, so wrappers under test must call `get_db_session()` (not hold a cached engine).
- The dummy env vars in `conftest.py` are set with `setdefault` *before* importing the engine module, so test-only env never leaks into dev. Don't reorder those imports.
- mypy runs in `strict` mode and excludes `python_test/*`. Skyfield, ax25, tinyaes, authlib, and pyStuffing have `ignore_missing_imports`.
- Ruff is scoped to `backend/*.py` only (frontend, `python_test`, and `migrations` are excluded) and enforces docstrings on classes/functions/methods (rules `D101 D102 D103 D105` plus `D213`).

## Pre-commit

`.pre-commit-config.yaml` runs whitespace fixers + `ruff --fix` + `ruff-format`. The hooks deliberately skip `libs/`, `hal/`, and `backend/data/resources/callsigns.csv` from the large-file check. After cloning, run `uv run pre-commit install`.

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
- **Tests required for new code.** Any new or modified Python under `backend/` ships with a matching pytest in `backend/python_test/` — covering the golden path and at least the edge cases the change introduces. CI runs the full suite; untested behavior won't pass review. If a change is genuinely untestable (e.g. wiring a third-party SDK), say so explicitly in the PR.

## Maintaining this file

**Hard cap: `CLAUDE.md` must stay under 250 lines.** If an edit would push it past that, compact first — merge related bullets, drop anything rederivable from `pyproject.toml`, `package.json`, or a quick grep, and prefer one tight sentence over a paragraph. Re-check `wc -l CLAUDE.md` after any addition.

## Conventions called out by the team

- Branch naming: `<developer_name>/<feature_description>` (e.g. `danielg/implement-random-device-driver`).
- A PR template enforces required details; PRs expect ≥3 reviewers including a software lead.
