from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Response header used to hand the correlation id back to the caller so an MCC
# operator or ARO client can tie a response to the server-side log trail.
REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that binds a unique correlation id to each request.

    The id is minted server-side, stored on ``request.state.request_id`` (backed
    by the shared ASGI ``scope["state"]`` dict, so it is visible to inner
    middleware and the route handler), exposed on the response via the
    ``X-Request-ID`` header, and bound into the loguru context so every log
    emitted while handling the request carries it. An inbound ``X-Request-ID`` is
    deliberately ignored to avoid log-injection/spoofing; validated propagation
    can be added here later if cross-service tracing is needed.
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        Initialize the middleware.

        :param app: the downstream ASGI application this middleware wraps.
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Attach a fresh request id to the request state, context, and response.

        :param request: the incoming request whose state receives the id.
        :param call_next: callable that runs the rest of the stack and returns the response.
        :return: the response produced by the wrapped handler, with the id header set.
        """
        request_id = str(uuid4())
        request.state.request_id = request_id

        # Bind the id to the loguru context so *every* log emitted during the
        # request (handlers, SQLAlchemy, errors) carries it into logs.api.extra.
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)

        response.headers[REQUEST_ID_HEADER] = request_id
        return response
