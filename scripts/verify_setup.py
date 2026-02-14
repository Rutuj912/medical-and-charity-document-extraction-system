import sys
from pathlib import Path


backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

def test_imports():
    print("=" * 60)
    print("Testing Module Imports")
    print("=" * 60)

    try:
        from app.config import settings
        print("✓ Settings imported successfully")

        from app.config import get_logger, log_info
        print("✓ Logging imported successfully")

        from app.utils import exceptions
        print("✓ Exceptions imported successfully")

        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_configuration():
    print("\n" + "=" * 60)
    print("Testing Configuration")
    print("=" * 60)

    try:
        from app.config import settings

        print(f"✓ App Name: {settings.APP_NAME}")
        print(f"✓ Version: {settings.APP_VERSION}")
        print(f"✓ Environment: {settings.ENVIRONMENT}")
        print(f"✓ OCR Engine: {settings.DEFAULT_OCR_ENGINE}")
        print(f"✓ DPI: {settings.DPI_CONVERSION}")

        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_logging():
    print("\n" + "=" * 60)
    print("Testing Logging System")
    print("=" * 60)

    try:
        from app.config import get_logger, log_info, log_error

        logger = get_logger("test")
        logger.info("Test log message")
        print("✓ Logger created successfully")

        log_info("Test info message", test_key="test_value")
        print("✓ Log info function works")

        log_error("Test error message", error_code="TEST001")
        print("✓ Log error function works")

        return True
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False


def test_exceptions():
    print("\n" + "=" * 60)
    print("Testing Exception System")
    print("=" * 60)

    try:
        from app.utils.exceptions import (
            InvalidFileTypeError,
            OCRProcessingError,
            BadRequestError
        )


        try:
            raise InvalidFileTypeError(
                message="Test file error",
                details={"file": "test.txt"}
            )
        except InvalidFileTypeError as e:
            print(f"✓ File exception works: {e.message}")


        try:
            raise OCRProcessingError(
                message="Test OCR error",
                details={"engine": "test"}
            )
        except OCRProcessingError as e:
            print(f"✓ OCR exception works: {e.message}")


        try:
            raise BadRequestError(
                message="Test API error"
            )
        except BadRequestError as e:
            print(f"✓ API exception works: {e.message} (Status: {e.status_code})")

        return True
    except Exception as e:
        print(f"✗ Exception test failed: {e}")
        return False


def test_storage_directories():
    print("\n" + "=" * 60)
    print("Testing Storage Directories")
    print("=" * 60)

    try:
        from app.config import settings

        directories = [
            settings.UPLOAD_DIR,
            settings.MERGED_PDF_DIR,
            settings.PROCESSED_IMAGE_DIR,
            settings.JSON_TASKS_DIR,
            settings.LOGS_DIR,
        ]

        for directory in directories:
            path = settings.get_absolute_path(directory)
            if path.exists():
                print(f"✓ {directory}: {path}")
            else:
                print(f"✗ {directory}: Not found")
                return False

        return True
    except Exception as e:
        print(f"✗ Storage test failed: {e}")
        return False


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "OCR SYSTEM VERIFICATION TEST" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
        ("Logging System", test_logging),
        ("Exception System", test_exceptions),
        ("Storage Directories", test_storage_directories),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))


    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<40} {status}")

    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! System is ready for development.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())