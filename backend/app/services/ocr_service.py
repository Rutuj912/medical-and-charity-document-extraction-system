from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

from backend.app.config import get_logger, settings
from backend.app.utils.exceptions import (
    OCRException,
    OCRProcessingError,
    OCRNoTextFoundError
)
from backend.app.services.pdf_service import PDFService
from backend.app.services.preprocessing_service import PreprocessingService
from backend.app.core.ocr_engines import OCREngineFactory, create_ocr_engine
from backend.app.utils.file_utils import load_image, ensure_directory

logger = get_logger(__name__)


class OCRService:

    def __init__(self):
        self.logger = logger
        self.default_engine = settings.DEFAULT_OCR_ENGINE
        self.pdf_service = PDFService()
        self.preprocessing_service = PreprocessingService()
        self._engine_cache = {}

        self.logger.info(
            f"OCR Service initialized | default_engine={self.default_engine}"
        )

    async def process_pdf(
        self,
        pdf_path: Path,
        output_dir: Optional[Path] = None,
        engine: Optional[str] = None,
        language: str = "eng",
        preprocess: bool = True,
        document_type: str = "general",
        **options
    ) -> Dict[str, Any]:

        self.logger.info(
            f"Processing PDF | path={pdf_path} | "
            f"engine={engine or self.default_engine} | preprocess={preprocess}"
        )

        try:
            if output_dir is None:
                output_dir = settings.get_absolute_path(settings.PROCESSED_IMAGE_DIR)
            ensure_directory(output_dir)

            is_scanned = await self.pdf_service.is_pdf_scanned(pdf_path)

            self.logger.info(
                f"PDF type detected: {'scanned' if is_scanned else 'text-based'}"
            )

            if not is_scanned:
                self.logger.info("Extracting text directly from PDF")
                text_result = await self.pdf_service.extract_text_from_pdf(pdf_path)

                return {
                    "pdf_path": str(pdf_path),
                    "is_scanned": False,
                    "processing_method": "direct_text_extraction",
                    "page_count": text_result['page_count'],
                    "total_characters": text_result['total_characters'],
                    "text": text_result['full_text'],
                    "pages": text_result['pages'],
                    "confidence": 100.0
                }

            self.logger.info("Converting PDF to images")
            image_paths = await self.pdf_service.convert_pdf_to_images(
                pdf_path,
                output_dir,
                dpi=settings.DPI_CONVERSION
            )

            self.logger.info(f"Converted to {len(image_paths)} images")

            if preprocess:
                self.logger.info(f"Preprocessing images | type={document_type}")
                processed_paths = []

                for img_path in image_paths:
                    processed_path = await self.preprocessing_service.preprocess_for_ocr(
                        img_path,
                        document_type=document_type
                    )
                    processed_paths.append(processed_path)

                self.logger.info(f"Preprocessed {len(processed_paths)} images")
            else:
                processed_paths = image_paths

            self.logger.info("Running OCR on images")
            ocr_results = await self.process_images(
                processed_paths,
                engine=engine,
                language=language
            )

            result = self._combine_page_results(
                pdf_path,
                ocr_results,
                is_scanned=True
            )

            self.logger.info(
                f"PDF OCR completed | pages={len(ocr_results)} | "
                f"chars={result['total_characters']} | "
                f"avg_conf={result['average_confidence']}"
            )

            return result

        except Exception as e:
            self.logger.error(
                f"PDF OCR failed | path={pdf_path} | error={str(e)}",
                exc_info=True
            )
            raise OCRProcessingError(
                message=f"Failed to process PDF: {str(e)}",
                details={
                    "pdf_path": str(pdf_path),
                    "error": str(e)
                }
            )

    async def process_images(
        self,
        image_paths: List[Path],
        engine: Optional[str] = None,
        language: str = "eng",
        parallel: bool = False
    ) -> List[Dict[str, Any]]:

        self.logger.info(
            f"Processing {len(image_paths)} images | "
            f"engine={engine or self.default_engine} | "
            f"language={language} | parallel={parallel}"
        )

        try:
            ocr_engine = await self._get_engine(engine, language)
            results = []

            for i, image_path in enumerate(image_paths, 1):
                self.logger.debug(f"Processing image {i}/{len(image_paths)}")

                try:
                    result = await ocr_engine.process_image_file(image_path)
                    result['image_path'] = str(image_path)
                    result['page_number'] = i
                    results.append(result)
                except Exception as e:
                    self.logger.error(
                        f"Failed to process {image_path} | error={e}"
                    )
                    results.append(
                        self._create_error_result(image_path, str(e))
                    )

            self.logger.info(
                f"OCR processing completed for {len(results)} images"
            )

            return results

        except Exception as e:
            self.logger.error(
                f"Batch OCR failed | error={str(e)}",
                exc_info=True
            )
            raise OCRProcessingError(
                message=f"Failed to process images: {str(e)}",
                details={
                    "image_count": len(image_paths),
                    "error": str(e)
                }
            )

    async def _get_engine(
        self,
        engine: Optional[str] = None,
        language: str = "eng"
    ):

        engine_name = engine or self.default_engine
        cache_key = f"{engine_name}_{language}"

        if cache_key in self._engine_cache:
            return self._engine_cache[cache_key]

        ocr_engine = create_ocr_engine(engine_name, language)
        await ocr_engine.initialize()

        self._engine_cache[cache_key] = ocr_engine

        return ocr_engine

    def _combine_page_results(
        self,
        pdf_path: Path,
        page_results: List[Dict[str, Any]],
        is_scanned: bool
    ) -> Dict[str, Any]:

        full_text = "\n\n".join(
            f"--- Page {i+1} ---\n{result.get('text','')}"
            for i, result in enumerate(page_results)
        )

        total_chars = sum(
            result.get('character_count', 0)
            for result in page_results
        )

        total_words = sum(
            result.get('word_count', 0)
            for result in page_results
        )

        avg_confidence = sum(
            result.get('confidence', 0)
            for result in page_results
        ) / len(page_results) if page_results else 0.0

        if total_chars < 10:
            self.logger.warning("Very little text found in OCR results")

        return {
            "pdf_path": str(pdf_path),
            "is_scanned": is_scanned,
            "processing_method": "ocr_pipeline",
            "page_count": len(page_results),
            "total_characters": total_chars,
            "total_words": total_words,
            "average_confidence": round(avg_confidence, 2),
            "text": full_text,
            "pages": page_results,
            "engine": page_results[0].get('engine') if page_results else None,
            "language": page_results[0].get('language') if page_results else None
        }

    def _create_error_result(
        self,
        image_path: Path,
        error_message: str
    ) -> Dict[str, Any]:

        return {
            "image_path": str(image_path),
            "text": "",
            "confidence": 0.0,
            "word_count": 0,
            "character_count": 0,
            "error": error_message,
            "success": False
        }
