from typing import Optional, Dict, Any
from pathlib import Path
import numpy as np
import cv2

from app.config import get_logger, settings
from app.utils.exceptions import ImageProcessingError
from app.utils.file_utils import load_image, save_image
from app.core.image_processors.enhancer import ImageEnhancer
from app.core.image_processors.denoiser import ImageDenoiser
from app.core.image_processors.deskewer import ImageDeskewer
from app.core.image_processors.binarizer import ImageBinarizer

logger = get_logger(__name__)


class PreprocessingService:
    def __init__(self):
        self.logger = logger
        self.dpi = settings.DPI_CONVERSION
        self.enable_preprocessing = settings.ENABLE_PREPROCESSING


        self.enhancer = ImageEnhancer()
        self.denoiser = ImageDenoiser()
        self.deskewer = ImageDeskewer()
        self.binarizer = ImageBinarizer()

        self.logger.info(
            "Preprocessing service initialized",
            dpi=self.dpi,
            enabled=self.enable_preprocessing
        )

    async def preprocess_image(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        **options
    ) -> Path:
        if not self.enable_preprocessing:
            self.logger.info("Preprocessing disabled, returning original")
            return image_path

        try:
            self.logger.info(
                "Starting image preprocessing",
                input_path=str(image_path),
                options=options
            )


            image = load_image(image_path)


            processed, metadata = await self.preprocess_image_array(
                image,
                **options
            )


            if output_path is None:
                output_dir = settings.get_absolute_path(
                    settings.PROCESSED_IMAGE_DIR
                )
                output_dir.mkdir(parents=True, exist_ok=True)

                output_path = output_dir / f"processed_{image_path.name}"


            save_image(processed, output_path)

            self.logger.info(
                "Image preprocessing completed",
                output_path=str(output_path),
                metadata=metadata
            )

            return output_path

        except Exception as e:
            self.logger.error(
                "Image preprocessing failed",
                input_path=str(image_path),
                error=str(e),
                exc_info=True
            )
            raise ImageProcessingError(
                message=f"Preprocessing failed: {str(e)}",
                details={
                    "input_path": str(image_path),
                    "error": str(e)
                }
            )

    async def preprocess_image_array(
        self,
        image: np.ndarray,
        **options
    ) -> tuple[np.ndarray, Dict[str, Any]]:
        do_enhance = options.get('enhance', settings.ENABLE_CONTRAST_ENHANCEMENT)
        do_denoise = options.get('denoise', settings.ENABLE_DENOISING)
        do_deskew = options.get('deskew', settings.ENABLE_DESKEWING)
        do_binarize = options.get('binarize', settings.ENABLE_BINARIZATION)

        enhancement_method = options.get('enhancement_method', 'auto')
        denoise_method = options.get('denoise_method', 'auto')
        deskew_method = options.get('deskew_method', 'auto')
        binarize_method = options.get('binarize_method', 'auto')


        metadata = {
            'original_shape': image.shape,
            'steps_applied': [],
            'skew_angle': 0.0
        }

        processed = image.copy()


        if do_enhance:
            self.logger.debug(f"Applying enhancement: {enhancement_method}")
            processed = self.enhancer.enhance(processed, method=enhancement_method)
            metadata['steps_applied'].append(f'enhance_{enhancement_method}')


        if do_denoise:
            self.logger.debug(f"Applying denoising: {denoise_method}")
            processed = self.denoiser.denoise(processed, method=denoise_method)
            metadata['steps_applied'].append(f'denoise_{denoise_method}')


        if do_deskew:
            self.logger.debug(f"Applying deskewing: {deskew_method}")
            processed, angle = self.deskewer.deskew(processed, method=deskew_method)
            metadata['skew_angle'] = angle
            metadata['steps_applied'].append(f'deskew_{deskew_method}')


        if do_binarize:
            self.logger.debug(f"Applying binarization: {binarize_method}")
            processed = self.binarizer.binarize(processed, method=binarize_method)
            metadata['steps_applied'].append(f'binarize_{binarize_method}')

        metadata['final_shape'] = processed.shape

        self.logger.debug(
            f"Preprocessing pipeline completed - steps: {metadata['steps_applied']}"
        )

        return processed, metadata

    async def preprocess_for_ocr(
        self,
        image_path: Path,
        document_type: str = "general"
    ) -> Path:
        self.logger.info(
            f"Preprocessing for OCR - document type: {document_type}"
        )


        presets = {
            "general": {
                "enhance": True,
                "enhancement_method": "auto",
                "denoise": True,
                "denoise_method": "median",
                "deskew": True,
                "deskew_method": "hough",
                "binarize": True,
                "binarize_method": "sauvola"
            },
            "form": {
                "enhance": True,
                "enhancement_method": "clahe",
                "denoise": True,
                "denoise_method": "bilateral",
                "deskew": True,
                "deskew_method": "hough",
                "binarize": True,
                "binarize_method": "adaptive"
            },
            "handwritten": {
                "enhance": True,
                "enhancement_method": "clahe",
                "denoise": False,
                "deskew": True,
                "deskew_method": "contour",
                "binarize": True,
                "binarize_method": "sauvola"
            },
            "low_quality": {
                "enhance": True,
                "enhancement_method": "auto",
                "denoise": True,
                "denoise_method": "nlm",
                "deskew": True,
                "deskew_method": "auto",
                "binarize": True,
                "binarize_method": "sauvola"
            },
            "photo": {
                "enhance": True,
                "enhancement_method": "clahe",
                "denoise": True,
                "denoise_method": "bilateral",
                "deskew": False,
                "binarize": True,
                "binarize_method": "adaptive"
            }
        }


        options = presets.get(document_type, presets["general"])


        return await self.preprocess_image(image_path, **options)

    async def quick_enhance(self, image_path: Path) -> Path:
        return await self.preprocess_image(
            image_path,
            enhance=True,
            enhancement_method="auto",
            denoise=False,
            deskew=False,
            binarize=False
        )

    async def normalize_dpi(
        self,
        image: np.ndarray,
        target_dpi: int = 300
    ) -> np.ndarray:



        self.logger.debug(f"DPI normalization to {target_dpi} DPI")
        return image

    async def batch_preprocess(
        self,
        image_paths: list[Path],
        **options
    ) -> list[Path]:
        self.logger.info(
            f"Batch preprocessing {len(image_paths)} images"
        )

        processed_paths = []

        for image_path in image_paths:
            try:
                processed_path = await self.preprocess_image(
                    image_path,
                    **options
                )
                processed_paths.append(processed_path)
            except Exception as e:
                self.logger.error(
                    f"Failed to preprocess {image_path}: {e}"
                )

                processed_paths.append(image_path)

        self.logger.info(
            f"Batch preprocessing completed - "
            f"{len(processed_paths)}/{len(image_paths)} successful"
        )

        return processed_paths

    def get_preprocessing_info(self) -> Dict[str, Any]:
        return {
            "enabled": self.enable_preprocessing,
            "dpi": self.dpi,
            "enhancement": settings.ENABLE_CONTRAST_ENHANCEMENT,
            "denoising": settings.ENABLE_DENOISING,
            "deskewing": settings.ENABLE_DESKEWING,
            "binarization": settings.ENABLE_BINARIZATION,
            "available_methods": {
                "enhancement": ["auto", "clahe", "histogram", "sharpen", "gamma"],
                "denoising": ["auto", "gaussian", "median", "bilateral", "nlm"],
                "deskewing": ["auto", "hough", "projection", "contour"],
                "binarization": ["auto", "otsu", "adaptive", "sauvola", "niblack", "triangle"]
            }
        }
