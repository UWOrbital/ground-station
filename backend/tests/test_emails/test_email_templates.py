import pytest
from jinja2 import TemplateNotFound

from app.utils.email import render_email_template


def test_reset_password_template_fills_placeholders() -> None:
    """The reset template substitutes the user's name and token."""
    html = render_email_template("reset_password.html", name="Jane Doe", token="abc.def.ghi")

    assert "Jane Doe" in html
    assert "abc.def.ghi" in html
    assert "{{" not in html


def test_reset_password_template_escapes_html() -> None:
    """User-controlled values are autoescaped so a name can't inject markup."""
    html = render_email_template("reset_password.html", name="<script>alert(1)</script>", token="t")

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_missing_template_raises() -> None:
    """Asking for a template that doesn't exist fails loudly instead of sending an empty email."""
    with pytest.raises(TemplateNotFound):
        render_email_template("does_not_exist.html")
