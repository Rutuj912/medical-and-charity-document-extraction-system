from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os


class Settings(BaseSettings):

    APP_NAME: str = "Medical-Charity-OCR-System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"


    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4


    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent


    UPLOAD_DIR: str = "storage/uploads"
    MERGED_PDF_DIR: str = "storage/merged_pdfs"
    PROCESSED_IMAGE_DIR: str = "storage/processed_images"
    JSON_TASKS_DIR: str = "storage/json_tasks"
    LOGS_DIR: str = "logs"


    MAX_FILE_SIZE: int = 52428800
    MAX_FILES_PER_UPLOAD: int = 10
    ALLOWED_EXTENSIONS: str = "pdf"


    DEFAULT_OCR_ENGINE: str = "easyocr"
    OCR_CONFIDENCE_THRESHOLD: float = 0.5
    OCR_LANGUAGE: str = "eng"
    OCR_PSM_MODE: int = 3
    OCR_OEM_MODE: int = 3


    ENABLE_MULTI_ENGINE: bool = False
    FALLBACK_OCR_ENGINE: str = "easyocr"


    ENABLE_PREPROCESSING: bool = True
    ENABLE_DENOISING: bool = True
    ENABLE_DESKEWING: bool = True
    ENABLE_BINARIZATION: bool = True
    ENABLE_CONTRAST_ENHANCEMENT: bool = True
    DPI_CONVERSION: int = 300


    DETECT_HANDWRITING: bool = True
    DETECT_TABLES: bool = True
    DETECT_MEDICAL_FORMS: bool = True


    DATABASE_URL: Optional[str] = None
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20


    REDIS_URL: Optional[str] = None
    ENABLE_CACHING: bool = False


    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_TO_FILE: bool = True
    LOG_ROTATION: str = "midnight"
    LOG_RETENTION_DAYS: int = 30


    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"
    CORS_ALLOW_CREDENTIALS: bool = True


    TASK_RETENTION_DAYS: int = 30
    AUTO_CLEANUP: bool = True


    ENABLE_ASYNC_PROCESSING: bool = True
    MAX_CONCURRENT_TASKS: int = 5


    ENABLE_METRICS: bool = False
    SENTRY_DSN: Optional[str] = None


    GOOGLE_CLOUD_VISION_ENABLED: bool = False
    GOOGLE_CLOUD_VISION_KEY_PATH: Optional[str] = None
    AWS_TEXTRACT_ENABLED: bool = False
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    @validator("ALLOWED_EXTENSIONS")
    def parse_allowed_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip().lower() for ext in v.split(",")]
        return v

    @validator("CORS_ORIGINS")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    def get_absolute_path(self, relative_path: str) -> Path:
        return self.BASE_DIR / relative_path

    def create_storage_directories(self):
        directories = [
            self.UPLOAD_DIR,
            self.MERGED_PDF_DIR,
            self.PROCESSED_IMAGE_DIR,
            self.JSON_TASKS_DIR,
            self.LOGS_DIR,
        ]

        for directory in directories:
            dir_path = self.get_absolute_path(directory)
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Directory created/verified: {dir_path}")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True



settings = Settings()



if __name__ != "__main__":
    settings.create_storage_directories()


if __name__ == "__main__":
    print("=" * 60)
    print(f"Application: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print("=" * 60)
    print(f"OCR Engine: {settings.DEFAULT_OCR_ENGINE}")
    print(f"DPI Conversion: {settings.DPI_CONVERSION}")
    print(f"Preprocessing Enabled: {settings.ENABLE_PREPROCESSING}")
    print(f"Multi-Engine: {settings.ENABLE_MULTI_ENGINE}")
    print("=" * 60)
    print("Storage Paths:")
    print(f"  Uploads: {settings.get_absolute_path(settings.UPLOAD_DIR)}")
    print(f"  Merged PDFs: {settings.get_absolute_path(settings.MERGED_PDF_DIR)}")
    print(f"  Processed Images: {settings.get_absolute_path(settings.PROCESSED_IMAGE_DIR)}")
    print(f"  JSON Tasks: {settings.get_absolute_path(settings.JSON_TASKS_DIR)}")
    print(f"  Logs: {settings.get_absolute_path(settings.LOGS_DIR)}")
    print("=" * 60)


    settings.create_storage_directories()
    print("\n✓ All storage directories created successfully!")
