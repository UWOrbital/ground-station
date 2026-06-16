import pytest


@pytest.fixture(scope="session", autouse=True)
def migrate_db():
    """Override the parent database-migration fixture for standalone codec tests."""
    yield


@pytest.fixture(autouse=True)
def test_get_db_session():
    """Override the repo-wide autouse DB fixture; log codec tests don't need a database."""
    yield
