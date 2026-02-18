from typing import Optional, Dict, Any
from pathlib import Path
import numpy as np

from backend.app.config import get_logger, settings
from backend.app.utils.exceptions import ImageProcessingError
from backend.app.utils.file_utils import load_image, save_image
from backend.app.core.image_processors.enhancer import ImageEnhancer
from backend.app.core.image_processors.denoiser import ImageDenoiser
from backend.app.core.image_processors.deskewer import ImageDeskewer
from backend.app.core.image_processors.binarizer import ImageBinarizer

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
            f"Preprocessing service initialized | dpi={self.dpi} | enabled={self.enable_preprocessing}"
        )

    async def preprocess_image(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
        **options
    ) -> Path:

        if not self.enable_preprocessing:
            self.logger.info("Preprocessing disabled, returning original image")
            return image_path

        try:
            self.logger.info(
                f"Starting image preprocessing | input={image_path} | options={options}"
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
                f"Image preprocessing completed | output={output_path} | metadata={metadata}"
            )

            return output_path

        except Exception as e:
            self.logger.error(
                f"Image preprocessing failed | input={image_path} | error={e}",
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
            self.logger.debug(f"Enhancement: {enhancement_method}")
            processed = self.enhancer.enhance(processed, method=enhancement_method)
            metadata['steps_applied'].append(f'enhance_{enhancement_method}')

        if do_denoise:
            self.logger.debug(f"Denoising: {denoise_method}")
            processed = self.denoiser.denoise(processed, method=denoise_method)
            metadata['steps_applied'].append(f'denoise_{denoise_method}')

        if do_deskew:
            self.logger.debug(f"Deskewing: {deskew_method}")
            processed, angle = self.deskewer.deskew(processed, method=deskew_method)
            metadata['skew_angle'] = angle
            metadata['steps_applied'].append(f'deskew_{deskew_method}')

        if do_binarize:
            self.logger.debug(f"Binarization: {binarize_method}")
            processed = self.binarizer.binarize(processed, method=binarize_method)
            metadata['steps_applied'].append(f'binarize_{binarize_method}')

        metadata['final_shape'] = processed.shape

        self.logger.debug(
            f"Preprocessing completed | steps={metadata['steps_applied']}"
        )

        return processed, metadata

    async def preprocess_for_ocr(
        self,
        image_path: Path,
        document_type: str = "general"
    ) -> Path:

        self.logger.info(f"Preprocessing for OCR | type={document_type}")

        presets = {
            "general": {
                "enhance": True,
                "denoise": True,
                "deskew": True,
                "binarize": True
            }
        }

        options = presets.get(document_type, presets["general"])
        return await self.preprocess_image(image_path, **options)
