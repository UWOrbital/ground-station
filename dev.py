#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import random
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from email.message import Message
from http.cookiejar import CookieJar, DefaultCookiePolicy
from pathlib import Path
from urllib.request import HTTPCookieProcessor, OpenerDirector, Request, build_opener

REPO_ROOT = Path(__file__).resolve().parent
REALM_JSON = REPO_ROOT / "backend" / "app" / "mcc_keycloak" / "mcc-realm.json"
ENV_FILE = REPO_ROOT / ".env"
BACKEND_LOG = REPO_ROOT / "gs-backend.log"

KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
REALM = "mcc"
MASTER_ADMIN_USER = "mcc-admin"
MASTER_ADMIN_PASS = "uworbital"

KC_CONTAINER = "gs-keycloak"
KC_VOLUME = "gs-keycloak-data"
PG_CONTAINER = "gs-postgres"
PG_VOLUME = "gs-postgres-data"
PG_PORT = "5433"
DB_USER = "gs_user"
DB_PASSWORD = "gs_password"
DB_NAME = "gs"


class InsecureCookiePolicy(DefaultCookiePolicy):
    # Keycloak marks its session cookies Secure even over plain http in dev mode; without this override
    # http.cookiejar silently drops them on every request and the login POST 400s with no useful error.
    def return_ok_secure(self, cookie: object, request: object) -> bool:
        return True


class Reporter:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, msg: str) -> None:
        self.passed += 1
        print(f"  PASS: {msg}")

    def bad(self, msg: str) -> None:
        self.failed += 1
        print(f"  FAIL: {msg}")

    def expect_status(self, desc: str, expected: int, actual: int) -> None:
        if actual == expected:
            self.ok(f"{desc} ({actual})")
        else:
            self.bad(f"{desc} (expected {expected}, got {actual})")


def sh(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def command_ok(cmd: list[str]) -> bool:
    try:
        return subprocess.run(cmd, capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def check_prereqs() -> None:
    problems = []
    if not command_ok(["docker", "--version"]):
        problems.append("docker is missing — install it with: sudo apt install docker.io")
    if not (command_ok(["docker", "compose", "version"]) or command_ok(["docker-compose", "--version"])):
        problems.append("docker compose is missing — install it with: sudo apt install docker-compose")
    if problems:
        for p in problems:
            print(p)
        sys.exit(1)


def wait_for(url: str, timeout: int = 120) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=3)
            return True
        except Exception:
            time.sleep(2)
    return False


def start_keycloak() -> None:
    sh(["docker", "rm", "-f", KC_CONTAINER])
    sh(["docker", "volume", "rm", KC_VOLUME])
    # Mirrors docker-compose.keycloak.yml: boot Keycloak, then use kcadm to relax
    # the master realm's sslRequired so http-only local testing doesn't get rejected.
    boot_script = (
        "/opt/keycloak/bin/kc.sh start-dev --import-realm & "
        "until echo > /dev/tcp/localhost/8080; do sleep 2; done; sleep 5; "
        f"/opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 "
        f"--realm master --user {MASTER_ADMIN_USER} --password {MASTER_ADMIN_PASS}; "
        "/opt/keycloak/bin/kcadm.sh update realms/master -s sslRequired=NONE; wait"
    )
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            KC_CONTAINER,
            "-e",
            f"KC_BOOTSTRAP_ADMIN_USERNAME={MASTER_ADMIN_USER}",
            "-e",
            f"KC_BOOTSTRAP_ADMIN_PASSWORD={MASTER_ADMIN_PASS}",
            "-e",
            "KC_HEALTH_ENABLED=true",
            "-p",
            "8080:8080",
            "-v",
            f"{KC_VOLUME}:/opt/keycloak/data",
            "-v",
            f"{REALM_JSON}:/opt/keycloak/data/import/mcc-realm.json",
            "--entrypoint",
            "/bin/bash",
            "quay.io/keycloak/keycloak:latest",
            "-c",
            boot_script,
        ],
        check=True,
    )
    print("waiting for Keycloak to import the mcc realm...")
    if not wait_for(f"{KEYCLOAK_URL}/realms/{REALM}/.well-known/openid-configuration"):
        sys.exit("Keycloak did not become ready in time")
    print("Keycloak ready")


