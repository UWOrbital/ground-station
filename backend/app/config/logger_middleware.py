from collections.abc import Awaitable, Callable, Sequence
from time import perf_counter

from fastapi import Request, Response
from loguru import logger
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp


def _content_length(headers: Headers) -> int | None:
    """
    Read the ``Content-Length`` header as an int, or None when it is absent or not an integer.

    Used instead of buffering the body so request/response sizes can be logged
    without ever reading (potentially sensitive) body bytes.

    :param headers: the request or response headers.
    :return: the content length as an int, or None if absent or not an integer.
    """
    value = headers.get("content-length")
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


class LoggerMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs request/response metadata.

    :param excluded_endpoints: endpoints whose response won't be logged
    :type excluded_endpoints: Sequence[str]
    """

    def __init__(self, app: ASGIApp, excluded_endpoints: Sequence[str] = ()) -> None:
        super().__init__(app)
        self.excluded_endpoints = excluded_endpoints

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """
        Log request/response metadata around the wrapped handler.

        :param request: the incoming request.
        :param call_next: callable that runs the rest of the stack and returns the response.
        :return: the response produced by the wrapped handler, untouched.
        """
        # Names only — a value can be a secret (e.g. the Keycloak OAuth `code`).
        param_keys = ",".join(sorted(request.query_params.keys()))
        # Size from the header so the (possibly sensitive) body is never read.
        request_size = _content_length(request.headers)
        # From UserIdMiddleware (app.config.user_id_middleware)
        request_user_id = getattr(request.state, "user_id", None)

        logger.bind(
            method=request.method,
            path=request.url.path,
            user_id=request_user_id,
            param_keys=param_keys,
            request_content_length=request_size,
        ).info("Request")

        start_time = perf_counter()
        response = await call_next(request)
        process_time = perf_counter() - start_time

        if request.url.path in self.excluded_endpoints:
            return response

        if response.status_code >= HTTP_500_INTERNAL_SERVER_ERROR:
            logger_severity = "CRITICAL"
        elif response.status_code >= HTTP_400_BAD_REQUEST:
            logger_severity = "ERROR"
        else:
            logger_severity = "INFO"

        logger.bind(
            status=response.status_code,
            response_content_length=_content_length(response.headers),
            duration_ms=round(process_time * 1000, 2),
        ).log(logger_severity, "Response")

        return response
