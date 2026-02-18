import cv2
import numpy as np
from typing import Tuple

from backend.app.config import get_logger

logger = get_logger(__name__)


class ImageDenoiser:
    def __init__(self):
        self.logger = logger

    def denoise(
        self,
        image: np.ndarray,
        method: str = "auto"
    ) -> np.ndarray:
        self.logger.debug(f"Denoising image with method: {method}")

        if method == "auto":
            return self._auto_denoise(image)
        elif method == "gaussian":
            return self.gaussian_denoise(image)
        elif method == "median":
            return self.median_denoise(image)
        elif method == "bilateral":
            return self.bilateral_denoise(image)
        elif method == "nlm":
            return self.nlm_denoise(image)
        elif method == "morphology":
            return self.morphological_denoise(image)
        else:
            self.logger.warning(f"Unknown method: {method}, using auto")
            return self._auto_denoise(image)

    def _auto_denoise(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()


        noise_level = self._estimate_noise(gray)

        self.logger.debug(f"Estimated noise level: {noise_level:.2f}")


        if noise_level > 15:
            self.logger.debug("High noise detected, using bilateral filter")
            return self.bilateral_denoise(image)
        elif noise_level > 8:
            self.logger.debug("Medium noise detected, using median filter")
            return self.median_denoise(image)
        else:
            self.logger.debug("Low noise detected, using light gaussian")
            return self.gaussian_denoise(image, kernel_size=3)

    def _estimate_noise(self, image: np.ndarray) -> float:
        laplacian = cv2.Laplacian(image, cv2.CV_64F)


        noise = laplacian.var()

        return noise

    def gaussian_denoise(
        self,
        image: np.ndarray,
        kernel_size: int = 5,
        sigma: float = 0
    ) -> np.ndarray:
        if kernel_size % 2 == 0:
            kernel_size += 1

        denoised = cv2.GaussianBlur(
            image,
            (kernel_size, kernel_size),
            sigma
        )

        self.logger.debug(
            f"Applied Gaussian denoise - kernel: {kernel_size}, sigma: {sigma}"
        )

        return denoised

    def median_denoise(
        self,
        image: np.ndarray,
        kernel_size: int = 5
    ) -> np.ndarray:
        if kernel_size % 2 == 0:
            kernel_size += 1

        denoised = cv2.medianBlur(image, kernel_size)

        self.logger.debug(f"Applied median denoise - kernel: {kernel_size}")

        return denoised

    def bilateral_denoise(
        self,
        image: np.ndarray,
        d: int = 9,
        sigma_color: float = 75,
        sigma_space: float = 75
    ) -> np.ndarray:
        denoised = cv2.bilateralFilter(
            image,
            d,
            sigma_color,
            sigma_space
        )

        self.logger.debug(
            f"Applied bilateral denoise - d: {d}, "
            f"sigma_color: {sigma_color}, sigma_space: {sigma_space}"
        )

        return denoised

    def nlm_denoise(
        self,
        image: np.ndarray,
        h: float = 10,
        template_size: int = 7,
        search_size: int = 21
    ) -> np.ndarray:
        if len(image.shape) == 2:

            denoised = cv2.fastNlMeansDenoising(
                image,
                None,
                h,
                template_size,
                search_size
            )
        else:

            denoised = cv2.fastNlMeansDenoisingColored(
                image,
                None,
                h,
                h,
                template_size,
                search_size
            )

        self.logger.debug(
            f"Applied NLM denoise - h: {h}, "
            f"template: {template_size}, search: {search_size}"
        )

        return denoised

    def morphological_denoise(
        self,
        image: np.ndarray,
        kernel_size: int = 3
    ) -> np.ndarray:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT,
            (kernel_size, kernel_size)
        )



        opened = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)



        denoised = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

        self.logger.debug(
            f"Applied morphological denoise - kernel: {kernel_size}"
        )

        return denoised

    def remove_salt_pepper(
        self,
        image: np.ndarray,
        kernel_size: int = 5
    ) -> np.ndarray:
        denoised = cv2.medianBlur(image, kernel_size)

        self.logger.debug("Removed salt-and-pepper noise")

        return denoised

    def adaptive_denoise(
        self,
        image: np.ndarray
    ) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            is_color = True
        else:
            gray = image.copy()
            is_color = False


        block_size = 64
        h, w = gray.shape

        denoised = gray.copy()


        for i in range(0, h, block_size):
            for j in range(0, w, block_size):
                block = gray[i:i+block_size, j:j+block_size]

                if block.size == 0:
                    continue


                noise = self._estimate_noise(block)


                if noise > 15:
                    denoised_block = cv2.bilateralFilter(block, 5, 50, 50)
                elif noise > 8:
                    denoised_block = cv2.medianBlur(block, 3)
                else:
                    denoised_block = cv2.GaussianBlur(block, (3, 3), 0)

                denoised[i:i+block_size, j:j+block_size] = denoised_block


        if is_color:
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

        self.logger.debug("Applied adaptive denoising")

        return denoised
