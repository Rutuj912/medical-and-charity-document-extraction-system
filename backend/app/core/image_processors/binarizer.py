import cv2
import numpy as np
from typing import Optional, Tuple

from backend.app.config import get_logger

logger = get_logger(__name__)


class ImageBinarizer:
    def __init__(self):
        self.logger = logger

    def binarize(
        self,
        image: np.ndarray,
        method: str = "auto"
    ) -> np.ndarray:
        self.logger.debug(f"Binarizing image with method: {method}")


        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        if method == "auto":
            return self._auto_binarize(gray)
        elif method == "otsu":
            return self.otsu_binarize(gray)
        elif method == "adaptive":
            return self.adaptive_binarize(gray)
        elif method == "sauvola":
            return self.sauvola_binarize(gray)
        elif method == "niblack":
            return self.niblack_binarize(gray)
        elif method == "triangle":
            return self.triangle_binarize(gray)
        else:
            self.logger.warning(f"Unknown method: {method}, using auto")
            return self._auto_binarize(gray)

    def _auto_binarize(self, image: np.ndarray) -> np.ndarray:
        mean_intensity = np.mean(image)
        std_intensity = np.std(image)

        self.logger.debug(
            f"Image stats - Mean: {mean_intensity:.2f}, Std: {std_intensity:.2f}"
        )


        if std_intensity > 50:
            self.logger.debug("High contrast detected, using Otsu")
            return self.otsu_binarize(image)

        elif std_intensity < 30:
            self.logger.debug("Low contrast detected, using adaptive")
            return self.adaptive_binarize(image)

        else:
            self.logger.debug("Medium contrast detected, using Sauvola")
            return self.sauvola_binarize(image)

    def otsu_binarize(
        self,
        image: np.ndarray,
        invert: bool = False
    ) -> np.ndarray:
        threshold_value, binary = cv2.threshold(
            image,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        if invert:
            binary = cv2.bitwise_not(binary)

        self.logger.debug(
            f"Otsu binarization - threshold: {threshold_value:.2f}"
        )

        return binary

    def adaptive_binarize(
        self,
        image: np.ndarray,
        block_size: int = 11,
        c: int = 2,
        method: str = "gaussian"
    ) -> np.ndarray:
        if block_size % 2 == 0:
            block_size += 1


        if method == "gaussian":
            adaptive_method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
        else:
            adaptive_method = cv2.ADAPTIVE_THRESH_MEAN_C


        binary = cv2.adaptiveThreshold(
            image,
            255,
            adaptive_method,
            cv2.THRESH_BINARY,
            block_size,
            c
        )

        self.logger.debug(
            f"Adaptive binarization - block_size: {block_size}, "
            f"c: {c}, method: {method}"
        )

        return binary

    def sauvola_binarize(
        self,
        image: np.ndarray,
        window_size: int = 15,
        k: float = 0.2,
        r: float = 128.0
    ) -> np.ndarray:
        if window_size % 2 == 0:
            window_size += 1


        mean = cv2.boxFilter(
            image.astype(float),
            -1,
            (window_size, window_size),
            normalize=True
        )

        mean_sq = cv2.boxFilter(
            (image.astype(float) ** 2),
            -1,
            (window_size, window_size),
            normalize=True
        )

        std = np.sqrt(mean_sq - mean ** 2)


        threshold = mean * (1 + k * ((std / r) - 1))


        binary = np.where(image > threshold, 255, 0).astype(np.uint8)

        self.logger.debug(
            f"Sauvola binarization - window: {window_size}, k: {k}, r: {r}"
        )

        return binary

    def niblack_binarize(
        self,
        image: np.ndarray,
        window_size: int = 15,
        k: float = -0.2
    ) -> np.ndarray:
        if window_size % 2 == 0:
            window_size += 1


        mean = cv2.boxFilter(
            image.astype(float),
            -1,
            (window_size, window_size),
            normalize=True
        )

        mean_sq = cv2.boxFilter(
            (image.astype(float) ** 2),
            -1,
            (window_size, window_size),
            normalize=True
        )

        std = np.sqrt(mean_sq - mean ** 2)


        threshold = mean + k * std


        binary = np.where(image > threshold, 255, 0).astype(np.uint8)

        self.logger.debug(
            f"Niblack binarization - window: {window_size}, k: {k}"
        )

        return binary

    def triangle_binarize(self, image: np.ndarray) -> np.ndarray:
        threshold_value, binary = cv2.threshold(
            image,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_TRIANGLE
        )

        self.logger.debug(
            f"Triangle binarization - threshold: {threshold_value:.2f}"
        )

        return binary

    def multi_scale_binarize(
        self,
        image: np.ndarray,
        scales: list = [11, 21, 31]
    ) -> np.ndarray:
        results = []

        for scale in scales:
            binary = self.adaptive_binarize(image, block_size=scale)
            results.append(binary)


        combined = np.median(results, axis=0).astype(np.uint8)

        self.logger.debug(
            f"Multi-scale binarization - scales: {scales}"
        )

        return combined

    def clean_binary_image(
        self,
        binary: np.ndarray,
        remove_small_objects: int = 20
    ) -> np.ndarray:
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            binary,
            connectivity=8
        )


        cleaned = np.zeros_like(binary)


        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= remove_small_objects:
                cleaned[labels == i] = 255

        self.logger.debug(
            f"Cleaned binary image - removed objects < {remove_small_objects} pixels"
        )

        return cleaned
