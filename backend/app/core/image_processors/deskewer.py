import cv2
import numpy as np
from typing import Tuple, Optional

from app.config import get_logger

logger = get_logger(__name__)


class ImageDeskewer:
    def __init__(self):
        self.logger = logger

    def deskew(
        self,
        image: np.ndarray,
        method: str = "auto"
    ) -> Tuple[np.ndarray, float]:
        self.logger.debug(f"Deskewing image with method: {method}")

        if method == "auto":
            return self._auto_deskew(image)
        elif method == "hough":
            angle = self.detect_skew_hough(image)
        elif method == "projection":
            angle = self.detect_skew_projection(image)
        elif method == "contour":
            angle = self.detect_skew_contour(image)
        else:
            self.logger.warning(f"Unknown method: {method}, using auto")
            return self._auto_deskew(image)


        deskewed = self.rotate_image(image, angle)

        return deskewed, angle

    def _auto_deskew(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        try:
            angle = self.detect_skew_hough(image)


            if abs(angle) < 45:
                self.logger.debug(f"Using Hough method, angle: {angle:.2f}°")
                deskewed = self.rotate_image(image, angle)
                return deskewed, angle
        except:
            pass


        try:
            angle = self.detect_skew_projection(image)
            self.logger.debug(f"Using projection method, angle: {angle:.2f}°")
            deskewed = self.rotate_image(image, angle)
            return deskewed, angle
        except:
            pass


        self.logger.warning("Could not detect skew, returning original")
        return image, 0.0

    def detect_skew_hough(
        self,
        image: np.ndarray,
        angle_range: float = 45.0
    ) -> float:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()


        edges = cv2.Canny(gray, 50, 150, apertureSize=3)


        lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)

        if lines is None:
            return 0.0


        angles = []
        for rho, theta in lines[:, 0]:
            angle = np.degrees(theta) - 90


            if abs(angle) < angle_range:
                angles.append(angle)

        if not angles:
            return 0.0


        median_angle = np.median(angles)

        self.logger.debug(
            f"Hough detection - found {len(angles)} lines, "
            f"median angle: {median_angle:.2f}°"
        )

        return median_angle

    def detect_skew_projection(
        self,
        image: np.ndarray,
        angle_range: float = 45.0,
        angle_step: float = 0.5
    ) -> float:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()


        _, binary = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        best_angle = 0.0
        max_variance = 0.0


        angles = np.arange(-angle_range, angle_range, angle_step)

        for angle in angles:

            rotated = self.rotate_image(binary, angle)


            projection = np.sum(rotated, axis=1)


            variance = np.var(projection)

            if variance > max_variance:
                max_variance = variance
                best_angle = angle

        self.logger.debug(
            f"Projection detection - best angle: {best_angle:.2f}°, "
            f"variance: {max_variance:.2f}"
        )

        return best_angle

    def detect_skew_contour(
        self,
        image: np.ndarray
    ) -> float:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()


        _, binary = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )


        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return 0.0


        largest_contour = max(contours, key=cv2.contourArea)


        rect = cv2.minAreaRect(largest_contour)
        angle = rect[2]


        if angle < -45:
            angle = 90 + angle
        elif angle > 45:
            angle = angle - 90

        self.logger.debug(f"Contour detection - angle: {angle:.2f}°")

        return -angle

    def rotate_image(
        self,
        image: np.ndarray,
        angle: float,
        background_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> np.ndarray:
        if abs(angle) < 0.1:

            return image


        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)


        M = cv2.getRotationMatrix2D(center, angle, 1.0)


        cos = np.abs(M[0, 0])
        sin = np.abs(M[0, 1])

        new_w = int((h * sin) + (w * cos))
        new_h = int((h * cos) + (w * sin))


        M[0, 2] += (new_w / 2) - center[0]
        M[1, 2] += (new_h / 2) - center[1]


        rotated = cv2.warpAffine(
            image,
            M,
            (new_w, new_h),
            borderValue=background_color
        )

        self.logger.debug(
            f"Rotated image by {angle:.2f}° - "
            f"old size: {(w, h)}, new size: {(new_w, new_h)}"
        )

        return rotated

    def check_if_skewed(
        self,
        image: np.ndarray,
        threshold: float = 2.0
    ) -> bool:
        angle = self.detect_skew_hough(image)

        is_skewed = abs(angle) > threshold

        self.logger.debug(
            f"Skew check - angle: {angle:.2f}°, "
            f"threshold: {threshold}°, skewed: {is_skewed}"
        )

        return is_skewed
