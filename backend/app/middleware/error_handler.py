from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.config import get_logger
from backend.app.utils.exceptions import (
    OCRSystemException,
    APIException,
    handle_exception
)

logger = get_logger(__name__)


def add_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(OCRSystemException)
    async def ocr_system_exception_handler(
        request: Request,
        exc: OCRSystemException
    ) -> JSONResponse:

        logger.error(
            f"OCR System Exception | "
            f"message={exc.message} | "
            f"error_code={exc.error_code} | "
            f"details={exc.details} | "
            f"path={request.url.path} | "
            f"method={request.method}",
            exc_info=True
        )

        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        if isinstance(exc, APIException):
            status_code = exc.status_code

        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict()
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException
    ) -> JSONResponse:

        logger.warning(
            f"HTTP Exception | "
            f"status_code={exc.status_code} | "
            f"detail={exc.detail} | "
            f"path={request.url.path} | "
            f"method={request.method}"
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTPException",
                "message": exc.detail,
                "status_code": exc.status_code
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:

        logger.warning(
            f"Validation Error | "
            f"errors={exc.errors()} | "
            f"path={request.url.path} | "
            f"method={request.method}"
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "ValidationError",
                "message": "Request validation failed",
                "details": exc.errors()
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:

        logger.error(
            f"Unhandled Exception | "
            f"type={type(exc).__name__} | "
            f"error={str(exc)} | "
            f"path={request.url.path} | "
            f"method={request.method}",
            exc_info=True
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred",
                "details": str(exc)
            }
        )
