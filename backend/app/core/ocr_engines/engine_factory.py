from typing import Dict, Type, Optional
from pathlib import Path

from backend.app.core.ocr_engines.base_engine import BaseOCREngine
# ❌ REMOVE TESSERACT IMPORT
# from backend.app.core.ocr_engines.tesseract_engine import TesseractEngine
from backend.app.core.ocr_engines.easyocr_engine import EasyOCREngine
from backend.app.core.ocr_engines.paddle_engine import PaddleOCREngine
from backend.app.config import get_logger, settings
from backend.app.utils.exceptions import OCREngineNotFoundError

logger = get_logger(__name__)


class OCREngineFactory:

    # ❌ Removed tesseract completely
    _engines: Dict[str, Type[BaseOCREngine]] = {
        "easyocr": EasyOCREngine,
        "paddle": PaddleOCREngine,
        "paddleocr": PaddleOCREngine,
    }

    @classmethod
    def create_engine(
        cls,
        engine_name: Optional[str] = None,
        language: str = "eng",
        **kwargs
    ) -> BaseOCREngine:

        # ✅ Force default engine to easyocr if nothing passed
        if engine_name is None:
            engine_name = "easyocr"

        engine_name = engine_name.lower().strip()

        logger.info(
            f"Creating OCR engine: {engine_name} (lang={language})"
        )

        # ❌ If someone still tries tesseract, block it clearly
        if engine_name == "tesseract":
            raise OCREngineNotFoundError(
                message="Tesseract is disabled. Use 'easyocr' or 'paddle'",
                details={"requested_engine": engine_name}
            )

        if engine_name not in cls._engines:
            available = list(cls._engines.keys())
            logger.error(
                f"OCR engine not found: {engine_name}. Available={available}"
            )
            raise OCREngineNotFoundError(
                message=f"OCR engine '{engine_name}' not found",
                details={
                    "requested_engine": engine_name,
                    "available_engines": available
                }
            )

        engine_class = cls._engines[engine_name]

        try:
            engine = engine_class(language=language, **kwargs)

            logger.info(
                f"OCR engine created successfully: {engine_name}"
            )

            return engine

        except Exception as e:
            logger.error(
                f"Failed to create OCR engine {engine_name}: {e}",
                exc_info=True
            )
            raise OCREngineNotFoundError(
                message=f"Failed to create OCR engine '{engine_name}'",
                details={
                    "engine": engine_name,
                    "error": str(e)
                }
            )

    @classmethod
    async def get_available_engines(cls) -> Dict[str, bool]:
        availability = {}

        for engine_name, engine_class in cls._engines.items():
            try:
                engine = engine_class(language="eng")
                is_available = await engine.is_available()
                availability[engine_name] = is_available

                logger.debug(
                    f"Engine availability: {engine_name} -> {is_available}"
                )

            except Exception as e:
                availability[engine_name] = False
                logger.debug(
                    f"Engine not available: {engine_name}, error={e}"
                )

        logger.info(
            f"Engine availability check complete: {availability}"
        )

        return availability

    @classmethod
    def get_engine_info(cls, engine_name: str) -> Dict[str, any]:
        engine_name = engine_name.lower().strip()

        if engine_name not in cls._engines:
            return {
                "name": engine_name,
                "available": False,
                "error": "Engine not found"
            }

        try:
            engine_class = cls._engines[engine_name]
            engine = engine_class(language="eng")
            return engine.get_engine_info()
        except Exception as e:
            return {
                "name": engine_name,
                "available": False,
                "error": str(e)
            }

    @classmethod
    def list_engines(cls) -> list:
        return sorted(list(cls._engines.keys()))


def create_ocr_engine(
    engine_name: Optional[str] = None,
    language: str = "eng",
    **kwargs
) -> BaseOCREngine:
    return OCREngineFactory.create_engine(engine_name, language, **kwargs)
