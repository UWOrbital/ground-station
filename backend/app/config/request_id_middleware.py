from collections.abc import Awaitable, Callable
from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

# Response headers used to hand the correlation ids back to the caller so an MCC
# operator or ARO client can tie a response to the server-side log trail.
REQUEST_ID_HEADER = "X-Request-ID"
RESPONSE_ID_HEADER = "X-Response-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Bind a unique correlation id to each request and a separate one to each response for log tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Attach fresh request/response ids to the request state, context, and response.

        :param request: the incoming request whose state receives the ids.
        :param call_next: callable that runs the rest of the stack and returns the response.
        :return: the response produced by the wrapped handler, with the id headers set.
        """
        # Minted server-side; an inbound X-Request-ID is ignored to avoid spoofing/log-injection.
        request_id = str(uuid4())
        request.state.request_id = request_id

        # Bind the id to the loguru context so *every* log emitted during the
        # request (handlers, SQLAlchemy, errors) carries it into logs.api.extra.
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)

        # Distinct id for the response, so a response can be referenced on its own.
        response_id = str(uuid4())
        request.state.response_id = response_id

        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[RESPONSE_ID_HEADER] = response_id
        return response
