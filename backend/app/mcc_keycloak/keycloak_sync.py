import json
import subprocess
from pathlib import Path
from typing import Any

from config.config import settings
from dotenv import set_key
from keycloak import KeycloakError
from mcc_keycloak.client import keycloak

SENSITIVE_KEYS = {"secret", "registrationAccessToken"}
ROOT_DIR = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"],
    check=True,
    capture_output=True,
    text=True,
).stdout.strip()


def sync() -> None:
    """Sync Keycloak realm config to backend/app/mcc_keycloak/mcc-realm.json."""

    try:
        exported: dict[str, Any] = keycloak.admin_client.export_realm(export_clients=True, export_groups_and_role=True)

        client_list: list[dict[str, Any]] = exported.get("clients", [])
        client = next((c for c in client_list if c["clientId"] == settings.keycloak.client_id), None)
        if not client:
            raise RuntimeError(f"Could not find client with client_id {settings.keycloak.client_id} in realm export")

        client_secret = keycloak.admin_client.get_client_secrets(client["id"]).get("value")
    except KeycloakError as e:
        raise RuntimeError("Could not reach keycloak") from e

    if client_secret:
        set_key(
            Path(ROOT_DIR) / "template.env",
            "KEYCLOAK_CLIENT_SECRET",
            client_secret,
            quote_mode="never",
        )

    exported["clients"] = [{k: v for k, v in c.items() if k not in SENSITIVE_KEYS} for c in client_list]

    out_path = Path(ROOT_DIR) / "backend/app/mcc_keycloak/mcc-realm.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(exported, indent=2) + "\n")
