from app.data.models.transactional_models import Session
from app.data.repositories.dal import DAL
from app.exceptions import InvalidStateError


def assert_not_locked_out(session: Session) -> None:
    """
    Raises ValueError if the given session is locked out or does not exist.

    :param session: Target session.
    :raises ValueError: if the session does not exist, or is locked out.
    """
    if DAL.sessions().is_locked_out(session):
        raise InvalidStateError("Session is within its lockout window; command scheduling is frozen")
