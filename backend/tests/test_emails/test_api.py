from unittest.mock import AsyncMock, patch

import pytest
from pydantic import NameEmail
from utils.email import Email, send, send_many


def get_name_email() -> NameEmail:
    return NameEmail(name="John Doe", email=f"john.doe@example.com")

@pytest.mark.asyncio
async def test_send_calls_send_many():
    email = Email(
        subject="Hello",
        recipients=[get_name_email()],
        text="world!",
    )

    with patch("utils.email.send_many", new_callable=AsyncMock) as mock_send_many:
        await send(email)

    mock_send_many.assert_awaited_once_with([email])

@pytest.mark.asyncio
async def test_send_many_sends_emails():
    email = Email(
        subject="fizz",
        recipients=[get_name_email()],
        text="buzz!",
    )

    with patch("utils.email.FastMail", autospec=True) as MockFastMail:
        MockFastMail.return_value.send_message = AsyncMock()

        await send_many([email])

    MockFastMail.assert_called_once()
    MockFastMail.return_value.send_message.assert_awaited_once()
