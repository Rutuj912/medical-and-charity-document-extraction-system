#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path
import fitz
import cv2
import numpy as np

backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.services.ocr_service import OCRService
from app.utils.file_utils import save_image, ensure_directory


def create_test_pdf_with_text(output_path: Path, text_content: str):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)

    text_rect = fitz.Rect(50, 50, 545, 792)
    page.insert_textbox(text_rect, text_content, fontsize=14, fontname="helv", align=0)

    doc.save(str(output_path))
    doc.close()
    return output_path


def create_test_image_with_text(output_path: Path, text: str):
    img = np.ones((400, 800, 3), dtype=np.uint8) * 255
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, text, (50, 200), font, 1.5, (0, 0, 0), 2)
    save_image(img, output_path)
    return output_path


async def test_service_initialization():
    print("\n" + "=" * 60)
    print("TEST 1: OCR Service Initialization")
    print("=" * 60)

    try:
        service = OCRService()

        print("\n1. Service Info:")
        info = service.get_service_info()
        print(f"   Default Engine: {info['default_engine']}")
        print(f"   Preprocessing: {info['preprocessing_enabled']}")
        print(f"   Default DPI: {info['default_dpi']}")

        print("\n2. Checking Available Engines:")
        engines = await service.get_available_engines()
        for engine, available in engines.items():
            status = "✓ Available" if available else "✗ Not Available"
            print(f"   {engine}: {status}")

        print("\n✓ Service Initialization: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_single_image_ocr():
    print("\n" + "=" * 60)
    print("TEST 2: Single Image OCR")
    print("=" * 60)

    try:
        service = OCRService()

        print("\n1. Creating Test Image:")
        test_image = Path("test_ocr_image.png")
        test_text = "Medical OCR System 2026"
        create_test_image_with_text(test_image, test_text)
        print(f"   ✓ Created: {test_image}")

        print("\n2. Processing Image (without preprocessing):")
        result = await service.process_single_image(
            test_image,
            engine="tesseract",
            language="eng",
            preprocess=False
        )

        print(f"   Detected Text: '{result['text'].strip()}'")
        print(f"   Confidence: {result['confidence']:.2f}%")
        print(f"   Word Count: {result['word_count']}")

        print("\n3. Processing Image (with preprocessing):")
        result_preprocessed = await service.process_single_image(
            test_image,
            engine="tesseract",
            language="eng",
            preprocess=True,
            document_type="general"
        )

        print(f"   Confidence: {result_preprocessed['confidence']:.2f}%")

        if test_image.exists():
            test_image.unlink()

        print("\n✓ Single Image OCR: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_text_based_pdf():
    print("\n" + "=" * 60)
    print("TEST 3: Text-Based PDF Processing")
    print("=" * 60)

    try:
        service = OCRService()

        print("\n1. Creating Text-Based PDF:")
        test_pdf = Path("test_text_pdf.pdf")
        text_content = "This is a text-based PDF document.\nMedical OCR System.\nDirect text extraction test."
        create_test_pdf_with_text(test_pdf, text_content)
        print(f"   ✓ Created: {test_pdf}")

        print("\n2. Processing PDF:")
        result = await service.process_pdf(
            test_pdf,
            engine="tesseract",
            language="eng",
            preprocess=False
        )

        print(f"   Is Scanned: {result['is_scanned']}")
        print(f"   Method: {result['processing_method']}")
        print(f"   Page Count: {result['page_count']}")
        print(f"   Total Characters: {result['total_characters']}")
        print(f"   Confidence: {result.get('confidence', result.get('average_confidence', 0))}%")

        print("\n3. Extracted Text Preview:")
        preview = result['text'][:150]
        print(f"   {preview}...")

        if test_pdf.exists():
            test_pdf.unlink()

        print("\n✓ Text-Based PDF: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_images():
    print("\n" + "=" * 60)
    print("TEST 4: Multiple Images Processing")
    print("=" * 60)

    try:
        service = OCRService()

        print("\n1. Creating Multiple Test Images:")
        image_paths = []
        texts = ["Page 1 Content", "Page 2 Data", "Page 3 Info"]

        for i, text in enumerate(texts, 1):
            img_path = Path(f"test_multi_{i}.png")
            create_test_image_with_text(img_path, text)
            image_paths.append(img_path)
            print(f"   ✓ Created: {img_path}")

        print("\n2. Processing Images (sequential):")
        results = await service.process_images(
            image_paths,
            engine="tesseract",
            language="eng",
            parallel=False
        )

        print(f"   Processed: {len(results)} images")
        for i, result in enumerate(results, 1):
            print(f"   Image {i}: {result['word_count']} words, {result['confidence']:.1f}% confidence")

        print("\n3. Processing Images (parallel):")
        results_parallel = await service.process_images(
            image_paths,
            engine="tesseract",
            language="eng",
            parallel=True
        )

        print(f"   Processed: {len(results_parallel)} images (parallel)")

        for img_path in image_paths:
            if img_path.exists():
                img_path.unlink()

        print("\n✓ Multiple Images: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pdf_batch_processing():
    print("\n" + "=" * 60)
    print("TEST 5: PDF Batch Processing")
    print("=" * 60)

    try:
        service = OCRService()

        print("\n1. Creating Multiple PDFs:")
        pdf_paths = []
        for i in range(3):
            pdf_path = Path(f"test_batch_{i+1}.pdf")
            create_test_pdf_with_text(pdf_path, f"Document {i+1}\nTest Content")
            pdf_paths.append(pdf_path)
            print(f"   ✓ Created: {pdf_path}")

        print("\n2. Processing PDFs (with merge):")
        result = await service.process_pdf_batch(
            pdf_paths,
            merge_pdfs=True,
            preprocess=False
        )

        if 'documents' in result:
            print(f"   Batch Size: {result['batch_size']}")
            print(f"   Total Pages: {result['total_pages']}")
        else:
            print(f"   Pages: {result['page_count']}")
            print(f"   Characters: {result['total_characters']}")

        for pdf_path in pdf_paths:
            if pdf_path.exists():
                pdf_path.unlink()

        print("\n✓ PDF Batch Processing: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_pipeline():
    print("\n" + "=" * 60)
    print("TEST 6: Complete OCR Pipeline")
    print("=" * 60)

    try:
        service = OCRService()

        print("\n1. Creating Test Image:")
        test_image = Path("test_pipeline.png")
        create_test_image_with_text(test_image, "Complete Pipeline Test - Medical Records 2026")

        print("\n2. Running Complete Pipeline:")
        print("   - Image preprocessing")
        print("   - OCR execution")
        print("   - Result formatting")

        result = await service.process_single_image(
            test_image,
            engine="tesseract",
            preprocess=True,
            document_type="general"
        )

        print(f"\n3. Pipeline Results:")
        print(f"   Text Length: {len(result['text'])} chars")
        print(f"   Confidence: {result['confidence']:.2f}%")
        print(f"   Words Detected: {result['word_count']}")
        print(f"   Engine: {result.get('engine', 'unknown')}")

        if test_image.exists():
            test_image.unlink()

        print("\n✓ Complete Pipeline: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_engine_validation():
    print("\n" + "=" * 60)
    print("TEST 7: Engine Validation")
    print("=" * 60)

    try:
        service = OCRService()

        print("\n1. Validating Engines:")
        engines_to_test = ["tesseract", "easyocr", "paddle"]

        for engine in engines_to_test:
            is_available = await service.validate_ocr_engine(engine)
            status = "✓ Available" if is_available else "✗ Not Available"
            print(f"   {engine}: {status}")

        print("\n✓ Engine Validation: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "OCR SERVICE INTEGRATION TEST" + " " * 18 + "║")
    print("╚" + "=" * 58 + "╝")

    tests = [
        ("Service Initialization", test_service_initialization),
        ("Single Image OCR", test_single_image_ocr),
        ("Text-Based PDF", test_text_based_pdf),
        ("Multiple Images", test_multiple_images),
        ("PDF Batch Processing", test_pdf_batch_processing),
        ("Complete Pipeline", test_complete_pipeline),
        ("Engine Validation", test_engine_validation),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  Tests interrupted by user")
            break
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
        print("\n🎉 All OCR integration tests passed!")
        print("\n✓ Service Initialization: Working")
        print("✓ Single Image OCR: Working")
        print("✓ Text-Based PDF: Working")
        print("✓ Multiple Images: Working")
        print("✓ PDF Batch: Working")
        print("✓ Complete Pipeline: Working")
        print("✓ Engine Validation: Working")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)