def start_postgres() -> None:
    sh(["docker", "rm", "-f", PG_CONTAINER])
    sh(["docker", "volume", "rm", PG_VOLUME])
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            PG_CONTAINER,
            "-e",
            f"POSTGRES_USER={DB_USER}",
            "-e",
            f"POSTGRES_PASSWORD={DB_PASSWORD}",
            "-e",
            f"POSTGRES_DB={DB_NAME}",
            "-p",
            f"{PG_PORT}:5432",
            "-v",
            f"{PG_VOLUME}:/var/lib/postgresql/data",
            "postgres:16-alpine",
        ],
        check=True,
    )
    print("waiting for Postgres...")
    deadline = time.time() + 60
    while time.time() < deadline:
        if sh(["docker", "exec", PG_CONTAINER, "pg_isready", "-U", DB_USER]).returncode == 0:
            print("Postgres ready")
            return
        time.sleep(2)
    sys.exit("Postgres did not become ready in time")


def kc_admin_request(
    method: str, path: str, token: str, body: dict[str, object] | None = None
) -> tuple[int, object, Message]:
    data = json.dumps(body).encode() if body is not None else None
    req = Request(
        f"{KEYCLOAK_URL}{path}",
        data=data,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None), resp.headers
    except urllib.error.HTTPError as e:
        raw = e.read()
        return e.code, (json.loads(raw) if raw else None), e.headers


def create_kc_user(token: str, username: str, password: str) -> str:
    status, _, headers = kc_admin_request(
        "POST",
        f"/admin/realms/{REALM}/users",
        token,
        {
            "username": username,
            "email": f"{username}@example.com",  # .test is an RFC 2606 reserved TLD pydantic's EmailStr rejects
            "firstName": "Test",
            "lastName": "User",
            "enabled": True,
            "emailVerified": True,
            "requiredActions": [],  # omitting this triggers Keycloak's VERIFY_PROFILE required-action on first login
        },
    )
    if status != 201:
        raise RuntimeError(f"failed to create Keycloak user {username}: HTTP {status}")
    user_id = (headers.get("Location") or "").rstrip("/").split("/")[-1]
    kc_admin_request(
        "PUT",
        f"/admin/realms/{REALM}/users/{user_id}/reset-password",
        token,
        {"type": "password", "value": password, "temporary": False},
    )
    return user_id


def in_group(token: str, user_id: str, group_name: str = "mcc-admins") -> bool:
    _, groups, _ = kc_admin_request("GET", f"/admin/realms/{REALM}/users/{user_id}/groups", token)
    if not isinstance(groups, list):
        return False
    return any(isinstance(g, dict) and g.get("name") == group_name for g in groups)


def get_client_secret(token: str) -> str:
    _, clients, _ = kc_admin_request("GET", f"/admin/realms/{REALM}/clients?clientId=ground-station", token)
    if not isinstance(clients, list) or not clients or not isinstance(clients[0], dict):
        raise RuntimeError("ground-station client not found in the mcc realm")
    client_id = clients[0]["id"]
    _, secret, _ = kc_admin_request("GET", f"/admin/realms/{REALM}/clients/{client_id}/client-secret", token)
    if not isinstance(secret, dict) or not isinstance(secret.get("value"), str):
        raise RuntimeError("could not fetch the ground-station client secret")
    value: str = secret["value"]
    return value


