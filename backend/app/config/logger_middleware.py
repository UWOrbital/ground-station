from collections.abc import Awaitable, Callable, Sequence
from datetime import datetime
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from loguru import logger
from starlette.datastructures import Headers
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from starlette.types import ASGIApp


def _content_length(headers: Headers) -> str:
    """
    Read the ``Content-Length`` header, or ``"unknown"`` when it is absent.

    Used instead of buffering the body so request/response sizes can be logged
    without ever reading (potentially sensitive) body bytes.

    :param headers: the request or response headers.
    :return: the content length as a string, or ``"unknown"`` if not provided.
    """
    return headers.get("content-length", "unknown")


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
        request_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        request_id = str(uuid4())
        # Names only — a value can be a secret (e.g. the Keycloak OAuth `code`).
        param_keys = sorted(request.query_params.keys())
        # Size from the header so the (possibly sensitive) body is never read.
        request_size = _content_length(request.headers)
        # TODO: update this based on userID header name
        request_user_id = request.headers.get("user_id", "Anonymous")

        logger.info(
            " | ".join(
                [
                    f"REQUEST | Method: {request.method}",
                    f"Request ID: {request_id}",
                    f"URL: {request.url.path}",
                    f"User id: {request_user_id}",
                    f"Param keys: {param_keys}",
                    f"Time: {request_time}",
                    f"Bytes: {request_size}.",
                ]
            )
        )

        start_time = perf_counter()
        response = await call_next(request)
        process_time = perf_counter() - start_time

        if request.url.path in self.excluded_endpoints:
            return response

        if response.status_code >= HTTP_500_INTERNAL_SERVER_ERROR:
            logger_severity = logger.critical
        elif response.status_code >= HTTP_400_BAD_REQUEST:
            logger_severity = logger.error
        else:
            logger_severity = logger.info

        logger_severity(
            " | ".join(
                [
                    f"RESPONSE | Status: {response.status_code}",
                    f"Request ID: {request_id}",
                    f"Bytes: {_content_length(response.headers)}",
                    f"ms Elapsed: {process_time * 1000:.2f}.",
                ]
            )
        )

        return response
