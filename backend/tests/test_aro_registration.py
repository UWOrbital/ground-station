import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.aro.routes.auth import router
from app.data.repositories.dal import DAL


def _app() -> FastAPI:
  """Mount just the ARO auth router for registration tasks.

  :return: a FastAPI app exposing /api/aro/auth/*.
  """
  app = FastAPI()
  app.include_router(router, prefix="/api/aro")
  return app


async def test_register_persists_callsign_and_phone(db_session) -> None:
  """A valid registration stores call sign and phone on the AROUsers row.

  :param db_session: the testcontainers-backed session fixture.
  """
  payload = {
    "first_name": "Alice",
    "email": "alice@example.com",
    "password": "blah2bla",
    "call_sign": "VA3ABC",
    "phone_number": "+15195550123",
  }
  async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://test") as client:
    res = await client.post("/api/aro/auth/register", json=payload)

  assert res.status_code == 201
  user = await DAL.aro_users().get_first_by(email="alice@example.com")
  assert user is not None
  assert user.call_sign == "VA3ABC"
  assert user.phone_number == "+15195550123"


async def test_register_rejects_missing_callsign() -> None:
  """Registration without a call sign is a 422."""
  payload = {
    "first_name": "Alice",
    "email": "alice2@example.com",
    "password": "blah2bla",
  }
  async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://test") as client:
    res = await client.post("/api/aro/auth/register", json=payload)
  assert res.status_code == 422


async def test_register_allows_missing_phone(db_session) -> None:
  """Phone number is optional; registration succeeds without it.

  :param db_session: the testcontainers-backed session fixture.
  """
  payload = {
    "first_name": "Bob",
    "email": "bob@example.com",
    "password": "verysecurepwd",
    "call_sign": "VA3XYZ",
  }
  async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://test") as client:
    res = await client.post("/api/aro/auth/register", json=payload)
  assert res.status_code == 201
