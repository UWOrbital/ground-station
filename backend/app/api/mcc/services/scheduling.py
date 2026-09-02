from app.data.models.transactional_models import CommsSession
from app.data.repositories.dal import DAL


def assert_not_locked_out(session: CommsSession) -> None:
    """
    Raises ValueError if the given session is locked out or does not exist.

    :param session: Target session.
    :raises ValueError: if the session does not exist, or is locked out.
    """
    if DAL.comms_sessions().is_locked_out(session):
        raise ValueError("Session is within its lockout window; command scheduling is frozen")
