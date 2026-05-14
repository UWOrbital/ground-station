import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from exceptions.exception_handlers import STATUS_MAP, setup_exception_handlers
from exceptions.exceptions import BaseOrbitalError

def _create_exception_route_handler(exception_type: type[BaseOrbitalError]):
    """Creates a route handler that raises the given BaseOrbitalError subclass type"""
    async def _handler():
        raise exception_type(f"Test {exception_type.__name__}")
    return _handler

# build test client for all custom errors
@pytest.fixture
def exceptions_client():
    app = FastAPI()
    setup_exception_handlers(app)

    for exception_type in STATUS_MAP.keys():
        app.add_api_route(
            path=f"/{exception_type.__name__.lower()}",
            endpoint=_create_exception_route_handler(exception_type),
            methods=["GET"]
        )

    return TestClient(app)

# test custom errors via manual cases
@pytest.mark.parametrize(
    "endpoint, status_code, expected_message",
    [
        ("/serviceerror", status.HTTP_400_BAD_REQUEST, "Test ServiceError"),
        ("/notfounderror", status.HTTP_404_NOT_FOUND, "Test NotFoundError"),
        ("/invalidargumenterror", status.HTTP_422_UNPROCESSABLE_ENTITY, "Test InvalidArgumentError"),
        ("/invalidstateerror", status.HTTP_409_CONFLICT, "Test InvalidStateError"),
        ("/databaseerror", status.HTTP_400_BAD_REQUEST, "Test DatabaseError"),
        ("/unauthorizederror", status.HTTP_401_UNAUTHORIZED, "Test UnauthorizedError"),
        ("/sunpositionerror", status.HTTP_500_INTERNAL_SERVER_ERROR, "Test SunPositionError"),
        ("/unknownerror", status.HTTP_500_INTERNAL_SERVER_ERROR, "Test UnknownError"),
    ]
)
def test_custom_exceptions(exceptions_client, endpoint, status_code, expected_message):
    response = exceptions_client.get(endpoint)
    assert response.status_code == status_code
    assert response.json().get("message") == expected_message
