from typing import Dict, Any, List, Optional
from pathlib import Path
import numpy as np
from PIL import Image
import cv2

from backend.app.config import get_logger
from backend.app.core.ocr_engines.base_engine import BaseOCREngine

logger = get_logger(__name__)


class PaddleOCREngine(BaseOCREngine):

    def __init__(self, language: str = "en", use_gpu: bool = False):
        super().__init__(language)
        self.use_gpu = use_gpu
        self.ocr = None
        self.engine_name = "PaddleOCR"

    async def initialize(self) -> bool:
        if self.ocr is not None:
            return True

        try:
            from paddleocr import PaddleOCR

            lang = self._get_paddle_language()

            self.logger.info(
                f"Initializing PaddleOCR",
                language=lang,
                gpu=self.use_gpu
            )

            self.ocr = PaddleOCR(
                lang=lang,
                use_angle_cls=True,
                use_gpu=self.use_gpu,
                show_log=False
            )

            self.logger.info("PaddleOCR initialized successfully")
            return True

        except ImportError:
            self.logger.error("PaddleOCR not installed")
            return False
        except Exception as e:
            self.logger.error(f"PaddleOCR initialization failed: {e}", exc_info=True)
            return False

    async def is_available(self) -> bool:
        try:
            from paddleocr import PaddleOCR
            return True
        except ImportError:
            return False

    async def process_image(self, image: np.ndarray) -> Dict[str, Any]:
        if self.ocr is None:
            await self.initialize()

        if self.ocr is None:
            raise RuntimeError("PaddleOCR engine not initialized")

        try:
            self.logger.debug("Processing image with PaddleOCR")

            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)

            results = self.ocr.ocr(image, cls=True)

            if not results or not results[0]:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "word_count": 0,
                    "character_count": 0,
                    "words": [],
                    "engine": self.engine_name,
                    "language": self.language,
                    "metadata": {}
                }

            full_text = []
            words = []
            total_confidence = 0
            word_count = 0

            for i, line in enumerate(results[0]):
                bbox = line[0]
                text_info = line[1]
                text = text_info[0]
                conf = text_info[1]

                full_text.append(text)

                x_coords = [point[0] for point in bbox]
                y_coords = [point[1] for point in bbox]
                x1, y1 = int(min(x_coords)), int(min(y_coords))
                x2, y2 = int(max(x_coords)), int(max(y_coords))

                words.append({
                    "text": text,
                    "confidence": float(conf * 100),
                    "bbox": {
                        "left": x1,
                        "top": y1,
                        "width": x2 - x1,
                        "height": y2 - y1
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
                    "gpu": self.use_gpu,
                    "model": "paddleocr",
                    "image_size": f"{image.shape[1]}x{image.shape[0]}",
                    "angle_classification": True
                }
            }

            self.logger.info(
                f"PaddleOCR processing completed",
                confidence=avg_confidence,
                words=word_count
            )

            return result

        except Exception as e:
            self.logger.error(f"PaddleOCR processing failed: {e}", exc_info=True)
            raise RuntimeError(f"PaddleOCR processing error: {str(e)}")

    async def process_image_file(self, image_path: Path) -> Dict[str, Any]:
        try:
            image = cv2.imread(str(image_path))

            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")

            return await self.process_image(image)

        except Exception as e:
            self.logger.error(f"Failed to load image: {e}")
            raise RuntimeError(f"Image loading error: {str(e)}")

    async def get_supported_languages(self) -> List[str]:
        return [
            'ch', 'en', 'fr', 'german', 'korean', 'japan',
            'chinese_cht', 'ta', 'te', 'ka', 'latin', 'arabic',
            'cyrillic', 'devanagari'
        ]

    def _get_paddle_language(self) -> str:
        lang_map = {
            'eng': 'en',
            'chi_sim': 'ch',
            'chi_tra': 'chinese_cht',
            'fra': 'fr',
            'deu': 'german',
            'kor': 'korean',
            'jpn': 'japan',
            'tam': 'ta',
            'tel': 'te',
            'kan': 'ka',
            'ara': 'arabic',
            'rus': 'cyrillic',
            'hin': 'devanagari'
        }

        if '+' in self.language:
            langs = self.language.split('+')
            return lang_map.get(langs[0], 'en')

        return lang_map.get(self.language, 'en')

    async def get_engine_info(self) -> Dict[str, Any]:
        try:
            import paddle
            version = paddle.__version__ if hasattr(paddle, '__version__') else 'unknown'
        except:
            version = 'not installed'

        return {
            "name": self.engine_name,
            "version": version,
            "language": self.language,
            "gpu_enabled": self.use_gpu,
            "available": await self.is_available(),
            "supported_languages": await self.get_supported_languages()
        }