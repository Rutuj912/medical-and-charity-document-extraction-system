from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import numpy as np

from app.config import get_logger

logger = get_logger(__name__)


class BaseOCREngine(ABC):
    def __init__(self, language: str = "eng", **kwargs):
        self.language = language
        self.config = kwargs
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    async def initialize(self) -> bool:
        pass

    @abstractmethod
    async def process_image(
        self,
        image: np.ndarray,
        **kwargs
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def process_image_file(
        self,
        image_path: Path,
        **kwargs
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        pass

    @abstractmethod
    def get_engine_info(self) -> Dict[str, Any]:
        pass

    async def is_available(self) -> bool:
        try:
            await self.initialize()
            return True
        except Exception as e:
            self.logger.error(f"Engine not available: {e}")
            return False

    def format_output(
        self,
        text: str,
        confidence: float,
        word_results: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "text": text,
            "confidence": confidence,
            "word_count": len(text.split()) if text else 0,
            "character_count": len(text) if text else 0,
            "words": word_results or [],
            "engine": self.__class__.__name__,
            "language": self.language,
            "metadata": kwargs
        }
