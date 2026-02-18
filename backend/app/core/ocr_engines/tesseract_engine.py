from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import numpy as np
import cv2
import pytesseract
from PIL import Image
import subprocess
import re

from backend.app.core.ocr_engines.base_engine import BaseOCREngine
from backend.app.config import get_logger, settings
from backend.app.utils.exceptions import (
    OCRProcessingError,
    OCREngineNotFoundError,
    ImageLoadError
)

logger = get_logger(__name__)


class TesseractEngine(BaseOCREngine):
    def __init__(
        self,
        language: str = "eng",
        psm: Optional[int] = None,
        oem: Optional[int] = None,
        **kwargs
    ):
        super().__init__(language, **kwargs)

        self.psm = psm if psm is not None else settings.OCR_PSM_MODE
        self.oem = oem if oem is not None else settings.OCR_OEM_MODE
        self.tesseract_cmd = kwargs.get('tesseract_cmd', None)


        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

        self._initialized = False
        self._version = None

        self.logger.info(
            "Tesseract engine initialized",
            language=self.language,
            psm=self.psm,
            oem=self.oem
        )

    async def initialize(self) -> bool:
        try:

            self._version = pytesseract.get_tesseract_version()

            self.logger.info(
                "Tesseract initialized successfully",
                version=str(self._version),
                language=self.language
            )

            self._initialized = True
            return True

        except pytesseract.TesseractNotFoundError as e:
            self.logger.error(
                "Tesseract not found on system",
                error=str(e)
            )
            raise OCREngineNotFoundError(
                message="Tesseract OCR is not installed or not found in PATH",
                details={
                    "error": str(e),
                    "install_instructions": "Install with: sudo apt-get install tesseract-ocr"
                }
            )
        except Exception as e:
            self.logger.error(
                "Failed to initialize Tesseract",
                error=str(e),
                exc_info=True
            )
            raise OCREngineNotFoundError(
                message=f"Tesseract initialization failed: {str(e)}"
            )

    async def process_image(
        self,
        image: np.ndarray,
        **kwargs
    ) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        try:

            psm = kwargs.get('psm', self.psm)
            oem = kwargs.get('oem', self.oem)
            custom_config = kwargs.get('config', '')


            config = self._build_config(psm, oem, custom_config)


            if isinstance(image, np.ndarray):

                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(image)
            else:
                pil_image = image

            self.logger.debug(
                "Processing image with Tesseract",
                image_size=pil_image.size,
                psm=psm,
                oem=oem
            )


            text = pytesseract.image_to_string(
                pil_image,
                lang=self.language,
                config=config
            )


            data = pytesseract.image_to_data(
                pil_image,
                lang=self.language,
                config=config,
                output_type=pytesseract.Output.DICT
            )


            confidences = [
                int(conf) for conf in data['conf']
                if conf != '-1' and str(conf).strip()
            ]
            overall_confidence = (
                sum(confidences) / len(confidences)
                if confidences else 0.0
            )


            word_results = self._extract_word_data(data)


            result = self.format_output(
                text=text.strip(),
                confidence=overall_confidence,
                word_results=word_results,
                psm=psm,
                oem=oem,
                image_size=pil_image.size,
                word_count_detected=len(word_results)
            )

            self.logger.info(
                "Tesseract OCR completed",
                text_length=len(text),
                confidence=overall_confidence,
                word_count=len(word_results)
            )

            return result

        except Exception as e:
            self.logger.error(
                "Tesseract OCR processing failed",
                error=str(e),
                exc_info=True
            )
            raise OCRProcessingError(
                message=f"Tesseract OCR failed: {str(e)}",
                details={"error": str(e)}
            )

    async def process_image_file(
        self,
        image_path: Path,
        **kwargs
    ) -> Dict[str, Any]:
        if not self._initialized:
            await self.initialize()

        try:

            if not image_path.exists():
                raise ImageLoadError(
                    message=f"Image file not found: {image_path}",
                    details={"path": str(image_path)}
                )

            self.logger.debug(
                "Loading image file",
                path=str(image_path)
            )


            image = cv2.imread(str(image_path))

            if image is None:
                raise ImageLoadError(
                    message=f"Failed to load image: {image_path}",
                    details={"path": str(image_path)}
                )


            result = await self.process_image(image, **kwargs)


            result['metadata']['source_file'] = str(image_path)

            return result

        except ImageLoadError:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to process image file",
                path=str(image_path),
                error=str(e),
                exc_info=True
            )
            raise OCRProcessingError(
                message=f"Failed to process image file: {str(e)}",
                details={
                    "path": str(image_path),
                    "error": str(e)
                }
            )

    def get_supported_languages(self) -> List[str]:
        try:
            langs = pytesseract.get_languages()
            self.logger.debug(
                "Tesseract supported languages",
                count=len(langs),
                languages=langs
            )
            return langs
        except Exception as e:
            self.logger.error(
                "Failed to get supported languages",
                error=str(e)
            )
            return []

    def get_engine_info(self) -> Dict[str, Any]:
        info = {
            "name": "Tesseract",
            "type": "OCR Engine",
            "version": str(self._version) if self._version else "unknown",
            "initialized": self._initialized,
            "language": self.language,
            "psm": self.psm,
            "oem": self.oem,
        }


        if self._initialized:
            try:
                info["supported_languages"] = self.get_supported_languages()
            except:
                pass

        return info

    def _build_config(
        self,
        psm: int,
        oem: int,
        custom_config: str = ""
    ) -> str:
        config_parts = []


        if psm is not None:
            config_parts.append(f"--psm {psm}")


        if oem is not None:
            config_parts.append(f"--oem {oem}")


        if custom_config:
            config_parts.append(custom_config)

        return " ".join(config_parts)

    def _extract_word_data(
        self,
        data: Dict[str, List]
    ) -> List[Dict[str, Any]]:
        words = []

        for i in range(len(data['text'])):

            if not data['text'][i].strip():
                continue


            if data['conf'][i] == '-1':
                continue

            word = {
                "text": data['text'][i],
                "confidence": float(data['conf'][i]),
                "bbox": {
                    "left": int(data['left'][i]),
                    "top": int(data['top'][i]),
                    "width": int(data['width'][i]),
                    "height": int(data['height'][i])
                },
                "block_num": int(data['block_num'][i]),
                "par_num": int(data['par_num'][i]),
                "line_num": int(data['line_num'][i]),
                "word_num": int(data['word_num'][i])
            }

            words.append(word)

        return words



PSM_MODES = {
    0: "Orientation and script detection (OSD) only",
    1: "Automatic page segmentation with OSD",
    2: "Automatic page segmentation, but no OSD, or OCR",
    3: "Fully automatic page segmentation, but no OSD (Default)",
    4: "Assume a single column of text of variable sizes",
    5: "Assume a single uniform block of vertically aligned text",
    6: "Assume a single uniform block of text",
    7: "Treat the image as a single text line",
    8: "Treat the image as a single word",
    9: "Treat the image as a single word in a circle",
    10: "Treat the image as a single character",
    11: "Sparse text. Find as much text as possible in no particular order",
    12: "Sparse text with OSD",
    13: "Raw line. Treat the image as a single text line, bypassing hacks"
}


OEM_MODES = {
    0: "Legacy engine only",
    1: "Neural nets LSTM engine only",
    2: "Legacy + LSTM engines",
    3: "Default, based on what is available"
}
