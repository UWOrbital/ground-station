"""
backend.api.v1.aro.endpoints.services 的 Docstring

Helper functions for our endpoints.

1. Authentication
"""
from sqlmodel import select
from backend.data.database.engine import get_db_session
from backend.data.tables.aro_user_tables import AROUsers
from pydantic import EmailStr

def get_user_by_email(email: EmailStr) -> AROUsers | None:
    # Find a user by their email address.
    with get_db_session() as session:
        found_user = session.exec(
            select(AROUsers).where(AROUsers.email == email)
        ).first()
    return found_user

def get_user_by_google_id(google_id: str) -> AROUsers | None:
    # Find a user from their Google ID.
    with get_db_session() as session:
        found_user = session.exec(
            select(AROUsers).where(AROUsers.google_id == google_id)
        ).first()
    return found_user
