from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List, Dict, Any
from datetime import datetime

from backend.app.config import get_logger
from backend.app.utils.exceptions import InvalidFileTypeError, FileSizeExceededError
from pathlib import Path
import shutil

from backend.app.services.ocr_service import OCRService

ocr_service = OCRService()

router = APIRouter()
logger = get_logger(__name__)


@router.post("/process", status_code=status.HTTP_200_OK)
async def process_documents(
    files: List[UploadFile] = File(...)
) -> Dict[str, Any]:

    results = []

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    for file in files:

        file_path = upload_dir / file.filename

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run OCR
        result = await ocr_service.process_pdf(file_path)

        results.append({
            "filename": file.filename,
            "ocr_result": result
        })

    return {
        "status": "completed",
        "documents_processed": len(results),
        "results": results,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/task/{task_id}", status_code=status.HTTP_200_OK)
async def get_task_status(task_id: str) -> Dict[str, Any]:

    logger.info(
        f"Task status request | task_id={task_id}"
    )

    return {
        "task_id": task_id,
        "status": "processing",
        "progress": 0,
        "message": "Task status endpoint - implementation pending",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/tasks", status_code=status.HTTP_200_OK)
async def list_tasks(
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:

    logger.info(
        f"Task list request | limit={limit} | offset={offset}"
    )

    return {
        "tasks": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "message": "Task listing endpoint - implementation pending",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.delete("/task/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(task_id: str) -> Dict[str, Any]:

    logger.info(
        f"Task deletion request | task_id={task_id}"
    )

    return {
        "task_id": task_id,
        "status": "deleted",
        "message": "Task deletion endpoint - implementation pending",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/engines", status_code=status.HTTP_200_OK)
async def list_ocr_engines() -> Dict[str, Any]:

    logger.info("OCR engines list request")

    return {
        "engines": [
            {
                "name": "tesseract",
                "available": False,
                "version": "TBD",
                "status": "not_implemented"
            },
            {
                "name": "easyocr",
                "available": False,
                "version": "TBD",
                "status": "not_implemented"
            },
            {
                "name": "paddleocr",
                "available": False,
                "version": "TBD",
                "status": "not_implemented"
            }
        ],
        "default_engine": "tesseract",
        "message": "OCR engines endpoint - implementation pending",
        "timestamp": datetime.utcnow().isoformat()
    }
