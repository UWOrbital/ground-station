"""
backend.api.v1.aro.endpoints.services 的 Docstring

Helper functions for our endpoints.

1. Authentication
"""
from data.database.engine import get_db_session
from data.tables.aro_user_tables import AROUsers
from pydantic import EmailStr
from sqlmodel import select


def get_user_by_email(email: EmailStr) -> AROUsers | None:
    """Find and return a user by their email address, or None if not found."""
    # Find a user by their email address.
    with get_db_session() as session:
        found_user = session.exec(select(AROUsers).where(AROUsers.email == email)).first()
    return found_user


def get_user_by_google_id(google_id: str) -> AROUsers | None:
    """Find and return a user by their Google ID, or None if not found."""
    # Find a user from their Google ID.
    with get_db_session() as session:
        found_user = session.exec(select(AROUsers).where(AROUsers.google_id == google_id)).first()
    return found_user
