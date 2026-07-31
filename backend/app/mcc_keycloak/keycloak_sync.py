import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx
from dotenv import set_key
from keycloak import KeycloakAdmin, KeycloakError

SENSITIVE_KEYS = {"secret", "registrationAccessToken"}
ROOT_DIR = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()

HOST = "http://localhost:8080"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"
REALM = "mcc"
CLIENT_ID = "ground-station"
HOST_REALM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcc-realm.json")


def start_keycloak() -> None:
    """Base `docker run` command for standalone Keycloak container."""
    cmd = [
        "docker",
        "run",
        "-d",
        "--name",
        "keycloak",
        "-p",
        "8080:8080",
        "-v",
        f"{HOST_REALM_PATH}:/opt/keycloak/data/import/mcc-realm.json",
        "-e",
        "KC_BOOTSTRAP_ADMIN_USERNAME=admin",
        "-e",
        "KC_BOOTSTRAP_ADMIN_PASSWORD=admin",
        "-e",
        "KC_HEALTH_ENABLED=true",
        "-e",
        "KC_HOSTNAME_STRICT=false",
        "quay.io/keycloak/keycloak:latest",
        "start-dev",
        "--import-realm",
    ]

    clean_up_container()
    subprocess.run(cmd, check=True)
    wait_for_keycloak(30)


def wait_for_keycloak(retries: int = 30) -> None:
    """Poll Keycloak until it is responsive."""
    for _ in range(retries):
        try:
            httpx.get(f"{HOST}/realms/mcc", timeout=2)
            print("keycloak responsive!")
            return
        except Exception:
            time.sleep(2)
    raise RuntimeError("Keycloak failed to start in time.")


def sync() -> None:
    """Sync Keycloak realm config to backend/app/mcc_keycloak/mcc-realm.json."""

    admin_client = KeycloakAdmin(
        server_url=HOST,
        username=ADMIN_USERNAME,
        password=ADMIN_PASSWORD,
        realm_name=REALM,
        user_realm_name="master",
    )

    try:
        exported: dict[str, Any] = admin_client.export_realm(export_clients=True, export_groups_and_role=True)

        client_list: list[dict[str, Any]] = exported.get("clients", [])
        client = next((c for c in client_list if c["clientId"] == CLIENT_ID), None)
        if client is None:
            raise RuntimeError(f"Could not find client with client_id {CLIENT_ID} in realm export")

        client_secret = admin_client.get_client_secrets(client["id"]).get("value")
    except KeycloakError as e:
        raise RuntimeError("Could not reach keycloak") from e

    if client_secret:
        set_key(
            Path(ROOT_DIR) / ".env",
            "KEYCLOAK_CLIENT_SECRET",
            client_secret,
            quote_mode="never",
        )

    exported["clients"] = [{k: v for k, v in c.items() if k not in SENSITIVE_KEYS} for c in client_list]

    out_path = Path(ROOT_DIR) / "backend/app/mcc_keycloak/mcc-realm.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(exported, indent=2) + "\n")

    print("mcc-realm sync success!")


def clean_up_container() -> None:
    """Removes the docker container that was previously started up."""
    cmd = ["docker", "rm", "-f", "keycloak"]

    subprocess.run(cmd, capture_output=True)
    print("container cleared success (if it existed)!")


if __name__ == "__main__":
    try:
        start_keycloak()
        sync()
    finally:
        clean_up_container()
