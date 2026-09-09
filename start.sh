#!/usr/bin/env bash
#
# Starts the decoupled Keycloak stack, waits for it to become available, then
# brings up the main ground-station stack. This mirrors an external Keycloak
# deployment where the auth service is provisioned independently of the app.
#
# Usage: ./start.sh
set -euo pipefail

KEYCLOAK_COMPOSE="docker-compose.keycloak.yml"
# Realm discovery endpoint; a 200 here means the realm has finished importing,
# not just that the port is open.
KEYCLOAK_READY_URL="http://localhost:8080/realms/mcc/.well-known/openid-configuration"

echo "Starting Keycloak (${KEYCLOAK_COMPOSE})..."
docker compose -f "${KEYCLOAK_COMPOSE}" up -d --build

echo "Waiting for Keycloak to become available at ${KEYCLOAK_READY_URL}..."
until curl -sf "${KEYCLOAK_READY_URL}" >/dev/null; do
  echo "  ...still waiting for Keycloak"
  sleep 3
done
echo "Keycloak is ready."

echo "Starting the main ground-station stack..."
docker compose up --build
