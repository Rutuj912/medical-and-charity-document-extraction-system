from typing import Dict, Any, List, Optional
from pathlib import Path
import numpy as np
from PIL import Image

from backend.app.config import get_logger
from backend.app.core.ocr_engines.base_engine import BaseOCREngine

logger = get_logger(__name__)


class EasyOCREngine(BaseOCREngine):

    def __init__(self, language: str = "en", gpu: bool = False):
        super().__init__(language)
        self.gpu = gpu
        self.reader = None
        self.engine_name = "EasyOCR"

    async def initialize(self) -> bool:
        if self.reader is not None:
            return True

        try:
            import easyocr

            lang_codes = self._get_easyocr_languages()

            self.logger.info(
                f"Initializing EasyOCR",
                languages=lang_codes,
                gpu=self.gpu
            )

            self.reader = easyocr.Reader(
                lang_codes,
                gpu=self.gpu,
                verbose=False
            )

            self.logger.info("EasyOCR initialized successfully")
            return True

        except ImportError:
            self.logger.error("EasyOCR not installed")
            return False
        except Exception as e:
            self.logger.error(f"EasyOCR initialization failed: {e}", exc_info=True)
            return False

    async def is_available(self) -> bool:
        try:
            import easyocr
            return True
        except ImportError:
            return False

    async def process_image(self, image: np.ndarray) -> Dict[str, Any]:
        if self.reader is None:
            await self.initialize()

        if self.reader is None:
            raise RuntimeError("EasyOCR engine not initialized")

        try:
            self.logger.debug("Processing image with EasyOCR")

            results = self.reader.readtext(image)

            full_text = []
            words = []
            total_confidence = 0
            word_count = 0

            for i, (bbox, text, conf) in enumerate(results):
                full_text.append(text)

                x1, y1 = bbox[0]
                x2, y2 = bbox[2]

                words.append({
                    "text": text,
                    "confidence": float(conf * 100),
                    "bbox": {
                        "left": int(x1),
                        "top": int(y1),
                        "width": int(x2 - x1),
                        "height": int(y2 - y1)
                    },
                    "block_num": 0,
                    "line_num": i,
                    "word_num": i
                })

                total_confidence += conf * 100
                word_count += 1

            combined_text = " ".join(full_text)
            avg_confidence = (total_confidence / word_count) if word_count > 0 else 0.0

            result = {
                "text": combined_text,
                "confidence": round(avg_confidence, 2),
                "word_count": word_count,
                "character_count": len(combined_text),
                "words": words,
                "engine": self.engine_name,
                "language": self.language,
                "metadata": {
                    "gpu": self.gpu,
                    "model": "easyocr",
                    "image_size": f"{image.shape[1]}x{image.shape[0]}"
                }
            }

            self.logger.info(
                f"EasyOCR processing completed",
                confidence=avg_confidence,
                words=word_count
            )

            return result

        except Exception as e:
            self.logger.error(f"EasyOCR processing failed: {e}", exc_info=True)
            raise RuntimeError(f"EasyOCR processing error: {str(e)}")

    async def process_image_file(self, image_path: Path) -> Dict[str, Any]:
        try:
            image = Image.open(image_path)

            if image.mode == 'RGBA':
                image = image.convert('RGB')

            image_np = np.array(image)

            return await self.process_image(image_np)

        except Exception as e:
            self.logger.error(f"Failed to load image: {e}")
            raise RuntimeError(f"Image loading error: {str(e)}")

    async def get_supported_languages(self) -> List[str]:
        return [
            'en', 'ch_sim', 'ch_tra', 'ja', 'ko', 'th', 'vi',
            'ar', 'ru', 'de', 'fr', 'es', 'pt', 'tr', 'fa',
            'hi', 'bn', 'ta', 'te', 'kn', 'ml', 'mr', 'ne',
            'it', 'nl', 'pl', 'sv', 'fi', 'da', 'no', 'hu'
        ]

    def _get_easyocr_languages(self) -> List[str]:
        lang_map = {
            'eng': 'en',
            'chi_sim': 'ch_sim',
            'chi_tra': 'ch_tra',
            'jpn': 'ja',
            'kor': 'ko',
            'tha': 'th',
            'vie': 'vi',
            'ara': 'ar',
            'rus': 'ru',
            'deu': 'de',
            'fra': 'fr',
            'spa': 'es',
            'por': 'pt',
            'tur': 'tr',
            'fas': 'fa',
            'hin': 'hi',
            'ben': 'bn',
            'tam': 'ta',
            'tel': 'te',
            'kan': 'kn',
            'mal': 'ml',
            'mar': 'mr',
            'nep': 'ne',
            'ita': 'it',
            'nld': 'nl',
            'pol': 'pl',
            'swe': 'sv',
            'fin': 'fi',
            'dan': 'da',
            'nor': 'no',
            'hun': 'hu'
        }

        if '+' in self.language:
            langs = self.language.split('+')
            return [lang_map.get(lang, 'en') for lang in langs]

        return [lang_map.get(self.language, 'en')]

    async def get_engine_info(self) -> Dict[str, Any]:
        try:
            import easyocr
            version = easyocr.__version__ if hasattr(easyocr, '__version__') else 'unknown'
        except:
            version = 'not installed'

        return {
            "name": self.engine_name,
            "version": version,
            "language": self.language,
            "gpu_enabled": self.gpu,
            "available": await self.is_available(),
            "supported_languages": await self.get_supported_languages()
        }