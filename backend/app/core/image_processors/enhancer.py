import cv2
import numpy as np
from typing import Tuple, Optional

from backend.app.config import get_logger

logger = get_logger(__name__)


class ImageEnhancer:
    def __init__(self):
        self.logger = logger

    def enhance(
        self,
        image: np.ndarray,
        method: str = "auto"
    ) -> np.ndarray:
        self.logger.debug(f"Enhancing image with method: {method}")

        if method == "auto":
            return self._auto_enhance(image)
        elif method == "clahe":
            return self.apply_clahe(image)
        elif method == "histogram":
            return self.histogram_equalization(image)
        elif method == "sharpen":
            return self.sharpen(image)
        elif method == "gamma":
            return self.gamma_correction(image)
        else:
            self.logger.warning(f"Unknown method: {method}, using auto")
            return self._auto_enhance(image)

    def _auto_enhance(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()


        mean_intensity = np.mean(gray)
        std_intensity = np.std(gray)

        self.logger.debug(
            f"Image stats - Mean: {mean_intensity:.2f}, Std: {std_intensity:.2f}"
        )


        if std_intensity < 40:
            self.logger.debug("Low contrast detected, applying CLAHE")
            enhanced = self.apply_clahe(image)

        elif mean_intensity < 100:
            self.logger.debug("Dark image detected, applying gamma correction")
            enhanced = self.gamma_correction(image, gamma=1.5)

        elif mean_intensity > 180:
            self.logger.debug("Bright image detected, applying gamma correction")
            enhanced = self.gamma_correction(image, gamma=0.7)

        else:
            self.logger.debug("Normal image, applying light CLAHE")
            enhanced = self.apply_clahe(image, clip_limit=2.0)

        return enhanced

    def apply_clahe(
        self,
        image: np.ndarray,
        clip_limit: float = 3.0,
        tile_size: Tuple[int, int] = (8, 8)
    ) -> np.ndarray:
        clahe = cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=tile_size
        )


        if len(image.shape) == 2:

            enhanced = clahe.apply(image)
        else:

            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        self.logger.debug(
            f"Applied CLAHE - clip_limit: {clip_limit}, tile_size: {tile_size}"
        )

        return enhanced

    def histogram_equalization(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 2:

            equalized = cv2.equalizeHist(image)
        else:

            yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
            yuv[:, :, 0] = cv2.equalizeHist(yuv[:, :, 0])
            equalized = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR)

        self.logger.debug("Applied histogram equalization")
        return equalized

    def sharpen(
        self,
        image: np.ndarray,
        strength: float = 1.0
    ) -> np.ndarray:
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ]) * strength


        sharpened = cv2.filter2D(image, -1, kernel)

        self.logger.debug(f"Applied sharpening - strength: {strength}")
        return sharpened

    def gamma_correction(
        self,
        image: np.ndarray,
        gamma: float = 1.0
    ) -> np.ndarray:
        inv_gamma = 1.0 / gamma
        table = np.array([
            ((i / 255.0) ** inv_gamma) * 255
            for i in np.arange(0, 256)
        ]).astype("uint8")


        corrected = cv2.LUT(image, table)

        self.logger.debug(f"Applied gamma correction - gamma: {gamma}")
        return corrected

    def adjust_brightness_contrast(
        self,
        image: np.ndarray,
        brightness: int = 0,
        contrast: int = 0
    ) -> np.ndarray:
        img = image.astype(float)


        if brightness != 0:
            img = img + brightness


        if contrast != 0:
            factor = (259 * (contrast + 255)) / (255 * (259 - contrast))
            img = factor * (img - 128) + 128


        img = np.clip(img, 0, 255).astype(np.uint8)

        self.logger.debug(
            f"Adjusted brightness: {brightness}, contrast: {contrast}"
        )

        return img

    def enhance_for_text(self, image: np.ndarray) -> np.ndarray:
        self.logger.debug("Applying text-specific enhancement")


        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()


        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)


        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]]) * 0.5
        enhanced = cv2.filter2D(enhanced, -1, kernel)

        return enhanced
