from typing import Dict, Type, Optional
from pathlib import Path

from app.core.ocr_engines.base_engine import BaseOCREngine
from app.core.ocr_engines.tesseract_engine import TesseractEngine
from app.core.ocr_engines.easyocr_engine import EasyOCREngine
from app.core.ocr_engines.paddle_engine import PaddleOCREngine
from app.config import get_logger, settings
from app.utils.exceptions import OCREngineNotFoundError

logger = get_logger(__name__)


class OCREngineFactory:

    _engines: Dict[str, Type[BaseOCREngine]] = {
        "tesseract": TesseractEngine,
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
        if engine_name is None:
            engine_name = settings.DEFAULT_OCR_ENGINE


        engine_name = engine_name.lower().strip()

        logger.info(
            "Creating OCR engine",
            engine=engine_name,
            language=language
        )


        if engine_name not in cls._engines:
            available = list(cls._engines.keys())
            logger.error(
                "OCR engine not found",
                engine=engine_name,
                available=available
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
                "OCR engine created successfully",
                engine=engine_name,
                engine_class=engine_class.__name__
            )
            return engine

        except Exception as e:
            logger.error(
                "Failed to create OCR engine",
                engine=engine_name,
                error=str(e),
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

            if engine_name == "paddleocr":
                continue

            try:
                engine = engine_class(language="eng")
                is_available = await engine.is_available()
                availability[engine_name] = is_available

                logger.debug(
                    "Engine availability checked",
                    engine=engine_name,
                    available=is_available
                )

            except Exception as e:
                availability[engine_name] = False
                logger.debug(
                    "Engine not available",
                    engine=engine_name,
                    error=str(e)
                )

        logger.info(
            "OCR engines availability check complete",
            available_count=sum(availability.values()),
            total_count=len(availability),
            engines=availability
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
    def register_engine(
        cls,
        name: str,
        engine_class: Type[BaseOCREngine]
    ) -> None:
        if not issubclass(engine_class, BaseOCREngine):
            raise ValueError(
                f"Engine class must inherit from BaseOCREngine"
            )

        name = name.lower().strip()
        cls._engines[name] = engine_class

        logger.info(
            "Custom OCR engine registered",
            engine_name=name,
            engine_class=engine_class.__name__
        )

    @classmethod
    def list_engines(cls) -> list:
        engines = []
        seen_classes = set()

        for name, engine_class in cls._engines.items():
            if engine_class not in seen_classes:
                engines.append(name)
                seen_classes.add(engine_class)

        return sorted(engines)



def create_ocr_engine(
    engine_name: Optional[str] = None,
    language: str = "eng",
    **kwargs
) -> BaseOCREngine:
    return OCREngineFactory.create_engine(engine_name, language, **kwargs)


if __name__ == "__main__":
    import asyncio

    async def test_factory():
        print("=" * 60)
        print("OCR Engine Factory Test")
        print("=" * 60)


        print("\n1. Registered Engines:")
        engines = OCREngineFactory.list_engines()
        for engine in engines:
            print(f"   - {engine}")


        print("\n2. Checking Engine Availability...")
        available = await OCREngineFactory.get_available_engines()
        for engine, status in available.items():
            status_text = "✓ Available" if status else "✗ Not Available"
            print(f"   {engine}: {status_text}")


        print("\n3. Creating Default Engine...")
        try:
            engine = OCREngineFactory.create_engine()
            info = engine.get_engine_info()
            print(f"   Created: {info['name']}")
            print(f"   Status: {info.get('status', 'unknown')}")
        except Exception as e:
            print(f"   Error: {e}")

        print("\n" + "=" * 60)
        print("Factory test complete!")

    asyncio.run(test_factory())