def write_env(secret: str) -> None:
    defaults = {
        "GS_DATABASE_USER": DB_USER,
        "GS_DATABASE_PASSWORD": DB_PASSWORD,
        "GS_DATABASE_LOCATION": "localhost",
        "GS_DATABASE_PORT": PG_PORT,
        "GS_DATABASE_NAME": DB_NAME,
        "KEYCLOAK_URL": KEYCLOAK_URL,
        "KEYCLOAK_REALM": REALM,
        "KEYCLOAK_CLIENT_ID": "ground-station",
        "KEYCLOAK_CLIENT_SECRET": secret,
        "KEYCLOAK_CALLBACK_URL": f"{BACKEND_URL}/api/v1/mcc/auth/callback",
        "KEYCLOAK_REDIRECT_URI": f"{BACKEND_URL}/docs",
        "KEYCLOAK_SECURE_COOKIES": "false",
        "KEYCLOAK_ADMIN_GROUP_PATH": "/mcc-admins",
        "ARO_AUTH_JWT_SECRET": "devsecretdevsecretdevsecretdev1",
        "ARO_AUTH_SESSION_SECRET": "devsecretdevsecretdevsecretdev2",
        "ARO_AUTH_IS_PRODUCTION": "False",
        "EMAIL_MAIL_USERNAME": "dev",
        "EMAIL_MAIL_PASSWORD": "dev",
        "EMAIL_MAIL_SERVER": "localhost",
        "EMAIL_MAIL_PORT": "465",
        "EMAIL_MAIL_FROM": "dev@example.com",
        "EMAIL_MAIL_FROM_NAME": "Dev",
    }
    existing: dict[str, str] = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, _, value = line.partition("=")
                existing[key.strip()] = value.strip()
    merged = {**defaults, **existing}  # existing .env values win, except the secret is always refreshed below
    merged["KEYCLOAK_CLIENT_SECRET"] = secret
    ENV_FILE.write_text("\n".join(f"{k}={v}" for k, v in merged.items()) + "\n")
    print(f"wrote {ENV_FILE}")


