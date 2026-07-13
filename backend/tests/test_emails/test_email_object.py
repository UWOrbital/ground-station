import pytest
from pydantic import NameEmail

from utils.email import Email, _default_sender
from config.config import settings

def get_name_email() -> NameEmail:
    return NameEmail(name="John Doe", email=f"john.doe@example.com")


def test_email_requires_subject():
    with pytest.raises(ValueError, match="Subject cannot be empty"):
        Email(
            subject="",
            recipients=[get_name_email()],
            text="skibidi toilet",
        )

def test_email_requires_recipients():
    with pytest.raises(ValueError, match="At least one recipient is required"):
        Email(
            subject="six",
            recipients=[],
            text="seven",
        )

def test_email_requires_body():
    with pytest.raises(ValueError, match="Email must have either a plaintext or HTML body, or both"):
        Email(
            subject="test",
            recipients=[get_name_email()],
        )

def test_email_accepts_plaintext():
    email = Email(
        subject="hey wanna play some video games",
        recipients=[get_name_email()],
        text="i know i do",
    )

    assert email.text == "i know i do"
    assert email.html is None

def test_email_accepts_html():
    email = Email(
        subject="hey wanna play some video games",
        recipients=[get_name_email()],
        html="<p>i know i do</p>",
    )

    assert email.text is None
    assert email.html == "<p>i know i do</p>"

def test_email_accepts_both_plaintext_and_html():
    email = Email(
        subject="hey wanna play some video games",
        recipients=[get_name_email()],
        text="i know i do",
        html="<p>i havent seen the sun in years</p>",
    )

    assert email.text == "i know i do"
    assert email.html == "<p>i havent seen the sun in years</p>"

def test_get_default_sender():
    sender = _default_sender()

    assert sender.name == settings.email.mail_from_name
    assert sender.email == settings.email.mail_from

def test_sender_defaults_to_settings():
    email = Email(
        subject="subject",
        recipients=[get_name_email()],
        text="text",
    )

    default_sender = _default_sender()

    assert email.sender.name == default_sender.name
    assert email.sender.email == default_sender.email


def test_custom_sender():
    sender = NameEmail("John Tester", "john.tester@example.com")

    email = Email(
        subject="subject",
        recipients=[get_name_email()],
        text="text",
        sender=sender,
    )

    assert email.sender.name == sender.name
    assert email.sender.email == sender.email
