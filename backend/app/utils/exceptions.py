from typing import Optional, Any, Dict


class OCRSystemException(Exception):
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }






class FileException(OCRSystemException):
    pass


class FileNotFoundError(FileException):
    pass


class InvalidFileTypeError(FileException):
    pass


class FileSizeExceededError(FileException):
    pass


class FileUploadError(FileException):
    pass


class FileReadError(FileException):
    pass


class FileWriteError(FileException):
    pass






class PDFException(OCRSystemException):
    pass


class PDFMergeError(PDFException):
    pass


class PDFCorruptedError(PDFException):
    pass


class PDFPasswordProtectedError(PDFException):
    pass


class PDFConversionError(PDFException):
    pass


class PDFEmptyError(PDFException):
    pass






class ImageException(OCRSystemException):
    pass


class ImageLoadError(ImageException):
    pass


class ImageProcessingError(ImageException):
    pass


class ImageQualityError(ImageException):
    pass


class ImageFormatError(ImageException):
    pass






class OCRException(OCRSystemException):
    pass


class OCREngineNotFoundError(OCRException):
    pass


class OCRProcessingError(OCRException):
    pass


class OCRNoTextFoundError(OCRException):
    pass


class OCRLowConfidenceError(OCRException):
    pass


class OCRTimeoutError(OCRException):
    pass


class OCRLanguageNotSupportedError(OCRException):
    pass






class TaskException(OCRSystemException):
    pass


class TaskNotFoundError(TaskException):
    pass


class TaskCreationError(TaskException):
    pass


class TaskStorageError(TaskException):
    pass


class TaskLimitExceededError(TaskException):
    pass






class ValidationException(OCRSystemException):
    pass


class JSONValidationError(ValidationException):
    pass


class SchemaValidationError(ValidationException):
    pass


class InputValidationError(ValidationException):
    pass






class ConfigurationException(OCRSystemException):
    pass


class MissingConfigurationError(ConfigurationException):
    pass


class InvalidConfigurationError(ConfigurationException):
    pass






class DatabaseException(OCRSystemException):
    pass


class DatabaseConnectionError(DatabaseException):
    pass


class DatabaseQueryError(DatabaseException):
    pass






class APIException(OCRSystemException):
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, details)
        self.status_code = status_code


class BadRequestError(APIException):
    def __init__(self, message: str = "Bad Request", **kwargs):
        super().__init__(message, status_code=400, **kwargs)


class UnauthorizedError(APIException):
    def __init__(self, message: str = "Unauthorized", **kwargs):
        super().__init__(message, status_code=401, **kwargs)


class ForbiddenError(APIException):
    def __init__(self, message: str = "Forbidden", **kwargs):
        super().__init__(message, status_code=403, **kwargs)


class NotFoundError(APIException):
    def __init__(self, message: str = "Resource Not Found", **kwargs):
        super().__init__(message, status_code=404, **kwargs)


class ConflictError(APIException):
    def __init__(self, message: str = "Conflict", **kwargs):
        super().__init__(message, status_code=409, **kwargs)


class InternalServerError(APIException):
    def __init__(self, message: str = "Internal Server Error", **kwargs):
        super().__init__(message, status_code=500, **kwargs)


class ServiceUnavailableError(APIException):
    def __init__(self, message: str = "Service Unavailable", **kwargs):
        super().__init__(message, status_code=503, **kwargs)






def handle_exception(exc: Exception) -> Dict[str, Any]:
    if isinstance(exc, OCRSystemException):
        return exc.to_dict()


    return {
        "error": exc.__class__.__name__,
        "message": str(exc),
        "details": {}
    }


if __name__ == "__main__":
    print("Testing Custom Exceptions")
    print("=" * 60)


    try:
        raise InvalidFileTypeError(
            message="Only PDF files are allowed",
            details={"file_type": "docx", "allowed_types": ["pdf"]}
        )
    except InvalidFileTypeError as e:
        print(f"✓ File Exception: {e.message}")
        print(f"  Error Code: {e.error_code}")
        print(f"  Details: {e.details}")

    print("\n" + "=" * 60)


    try:
        raise OCRProcessingError(
            message="OCR engine failed to process image",
            details={"engine": "tesseract", "page": 5}
        )
    except OCRProcessingError as e:
        print(f"✓ OCR Exception: {e.message}")
        print(f"  Dict: {e.to_dict()}")

    print("\n" + "=" * 60)


    try:
        raise BadRequestError(
            message="Invalid request parameters",
            details={"missing_field": "file"}
        )
    except BadRequestError as e:
        print(f"✓ API Exception: {e.message}")
        print(f"  Status Code: {e.status_code}")
        print(f"  Dict: {e.to_dict()}")

    print("\n" + "=" * 60)
    print("✓ All exception tests passed!")
