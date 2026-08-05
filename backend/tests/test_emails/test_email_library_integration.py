from io import BytesIO

import pytest
from fastapi import UploadFile
from fastapi_mail import MessageSchema, MessageType, MultipartSubtypeEnum
from pydantic import NameEmail
from app.utils.email import Email, EmailType, _create_message_schema_fields, _default_sender


def get_name_email(name: str = "John Doe") -> NameEmail:
    username = name.lower().replace(' ', '.')
    return NameEmail(name=name, email=f"{username}@example.com")

def test_plaintext_email_to_message_schema():
    email = Email(
        subject="John subject",
        recipients=[get_name_email()],
        type=EmailType.TEST,
        text="John body",
    )

    default_sender = _default_sender()
    message_fields = _create_message_schema_fields(email)

    assert message_fields == {
        "subject": "John subject",
        "recipients": [get_name_email()],
        "from_email": default_sender.email,
        "from_name": default_sender.name,
        "cc": [],
        "bcc": [],
        "reply_to": [],
        "attachments": [],
        "headers": None,
        "body": "John body",
        "subtype": MessageType.plain,
    }
    MessageSchema(**message_fields)

def test_html_email_to_message_schema():
    email = Email(
        subject="John subject",
        recipients=[get_name_email()],
        type=EmailType.TEST,
        html="<p>John body</p>",
    )

    default_sender = _default_sender()
    message_fields = _create_message_schema_fields(email)

    assert message_fields == {
        "subject": "John subject",
        "recipients": [get_name_email()],
        "from_email": default_sender.email,
        "from_name": default_sender.name,
        "cc": [],
        "bcc": [],
        "reply_to": [],
        "attachments": [],
        "headers": None,
        "body": "<p>John body</p>",
        "subtype": MessageType.html,
    }
    MessageSchema(**message_fields)

def test_multipart_email_to_message_schema():
    email = Email(
        subject="John subject",
        recipients=[get_name_email()],
        type=EmailType.TEST,
        text="John plaintext",
        html="<p>John html</p>",
    )

    default_sender = _default_sender()
    message_fields = _create_message_schema_fields(email)

    assert message_fields == {
        "subject": "John subject",
        "recipients": [get_name_email()],
        "from_email": default_sender.email,
        "from_name": default_sender.name,
        "cc": [],
        "bcc": [],
        "reply_to": [],
        "attachments": [],
        "headers": None,
        "template_body": "<p>John html</p>",
        "subtype": MessageType.html,
        "alternative_body": "John plaintext",
        "multipart_subtype": MultipartSubtypeEnum.alternative,
    }
    MessageSchema(**message_fields)

def test_optional_fields_are_preserved():
    email = Email(
        subject="John subject",
        recipients=[get_name_email()],
        type=EmailType.TEST,
        text="John text",
        cc=[get_name_email("John cc")],
        bcc=[get_name_email("John bcc")],
        reply_to=[get_name_email("John reply")],
        headers={"X-Test": "John header"},
    )

    message_fields = _create_message_schema_fields(email)

    assert message_fields["cc"] == [get_name_email("John cc")]
    assert message_fields["bcc"] == [get_name_email("John bcc")]
    assert message_fields["reply_to"] == [get_name_email("John reply")]
    assert message_fields["headers"] == {"X-Test": "John header"}
    MessageSchema(**message_fields)

def test_attachments_are_preserved():
    file = UploadFile(BytesIO(b"John file"))

    email = Email(
        subject="John subject",
        recipients=[get_name_email()],
        type=EmailType.TEST,
        text="John text",
        attachments=[file],
    )

    message_fields = _create_message_schema_fields(email)

    assert message_fields["attachments"] == [file]
    MessageSchema(**message_fields)
