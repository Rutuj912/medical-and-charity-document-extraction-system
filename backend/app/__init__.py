__version__ = "1.0.0"
__author__ = "Medical OCR Team"
__description__ = "Advanced OCR system for medical and charity documents"

from .config import settings, get_logger


logger = get_logger(__name__)


logger.info(
    f"Initializing {settings.APP_NAME} v{__version__} | "
    f"Environment: {settings.ENVIRONMENT} | "
    f"Debug: {settings.DEBUG}"
)
