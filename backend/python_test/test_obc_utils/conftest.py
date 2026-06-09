import pytest


@pytest.fixture(autouse=True)
def test_get_db_session():
    """Override the repo-wide autouse DB fixture; log codec tests don't need a database."""
    yield
