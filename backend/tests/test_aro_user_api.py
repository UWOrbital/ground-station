import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.v1.aro.auth.aro_session import create_access_token
from app.data.repositories.repositories import AROUsersRepository
from main import app


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers():
    """Bearer token headers for a superuser, required by every /user route."""
    superuser = await AROUsersRepository().create(
        {
            "email": "admin@test.com",
            "first_name": "Admin",
            "is_superuser": True,
        }
    )
    token, _ = create_access_token(superuser)
    return {"Authorization": f"Bearer {token}"}


# Test data for user 1
@pytest.fixture
def user1_data():
    return {
        "call_sign": "ABCDEF",
        "email": "bob@test.com",
        "first_name": "Bob",
        "last_name": "Smith",
        "phone_number": "4039790916",
    }


# Test data for user 2
@pytest.fixture
def user2_data():
    return {
        "call_sign": "KEVWAN",
        "email": "kevian@gmail.com",
        "first_name": "kevin",
        "last_name": "wan",
        "phone_number": "416-302-2725",
    }


# Test creating user1
@pytest_asyncio.fixture
async def test_user1_creation(client, user1_data, auth_headers):
    response = await client.post("/api/v1/aro/user/create_user", json=user1_data, headers=auth_headers)

    assert response.status_code == 200
    user = response.json()["data"]
    assert user["email"] == user1_data["email"]
    assert user["call_sign"] == user1_data["call_sign"]
    assert user["first_name"] == user1_data["first_name"].title()
    assert user["last_name"] == user1_data["last_name"].title()

    assert user["phone_number"] == "+1" + user1_data["phone_number"]

    return user


# Test creating user2
@pytest_asyncio.fixture
async def test_user2_creation(client, user2_data, auth_headers):
    response = await client.post("/api/v1/aro/user/create_user", json=user2_data, headers=auth_headers)

    assert response.status_code == 200
    user = response.json()["data"]
    assert user["email"] == user2_data["email"]
    assert user["call_sign"] == user2_data["call_sign"]
    assert user["first_name"] == user2_data["first_name"].title()
    assert user["last_name"] == user2_data["last_name"].title()
    assert user["phone_number"] == "+1" + user2_data["phone_number"].replace("-", "")

    return user


# Test getting user1 by ID
async def test_get_user1_by_id(client, test_user1_creation, auth_headers):
    user_id = test_user1_creation["id"]
    res = await client.get(f"/api/v1/aro/user/get_user/{user_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["id"] == user_id


# Test getting user2 by ID
async def test_get_user2_by_id(client, test_user2_creation, auth_headers):
    user_id = test_user2_creation["id"]
    res = await client.get(f"/api/v1/aro/user/get_user/{user_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"]["id"] == user_id


# Test getting all users
async def test_get_all_users(client, test_user1_creation, test_user2_creation, auth_headers):
    res = await client.get("/api/v1/aro/user/get_all_users", headers=auth_headers)
    assert res.status_code == 200
    all_users = res.json()["data"]
    assert len(all_users) == 3  # test_user1, test_user2, and the auth_headers superuser

    # Check user1
    user1_id = test_user1_creation["id"]
    user1_from_response = next(user for user in all_users if user["id"] == user1_id)
    assert user1_from_response["call_sign"] == test_user1_creation["call_sign"]
    assert user1_from_response["email"] == test_user1_creation["email"]
    assert user1_from_response["first_name"] == test_user1_creation["first_name"].title()
    assert user1_from_response["last_name"] == test_user1_creation["last_name"].title()
    assert user1_from_response["phone_number"] == test_user1_creation["phone_number"]

    # Check user2
    user2_id = test_user2_creation["id"]
    user2_from_response = next(user for user in all_users if user["id"] == user2_id)
    assert user2_from_response["email"] == test_user2_creation["email"]
    assert user2_from_response["call_sign"] == test_user2_creation["call_sign"]
    assert user2_from_response["first_name"] == test_user2_creation["first_name"].title()
    assert user2_from_response["last_name"] == test_user2_creation["last_name"].title()
    assert user2_from_response["phone_number"] == test_user2_creation["phone_number"]


# Test deleting user1
async def test_user1_deletion(client, test_user1_creation, test_user2_creation, auth_headers):
    user_id = test_user1_creation["id"]
    res = await client.delete(f"/api/v1/aro/user/delete_user/{user_id}", headers=auth_headers)

    assert res.status_code == 200
    deleted_user = res.json()["data"]
    assert deleted_user["id"] == user_id
    assert deleted_user["email"] == test_user1_creation["email"]
    assert deleted_user["call_sign"] == test_user1_creation["call_sign"]
    assert deleted_user["first_name"] == test_user1_creation["first_name"].title()
    assert deleted_user["last_name"] == test_user1_creation["last_name"].title()
    assert deleted_user["phone_number"] == test_user1_creation["phone_number"]


# Test that unauthenticated requests are rejected
async def test_get_all_users_requires_auth(client):
    res = await client.get("/api/v1/aro/user/get_all_users")
    assert res.status_code == 401


# Test that non-superusers are rejected
async def test_get_all_users_requires_superuser(client):
    regular_user = await AROUsersRepository().create({"email": "regular@test.com", "first_name": "Regular"})
    token, _ = create_access_token(regular_user)
    res = await client.get("/api/v1/aro/user/get_all_users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
