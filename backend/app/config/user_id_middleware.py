from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from jwt import decode
from jwt.exceptions import PyJWTError
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.env_settings.backend_config import settings


class UserIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that takes a request, and if it is authenticated, extracts the user ID and
    attaches it to the request state.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Extracts the user ID from the JWT token in the Authorization header and sets it in request.state.user_id.
        If the Authorization header is missing or the token is invalid, request.state.user_id will
        not be set so that the app can treat the request as unauthenticated.

        :param request: the incoming request whose state receives the ids.
        :param call_next: callable that runs the rest of the stack and returns the response.
        :return: the response produced by the wrapped handler, with the id headers set.
        """
        auth_header = request.headers.get("authorization")

        if auth_header:
            user_id = self.extract_user_id(auth_header)

            if user_id is not None:
                request.state.user_id = user_id

        response = await call_next(request)
        return response

    def extract_user_id(self, auth_header: str) -> str | None:
        """
        Extracts the user ID from the JWT token.
        If the token is invalid or 'sub' is missing, returns None.
        Also logs a warning if the 'sub' key is missing in the decoded payload.
        """
        scheme, _, token = auth_header.partition(" ")

        if scheme.lower() != "bearer" or not token:
            return None

        try:
            decoded = decode(token, key=settings.auth.jwt_secret, algorithms=["HS256"])
        except PyJWTError:
            # Treat decoding errors as an unauthenticated request
            return None

        user_id = decoded.get("sub", None)

        if user_id is None:
            logger.warning(
                "UserIdMiddleware: JWT token decoded but 'sub' key in payload is missing, "
                "did the structure of the tokens we generate change?"
            )

        return user_id
