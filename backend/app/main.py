from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings, get_logger
from app.api.routes import ocr_routes, health_routes
from app.middleware.error_handler import add_exception_handlers
from app.middleware.request_logger import RequestLoggingMiddleware


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Startup started")
    yield
    print("Shutdown")



app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Advanced OCR system for medical and charity documents",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(RequestLoggingMiddleware)


add_exception_handlers(app)


app.include_router(
    health_routes.router,
    prefix="/api/v1",
    tags=["Health"]
)

app.include_router(
    ocr_routes.router,
    prefix="/api/v1/ocr",
    tags=["OCR"]
)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1,
        log_level=settings.LOG_LEVEL.lower()
    )
