from dataclasses import dataclass, field
from typing import Any

from config.config import settings
from fastapi import UploadFile
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType, MultipartSubtypeEnum
from pydantic import NameEmail

_conf = ConnectionConfig(
    MAIL_USERNAME=settings.email.mail_username,
    MAIL_PASSWORD=settings.email.mail_password,
    MAIL_SERVER=settings.email.mail_server,
    MAIL_PORT=settings.email.mail_port,
    MAIL_FROM=settings.email.mail_from,
    MAIL_FROM_NAME=settings.email.mail_from_name,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    MAIL_DEBUG=False,
    SUPPRESS_SEND=False,  # Set to True for testing
)


def _default_sender() -> NameEmail:
    return NameEmail(
        name=settings.email.mail_from_name,
        email=settings.email.mail_from,
    )


@dataclass(frozen=True)
class Email:
    """
    Immutable representation of an email to be sent.
    To send a plaintext email, provide a `text` value.
    To send an HTML email, provide an `html` value.
    To send a multipart email, provide both the `text` and `html` values.

    :param subject: Email subject
    :type subject: str

    :param recipients: List of recipients in RFC 5322 format
    :type recipients: list[NameEmail]

    :param text: Plain text body of the email
    :type text: str | None

    :param html: HTML body of the email
    :type html: str | None

    :param sender: (Optional) Sender of the email in RFC 5322 format. Defaults to using the values
        of `EMAIL_MAIL_FROM` and `EMAIL_MAIL_FROM_NAME` loaded from environment variables
    :type sender: NameEmail | None

    :param cc: (Optional) List of CC recipients in RFC 5322 format
    :type cc: list[NameEmail]

    :param bcc: (Optional) List of BCC recipients in RFC 5322 format
    :type bcc: list[NameEmail]

    :param reply_to: (Optional) List of reply-to recipients in RFC 5322 format
    :type reply_to: list[NameEmail]

    :param attachments: (Optional) List of attachments
    :type attachments: list[UploadFile]

    :param headers: (Optional) Dictionary of custom SMTP headers
    :type headers: dict[str, str]
    """

    subject: str
    recipients: list[NameEmail]

    text: str | None = None
    html: str | None = None

    sender: NameEmail = field(default_factory=_default_sender)
    cc: list[NameEmail] = field(default_factory=list)
    bcc: list[NameEmail] = field(default_factory=list)
    reply_to: list[NameEmail] = field(default_factory=list)

    attachments: list[UploadFile] = field(default_factory=list)

    headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:  # noqa: D105
        if not self.subject:
            raise ValueError("Subject cannot be empty")

        if not self.recipients:
            raise ValueError("At least one recipient is required")

        if self.text is None and self.html is None:
            raise ValueError("Email must have either a plaintext or HTML body, or both")


def _create_message_schema_fields(email: Email) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "subject": email.subject,
        "recipients": email.recipients,
        "from_email": email.sender.email,
        "from_name": email.sender.name,
        "cc": email.cc,
        "bcc": email.bcc,
        "reply_to": email.reply_to,
        "attachments": email.attachments,
        "headers": email.headers or None,
    }

    if email.html and email.text:
        # Create a multipart email
        fields |= {
            "template_body": email.html,
            "subtype": MessageType.html,
            "alternative_body": email.text,
            "multipart_subtype": MultipartSubtypeEnum.alternative,
        }
    elif email.html is not None:
        fields |= {
            "body": email.html,
            "subtype": MessageType.html,
        }
    else:
        fields |= {
            "body": email.text,
            "subtype": MessageType.plain,
        }

    return fields


def _create_fastmail() -> FastMail:
    return FastMail(_conf)


async def send(email: Email) -> None:
    """
    Sends a single email using the provided `email` and SMTP connection configuration `conf`.

    :param email: The email message as a `Email` object to send.
    :param conf: SMTP connection configuration. Defaults to the configuration loaded from environment variables.
    """
    await send_many([email])


async def send_many(emails: list[Email]) -> None:
    """
    Send multiple emails in a single call while reusing the same SMTP connection.

    :param emails: List of email messages as `Email` objects to send.
    """
    fm = _create_fastmail()
    await fm.send_message(
        [MessageSchema(**_create_message_schema_fields(email)) for email in emails],
    )