def start_backend() -> subprocess.Popen[bytes]:
    log_file = BACKEND_LOG.open("ab")
    log_file.write(f"\n===== dev.py run started {datetime.now(UTC).isoformat()} =====\n\n".encode())
    log_file.flush()
    proc = subprocess.Popen(
        ["uv", "run", "fastapi", "dev", "backend/main.py", "--port", "8000"],
        cwd=REPO_ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    print(f"backend starting (pid {proc.pid}, logs: {BACKEND_LOG})")
    if not wait_for(f"{BACKEND_URL}/docs", timeout=60):
        sys.exit(f"backend did not become ready in time; see {BACKEND_LOG}")
    print("backend ready")
    return proc


def login_user(username: str, password: str) -> OpenerDirector:
    cj = CookieJar(policy=InsecureCookiePolicy())
    opener = build_opener(HTTPCookieProcessor(cj))
    login_page = opener.open(f"{BACKEND_URL}/api/v1/mcc/auth/login").read().decode()
    match = re.search(r'action="([^"]+)"', login_page)
    if not match:
        raise RuntimeError("could not find Keycloak login form action URL")
    action_url = match.group(1).replace("&amp;", "&")
    data = urllib.parse.urlencode({"username": username, "password": password, "credentialId": ""}).encode()
    # urllib does not set this automatically for a bytes body; without it Keycloak 400s the login POST
    req = Request(action_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        opener.open(req)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"login failed for {username}: HTTP {e.code}") from e
    if not any(c.name == "access_token" for c in cj):
        raise RuntimeError(f"login succeeded for {username} but no access_token cookie was set")
    opener.cookiejar = cj  # type: ignore[attr-defined]
    return opener


def token_has_admin_role(opener: OpenerDirector) -> bool:
    cj: CookieJar = opener.cookiejar  # type: ignore[attr-defined]
    token = next((c.value for c in cj if c.name == "access_token"), None)
    if not token:
        return False
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    claims = json.loads(base64.urlsafe_b64decode(payload))
    return "mcc-admin" in claims.get("realm_access", {}).get("roles", [])


def backend_request(
    opener: OpenerDirector, method: str, path: str, body: dict[str, object] | None = None
) -> tuple[int, object]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = Request(f"{BACKEND_URL}{path}", data=data, method=method, headers=headers)
    try:
        with opener.open(req) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, None


def run_live_tests(reporter: Reporter, kc_token: str, group_id: str) -> None:
    suffix = random.randint(10000, 99999)
    admin_user, alice_user, bob_user = f"gs_admin_{suffix}", f"gs_alice_{suffix}", f"gs_bob_{suffix}"

    admin_id = create_kc_user(kc_token, admin_user, "Passw0rd!")
    alice_id = create_kc_user(kc_token, alice_user, "Passw0rd!")
    bob_id = create_kc_user(kc_token, bob_user, "Passw0rd!")
    reporter.ok("created three Keycloak test users")

    kc_admin_request("PUT", f"/admin/realms/{REALM}/users/{admin_id}/groups/{group_id}", kc_token)
    if in_group(kc_token, admin_id):
        reporter.ok("bootstrapped test admin into mcc-admins directly")
    else:
        reporter.bad("bootstrapped test admin into mcc-admins directly")
        return

    try:
        admin_opener = login_user(admin_user, "Passw0rd!")
        reporter.ok("admin logged in")
        alice_opener = login_user(alice_user, "Passw0rd!")
        reporter.ok("alice logged in")
        bob_opener = login_user(bob_user, "Passw0rd!")
        reporter.ok("bob logged in")
    except RuntimeError as e:
        reporter.bad(str(e))
        return

    status, body = backend_request(alice_opener, "POST", "/api/v1/mcc/admin/request")
    reporter.expect_status("Alice requests admin access", 200, status)
    if isinstance(body, dict) and body.get("admin_request_status") == "pending":
        reporter.ok("Alice's status is pending")
    else:
        reporter.bad("Alice's status is pending")

    status, body = backend_request(admin_opener, "GET", "/api/v1/mcc/admin/requests")
    reporter.expect_status("admin lists pending requests", 200, status)
    if isinstance(body, dict) and any(u["id"] == alice_id for u in body.get("data", [])):
        reporter.ok("Alice appears in the pending list")
    else:
        reporter.bad("Alice appears in the pending list")

    status, body = backend_request(
        admin_opener, "PATCH", f"/api/v1/mcc/admin/requests/{alice_id}", {"status": "approved"}
    )
    reporter.expect_status("admin approves Alice", 200, status)
    if isinstance(body, dict) and body.get("admin_request_status") == "approved":
        reporter.ok("Alice's status is approved")
    else:
        reporter.bad("Alice's status is approved")

    if in_group(kc_token, alice_id):
        reporter.ok("Alice was actually added to mcc-admins in Keycloak")
    else:
        reporter.bad("Alice was actually added to mcc-admins in Keycloak")

    alice_opener = login_user(alice_user, "Passw0rd!")  # re-login: the first token predates the group grant
    if token_has_admin_role(alice_opener):
        reporter.ok("Alice's fresh token carries the mcc-admin role")
    else:
        reporter.bad("Alice's fresh token carries the mcc-admin role")

    status, _ = backend_request(alice_opener, "GET", "/api/v1/mcc/admin/requests")
    reporter.expect_status("Alice, now an admin, can list requests", 200, status)

    status, _ = backend_request(alice_opener, "POST", "/api/v1/mcc/admin/request")
    reporter.expect_status("Alice re-requesting while already approved is rejected", 409, status)

    backend_request(bob_opener, "POST", "/api/v1/mcc/admin/request")
    status, body = backend_request(
        admin_opener, "PATCH", f"/api/v1/mcc/admin/requests/{bob_id}", {"status": "rejected"}
    )
    reporter.expect_status("admin rejects Bob", 200, status)
    if isinstance(body, dict) and body.get("admin_request_status") == "rejected":
        reporter.ok("Bob's status is rejected")
    else:
        reporter.bad("Bob's status is rejected")

    if in_group(kc_token, bob_id):
        reporter.bad("Bob was NOT added to mcc-admins")
    else:
        reporter.ok("Bob was NOT added to mcc-admins")

    status, _ = backend_request(admin_opener, "PATCH", f"/api/v1/mcc/admin/requests/{bob_id}", {"status": "approved"})
    reporter.expect_status("re-deciding Bob's already-closed request is rejected", 409, status)

    status, _ = backend_request(bob_opener, "GET", "/api/v1/mcc/admin/requests")
    reporter.expect_status("Bob (non-admin) is forbidden from listing requests", 403, status)

    status, _ = backend_request(
        admin_opener, "PATCH", "/api/v1/mcc/admin/requests/00000000-0000-0000-0000-000000000000", {"status": "approved"}
    )
    reporter.expect_status("approving a nonexistent user returns 404", 404, status)

    status, _ = backend_request(admin_opener, "PATCH", f"/api/v1/mcc/admin/requests/{alice_id}", {"status": "pending"})
    reporter.expect_status("an invalid status value is rejected", 422, status)


def main() -> None:
    check_prereqs()
    start_keycloak()
    start_postgres()

    kc_token_response = urllib.request.urlopen(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data=urllib.parse.urlencode(
            {
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": MASTER_ADMIN_USER,
                "password": MASTER_ADMIN_PASS,
            }
        ).encode(),
    )
    kc_token = json.load(kc_token_response)["access_token"]

    status, _, _ = kc_admin_request("GET", f"/admin/realms/{REALM}/roles/mcc-admin", kc_token)
    if status != 200:
        sys.exit("mcc-admin realm role is missing from the mcc realm — see howto.md")
    status, group, _ = kc_admin_request("GET", f"/admin/realms/{REALM}/group-by-path/mcc-admins", kc_token)
    if status != 200 or not isinstance(group, dict):
        sys.exit("mcc-admins group is missing from the mcc realm — see howto.md")
    group_id = group["id"]

    write_env(get_client_secret(kc_token))

    print("running migrations...")
    if subprocess.run(["uv", "run", "alembic", "upgrade", "head"], cwd=REPO_ROOT).returncode != 0:
        sys.exit("alembic upgrade failed")

    backend_proc = start_backend()

    reporter = Reporter()
    print("\n== Automated test suite ==")
    test_env = os.environ.copy()
    # conftest.py needs these just to import (pydantic validates at module load); real values don't matter here
    test_env.setdefault("GS_DATABASE_LOCATION", "localhost")
    test_env.setdefault("GS_DATABASE_PORT", "5432")
    test_env.setdefault("EMAIL_MAIL_USERNAME", "test")
    test_env.setdefault("EMAIL_MAIL_PASSWORD", "test")
    test_env.setdefault("EMAIL_MAIL_SERVER", "localhost")
    test_env.setdefault("EMAIL_MAIL_FROM", "test@example.com")
    test_env.setdefault("EMAIL_MAIL_FROM_NAME", "Test")
    test_env.setdefault("EMAIL_MAIL_PORT", "465")
    pytest_result = subprocess.run(
        [
            "uv",
            "run",
            "pytest",
            "backend/tests/test_mcc_admin_endpoints.py",
            "backend/tests/test_mcc_authentication.py",
            "-q",
        ],
        cwd=REPO_ROOT,
        env=test_env,
    )
    reporter.ok("pytest suite") if pytest_result.returncode == 0 else reporter.bad("pytest suite")

    print("\n== Golden path & edge cases ==")
    run_live_tests(reporter, kc_token, group_id)

    print(f"\n== {reporter.passed} passed, {reporter.failed} failed ==")

    print("\ntearing down...")
    backend_proc.terminate()
    try:
        backend_proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        backend_proc.kill()
    sh(["docker", "rm", "-f", KC_CONTAINER, PG_CONTAINER])
    sh(["docker", "volume", "rm", KC_VOLUME, PG_VOLUME])
    ENV_FILE.unlink(missing_ok=True)  # tied to this session's now-dead Keycloak client secret

    sys.exit(0 if reporter.failed == 0 else 1)


if __name__ == "__main__":
    main()
