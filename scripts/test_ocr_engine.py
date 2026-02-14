#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path
import cv2
import numpy as np


backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.core.ocr_engines.engine_factory import OCREngineFactory
from app.core.ocr_engines.tesseract_engine import TesseractEngine
from app.utils.file_utils import save_image, load_image
from app.config import settings


def create_sample_image(text: str = "Hello OCR!", output_path: Path = None) -> Path:
    img = np.ones((200, 600, 3), dtype=np.uint8) * 255


    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.5
    color = (0, 0, 0)
    thickness = 2


    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]


    text_x = (img.shape[1] - text_size[0]) // 2
    text_y = (img.shape[0] + text_size[1]) // 2


    cv2.putText(img, text, (text_x, text_y), font, font_scale, color, thickness)


    if output_path is None:
        output_path = Path("sample_image.png")

    save_image(img, output_path)

    print(f"✓ Sample image created: {output_path}")
    return output_path


async def test_engine_factory():
    print("\n" + "=" * 60)
    print("TEST 1: OCR Engine Factory")
    print("=" * 60)


    print("\n1. Registered Engines:")
    engines = OCREngineFactory.list_engines()
    for engine in engines:
        print(f"   - {engine}")


    print("\n2. Engine Availability:")
    available = await OCREngineFactory.get_available_engines()
    for engine, status in available.items():
        status_icon = "✓" if status else "✗"
        status_text = "Available" if status else "Not Available"
        print(f"   {status_icon} {engine}: {status_text}")


    print("\n3. Creating Default Engine:")
    try:
        engine = OCREngineFactory.create_engine()
        info = engine.get_engine_info()
        print(f"   ✓ Engine Created: {info['name']}")
        print(f"   ✓ Version: {info.get('version', 'unknown')}")
        print(f"   ✓ Language: {info.get('language', 'unknown')}")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False


async def test_tesseract_basic():
    print("\n" + "=" * 60)
    print("TEST 2: Tesseract Basic OCR")
    print("=" * 60)

    try:

        print("\n1. Creating Tesseract Engine...")
        engine = TesseractEngine(language="eng")
        await engine.initialize()


        info = engine.get_engine_info()
        print(f"   ✓ Engine: {info['name']}")
        print(f"   ✓ Version: {info['version']}")
        print(f"   ✓ Initialized: {info['initialized']}")


        print("\n2. Supported Languages:")
        langs = engine.get_supported_languages()
        print(f"   Total: {len(langs)} languages")
        print(f"   Sample: {', '.join(langs[:10])}")

        return True

    except Exception as e:
        print(f"   ✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ocr_with_sample_image():
    print("\n" + "=" * 60)
    print("TEST 3: OCR Processing with Sample Image")
    print("=" * 60)

    try:

        print("\n1. Creating Sample Image...")
        sample_text = "Medical OCR System 2026"
        image_path = Path("test_sample.png")
        create_sample_image(sample_text, image_path)


        print("\n2. Initializing Tesseract...")
        engine = TesseractEngine(language="eng", psm=6)
        await engine.initialize()


        print("\n3. Processing Image...")
        result = await engine.process_image_file(image_path)


        print("\n4. OCR Results:")
        print(f"   Original Text: '{sample_text}'")
        print(f"   Detected Text: '{result['text']}'")
        print(f"   Confidence: {result['confidence']:.2f}%")
        print(f"   Word Count: {result['word_count']}")
        print(f"   Words Detected: {result['metadata']['word_count_detected']}")


        if result['words']:
            print("\n5. Word-Level Detection:")
            for i, word in enumerate(result['words'][:5], 1):
                print(f"   {i}. '{word['text']}' (confidence: {word['confidence']:.1f}%)")


        if image_path.exists():
            image_path.unlink()
            print(f"\n✓ Cleaned up test image: {image_path}")

        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_ocr_with_user_image():
    print("\n" + "=" * 60)
    print("TEST 4: OCR with User Image (Optional)")
    print("=" * 60)


    print("\nDo you have an image to test? (Enter path or press Enter to skip)")
    user_input = input("Image path: ").strip()

    if not user_input:
        print("Skipped - No image provided")
        return True

    try:
        image_path = Path(user_input)

        if not image_path.exists():
            print(f"✗ Image not found: {image_path}")
            return False


        print("\n1. Initializing Tesseract...")
        engine = TesseractEngine(language="eng")
        await engine.initialize()


        print("\n2. Processing Your Image...")
        result = await engine.process_image_file(image_path)


        print("\n3. OCR Results:")
        print(f"   Detected Text:\n")
        print("   " + "-" * 50)
        for line in result['text'].split('\n'):
            if line.strip():
                print(f"   {line}")
        print("   " + "-" * 50)
        print(f"\n   Confidence: {result['confidence']:.2f}%")
        print(f"   Total Words: {len(result['words'])}")
        print(f"   Total Characters: {result['character_count']}")

        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_different_psm_modes():
    print("\n" + "=" * 60)
    print("TEST 5: Different PSM Modes")
    print("=" * 60)

    try:

        sample_text = "Testing PSM Modes"
        image_path = Path("test_psm.png")
        create_sample_image(sample_text, image_path)


        psm_modes = [3, 6, 7, 11]

        print("\nTesting PSM Modes:")
        print("  PSM 3: Fully automatic (default)")
        print("  PSM 6: Uniform block of text")
        print("  PSM 7: Single text line")
        print("  PSM 11: Sparse text")

        for psm in psm_modes:
            engine = TesseractEngine(language="eng", psm=psm)
            await engine.initialize()

            result = await engine.process_image_file(image_path)

            print(f"\n  PSM {psm}:")
            print(f"    Text: '{result['text'].strip()}'")
            print(f"    Confidence: {result['confidence']:.2f}%")


        if image_path.exists():
            image_path.unlink()

        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        return False


async def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "OCR ENGINE TEST SUITE" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")

    tests = [
        ("Engine Factory", test_engine_factory),
        ("Tesseract Basic", test_tesseract_basic),
        ("Sample Image OCR", test_ocr_with_sample_image),
        ("User Image OCR", test_ocr_with_user_image),
        ("PSM Modes", test_different_psm_modes),
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
        print("\n🎉 All tests passed! Tesseract OCR is working!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)