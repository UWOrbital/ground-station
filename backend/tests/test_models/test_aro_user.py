import pytest
from app.data.models.aro_user_models import AROUsers
from pydantic import ValidationError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


# TODO: Add call sign validation tests
async def test_users_data_basic(db_session: AsyncSession):
    user_data = AROUsers(call_sign="123456", email="bob@test.com", first_name="Bob", phone_number="123456789")
    db_session.add(user_data)
    await db_session.commit()

    user_data_query = select(AROUsers)
    user_data_items = (await db_session.exec(user_data_query)).all()

    assert len(user_data_items) == 1
    data_returned1 = user_data_items[0]
    assert data_returned1.call_sign == "123456"
    assert data_returned1.email == "bob@test.com"
    assert data_returned1.first_name == "Bob"
    assert data_returned1.last_name is None
    assert data_returned1.phone_number == "123456789"


def test_users_data_invalid_email():
    with pytest.raises(ValidationError):
        AROUsers(
            call_sign="123456",
            email="www.test.com",  # invalid email format
            first_name="Bob",
            phone_number="123456789",
        )
