from fastapi import APIRouter, status
from datetime import datetime
from typing import Dict, Any

from app.config import settings, get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check() -> Dict[str, Any]:
    import os
    import psutil


    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return {
        "status": "healthy",
        "app": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
        },
        "system": {
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_mb": round(memory.total / 1024 / 1024, 2),
                "available_mb": round(memory.available / 1024 / 1024, 2),
                "percent_used": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                "percent_used": disk.percent
            }
        },
        "configuration": {
            "ocr_engine": settings.DEFAULT_OCR_ENGINE,
            "dpi": settings.DPI_CONVERSION,
            "preprocessing_enabled": settings.ENABLE_PREPROCESSING,
            "max_file_size_mb": round(settings.MAX_FILE_SIZE / 1024 / 1024, 2),
            "max_files_per_upload": settings.MAX_FILES_PER_UPLOAD
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, str]:




    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
