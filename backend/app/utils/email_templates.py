from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "emails"
_env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR), autoescape=select_autoescape(["html"]))


def render_email_template(template_name: str, **context: object) -> str:
    """
    Render an HTML email template from app/templates/emails.

    :param template_name: file name of the template, e.g. "reset_password.html".
    :param context: values substituted into the template's placeholders.
    :return: the rendered HTML string.
    """
    return _env.get_template(template_name).render(**context)
