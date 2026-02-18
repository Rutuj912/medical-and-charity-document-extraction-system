import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.app.config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)

            logger.info(
                f"Request completed | method={request.method} "
                f"| path={request.url.path} "
                f"| status={response.status_code}"
            )

            return response

        except Exception as e:
            logger.error(
                f"Request failed | method={request.method} "
                f"| path={request.url.path} "
                f"| error={str(e)}"
            )
            raise e
