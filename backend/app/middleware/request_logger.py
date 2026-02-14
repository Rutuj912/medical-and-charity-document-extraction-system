import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        import time
        request_id = "N/A"

        start_time = time.time()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            logger.info(
                f"Request completed | "
                f"method={request.method} | "
                f"path={request.url.path} | "
                f"status={response.status_code} | "
                f"duration={duration:.4f}s"
            )

            return response

        except Exception as e:
            duration = time.time() - start_time

            logger.error(
                f"Request failed | "
                f"method={request.method} | "
                f"path={request.url.path} | "
                f"error={str(e)} | "
                f"duration={duration:.4f}s"
            )

            raise e
