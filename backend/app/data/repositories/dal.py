from collections.abc import Callable
from typing import Any, TypeVar, cast

from app.data.repositories.abstract_repository import AbstractRepository
from app.data.repositories.repositories import (
    ARORequestRepository,
    AROUserAuthTokenRepository,
    AROUserCallsignRepository,
    AROUserLoginRepository,
    AROUsersRepository,
    CommandsRepository,
    CommsSessionRepository,
    ImageRepository,
    MainCommandRepository,
    MainTelemetryRepository,
    MCCUsersRepository,
    PacketRepository,
    TelemetryRepository,
)

R = TypeVar("R", bound=AbstractRepository[Any, Any])


class DAL:
    """
    Data Access Layer: the single registry of repositories.

    Each class attribute maps a name to its repository *class*. Two usages:

    - Inside a route, inject the repository via FastAPI's dependency injection::

        commands: Annotated[CommandsRepository, Depends(DAL.get_repo(DAL.commands))]

    - Outside the request lifecycle (services, auth helpers, scripts), instantiate
      the repository directly::

        commands = DAL.commands()
    """

    mcc_users = MCCUsersRepository
    aro_users = AROUsersRepository
    aro_user_auth_tokens = AROUserAuthTokenRepository
    aro_user_callsigns = AROUserCallsignRepository
    aro_user_logins = AROUserLoginRepository
    aro_requests = ARORequestRepository
    main_commands = MainCommandRepository
    main_telemetries = MainTelemetryRepository
    comms_sessions = CommsSessionRepository
    packets = PacketRepository
    commands = CommandsRepository
    telemetry = TelemetryRepository
    images = ImageRepository

    # Cache of provider callables keyed by repository class. FastAPI keys
    # dependency_overrides by callable identity, so get_repo must return the
    # *same* provider object for a given repository class to stay overridable.
    _providers: dict[type[Any], Callable[[], Any]] = {}

    @staticmethod
    def get_repo(repo_cls: type[R]) -> Callable[[], R]:
        """
        Return a stable FastAPI dependency provider that instantiates a repository.

        :param repo_cls: the repository class to provide, e.g. ``DAL.commands``.
        :return: a cached zero-argument callable returning a fresh repository instance.
        """
        if repo_cls not in DAL._providers:

            def _provider() -> R:
                return repo_cls()

            DAL._providers[repo_cls] = _provider
        return cast("Callable[[], R]", DAL._providers[repo_cls])
