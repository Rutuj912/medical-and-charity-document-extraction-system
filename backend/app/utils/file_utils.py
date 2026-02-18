from pathlib import Path
from typing import Optional, List, Union
import shutil
import aiofiles
import os
from datetime import datetime, timedelta
import cv2
import numpy as np
from PIL import Image

from backend.app.config import get_logger, settings
from backend.app.utils.exceptions import (
    FileException,
    FileReadError,
    FileWriteError,
    ImageLoadError,
    ImageFormatError
)

logger = get_logger(__name__)


async def save_uploaded_file(
    file,
    destination: Path,
    chunk_size: int = 1024 * 1024
) -> Path:
    try:

        destination.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Saving uploaded file",
            filename=file.filename,
            destination=str(destination)
        )


        async with aiofiles.open(destination, 'wb') as f:
            while chunk := await file.read(chunk_size):
                await f.write(chunk)


        file_size = destination.stat().st_size

        logger.info(
            "File saved successfully",
            destination=str(destination),
            size_bytes=file_size
        )

        return destination

    except Exception as e:
        logger.error(
            "Failed to save uploaded file",
            filename=getattr(file, 'filename', 'unknown'),
            destination=str(destination),
            error=str(e),
            exc_info=True
        )
        raise FileWriteError(
            message=f"Failed to save file: {str(e)}",
            details={
                "filename": getattr(file, 'filename', 'unknown'),
                "destination": str(destination),
                "error": str(e)
            }
        )


async def cleanup_files(
    directory: Path,
    days: int = 30,
    pattern: str = "*"
) -> int:
    if not directory.exists():
        logger.warning(
            "Cleanup directory does not exist",
            directory=str(directory)
        )
        return 0

    deleted_count = 0
    cutoff_time = datetime.now() - timedelta(days=days)

    try:
        for file_path in directory.glob(pattern):
            if file_path.is_file():

                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

                if mtime < cutoff_time:
                    file_path.unlink()
                    deleted_count += 1
                    logger.debug(
                        "Deleted old file",
                        path=str(file_path),
                        age_days=(datetime.now() - mtime).days
                    )

        logger.info(
            "Cleanup completed",
            directory=str(directory),
            deleted_count=deleted_count,
            days=days
        )

        return deleted_count

    except Exception as e:
        logger.error(
            "Cleanup failed",
            directory=str(directory),
            error=str(e),
            exc_info=True
        )
        return deleted_count


def load_image(image_path: Path) -> np.ndarray:
    try:
        if not image_path.exists():
            raise ImageLoadError(
                message=f"Image file not found: {image_path}",
                details={"path": str(image_path)}
            )


        image = cv2.imread(str(image_path))

        if image is None:

            try:
                pil_image = Image.open(image_path)
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            except Exception:
                raise ImageLoadError(
                    message=f"Failed to load image: {image_path}",
                    details={"path": str(image_path)}
                )

        logger.debug(
            "Image loaded successfully",
            path=str(image_path),
            shape=image.shape
        )

        return image

    except ImageLoadError:
        raise
    except Exception as e:
        logger.error(
            "Failed to load image",
            path=str(image_path),
            error=str(e),
            exc_info=True
        )
        raise ImageLoadError(
            message=f"Failed to load image: {str(e)}",
            details={"path": str(image_path), "error": str(e)}
        )


def save_image(image: np.ndarray, output_path: Path) -> Path:
    try:

        output_path.parent.mkdir(parents=True, exist_ok=True)


        success = cv2.imwrite(str(output_path), image)

        if not success:
            raise FileWriteError(
                message=f"Failed to save image: {output_path}",
                details={"path": str(output_path)}
            )

        logger.debug(
            "Image saved successfully",
            path=str(output_path)
        )

        return output_path

    except Exception as e:
        logger.error(
            "Failed to save image",
            path=str(output_path),
            error=str(e),
            exc_info=True
        )
        raise FileWriteError(
            message=f"Failed to save image: {str(e)}",
            details={"path": str(output_path), "error": str(e)}
        )


def get_image_info(image_path: Path) -> dict:
    try:
        image = load_image(image_path)

        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) > 2 else 1

        return {
            "path": str(image_path),
            "width": width,
            "height": height,
            "channels": channels,
            "size_bytes": image_path.stat().st_size,
            "format": image_path.suffix.lower()
        }

    except Exception as e:
        logger.error(
            "Failed to get image info",
            path=str(image_path),
            error=str(e)
        )
        return {
            "path": str(image_path),
            "error": str(e)
        }


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_unique_filename(
    directory: Path,
    base_name: str,
    extension: str
) -> Path:
    if not extension.startswith('.'):
        extension = f'.{extension}'


    file_path = directory / f"{base_name}{extension}"

    if not file_path.exists():
        return file_path


    counter = 1
    while True:
        file_path = directory / f"{base_name}_{counter}{extension}"
        if not file_path.exists():
            return file_path
        counter += 1


def get_file_size_mb(file_path: Path) -> float:
    size_bytes = file_path.stat().st_size
    return size_bytes / (1024 * 1024)


def validate_image_format(file_path: Path) -> bool:
    supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp'}
    return file_path.suffix.lower() in supported_formats
