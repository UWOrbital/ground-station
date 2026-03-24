from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def aro_user_data():
    return {
        "call_sign": "ABCDEF",
        "email": "test@test.com",
        "first_name": "first",
        "last_name": "last",
        "phone_number": "1234567890",
    }

@pytest.fixture
def created_aro_user(client, aro_user_data):
    response = client.post(
        "/api/v1/aro/user/create_user", json=aro_user_data, headers={"Content-Type": "application/json"}
    )

    user = response.json()["data"]
    return user

@pytest.fixture
def picture_request_payload(created_aro_user):
    return {
        "aro_id": created_aro_user["id"],
        "latitude": "49.282",
        "longitude": "-123.120",
    }

@pytest.fixture
def created_picture_request(client, picture_request_payload):
    response = client.post(
        "/api/v1/aro/requests/", json=picture_request_payload, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200
    request_data = response.json()["data"]
    assert request_data["aro_id"] == picture_request_payload["aro_id"]
    assert request_data["latitude"] == picture_request_payload["latitude"]
    assert request_data["longitude"] == picture_request_payload["longitude"]

    return response.json()

@pytest.fixture
def multi_created_picture_requests(client, picture_request_payload):

    responses = []

    for i in range(5):
        response = client.post(
            "/api/v1/aro/requests/", json=picture_request_payload, headers={"Content-Type": "application/json"}
        )

        responses.append(response.json())

    return responses

def test_create_picture_request(client, picture_request_payload):
    response = client.post(
        "/api/v1/aro/requests/", json=picture_request_payload, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200

    payload = response.json()
    data = payload["data"]
    operations = payload["operations"]

    assert data["aro_id"] == picture_request_payload["aro_id"]
    assert data["latitude"] == picture_request_payload["latitude"]
    assert data["longitude"] == picture_request_payload["longitude"]

    request_id = data["id"]

    assert operations["delete"] == f"/api/v1/aro/requests/{request_id}/delete"
    assert operations["download"] == f"/api/v1/aro/requests/{request_id}/packet"


def test_get_all_picture_requests(client, multi_created_picture_requests):
    response = client.get("/api/v1/aro/requests/")

    assert response.status_code == 200
    payload = response.json()
    requests = payload["data"]
    operations = payload["operations"]

    assert len(requests) == 5
    assert len(operations) == 5

    for i in range(5):

        assert requests[i]["aro_id"] == multi_created_picture_requests[i]["data"]["aro_id"]
        assert requests[i]["latitude"] == multi_created_picture_requests[i]["data"]["latitude"]
        assert requests[i]["longitude"] == multi_created_picture_requests[i]["data"]["longitude"]

    for i in range(5):

        assert operations[i]["delete"] == f"/api/v1/aro/requests/{requests[i]["id"]}/delete"
        assert operations[i]["download"] == f"/api/v1/aro/requests/{requests[i]["id"]}/packet"


def test_count_and_offset(client, multi_created_picture_requests):

    response = client.get("/api/v1/aro/requests/?count=2&offset=2")

    assert response.status_code == 200
    data = response.json()["data"]

    assert len(data) == 2

    assert data[0]["id"] == multi_created_picture_requests[2]["data"]["id"]
    assert data[1]["id"] == multi_created_picture_requests[3]["data"]["id"]

def test_get_picture_requests_offset_out_of_bounds(client):

    response = client.get("/api/v1/aro/requests/?count=5&offset=10")

    assert response.status_code == 200
    payload = response.json()

    assert payload["data"] == []
    assert payload["operations"] == []

def test_create_invalid_picture_request(client, created_aro_user):
    invalid_payload = {
        "aro_id": created_aro_user["id"],
        "latitude": "not-a-number",
        "longitude": "-123.1207",
    }

    response = client.post("/api/v1/aro/requests/", json=invalid_payload)
    assert response.status_code == 422

'''
def test_get_packet(client, created_picture_request):
    request_id = created_picture_request["data"]["id"]

    response = client.get(f"/api/v1/aro/requests/{request_id}/packet")

    assert response.status_code == 200
'''

def test_delete_picture_request(client, created_picture_request, picture_request_payload):
    request_id = created_picture_request["data"]["id"]

    response = client.delete(f"/api/v1/aro/requests/{request_id}")

    assert response.status_code == 200

    payload = response.json()
    data = payload["data"]
    operations = payload["operations"]

    assert data["aro_id"] == picture_request_payload["aro_id"]
    assert data["latitude"] == picture_request_payload["latitude"]
    assert data["longitude"] == picture_request_payload["longitude"]

    request_id = data["id"]

    assert operations["download"] == f"/api/v1/aro/requests/{request_id}/packet"
