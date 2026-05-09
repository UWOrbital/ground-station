#!/bin/bash

# This is a bash script to sync the keycloak configuration to the settings json as a makeshift version control.
# To use, first run `chmod a+x kc-sync.sh` to grant permissions

# get token
TOKEN=$(curl -s -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -d "client_id=admin-cli" \
  -d "username=mcc-admin" \
  -d "password=uworbital" \
  -d "grant_type=password" | python3 -m json.tool | grep access_token | cut -d'"' -f4)

# get realm settings
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/admin/realms/mcc \
  -o /tmp/realm.json

# get clients
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/admin/realms/mcc/clients \
  -o /tmp/clients.json

# get roles
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/admin/realms/mcc/roles \
  -o /tmp/roles.json

# merge them into one file
python3 -c "
import json
realm = json.load(open('/tmp/realm.json'))
realm['clients'] = json.load(open('/tmp/clients.json'))
realm['roles'] = {'realm': json.load(open('/tmp/roles.json'))}
json.dump(realm, open('../../backend/keycloak/mcc-realm.json', 'w'), indent=2)
print('Keycloak is synced!')
"
