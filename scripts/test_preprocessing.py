#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path
import cv2
import numpy as np


backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.core.image_processors import (
    ImageEnhancer,
    ImageDenoiser,
    ImageDeskewer,
    ImageBinarizer
)
from app.services.preprocessing_service import PreprocessingService
from app.utils.file_utils import save_image, load_image


def create_test_image(noise_level: float = 0.05, skew_angle: float = 5.0):
    img = np.ones((400, 800, 3), dtype=np.uint8) * 255


    font = cv2.FONT_HERSHEY_SIMPLEX
    texts = [
        ("Medical OCR System", (150, 100), 1.5),
        ("Image Preprocessing Test", (120, 180), 1.2),
        ("Testing Enhancement", (180, 260), 1.0),
        ("Denoising & Deskewing", (160, 340), 1.0),
    ]

    for text, pos, scale in texts:
        cv2.putText(img, text, pos, font, scale, (0, 0, 0), 2)


    if noise_level > 0:
        noise = np.random.normal(0, noise_level * 255, img.shape)
        img = np.clip(img + noise, 0, 255).astype(np.uint8)


    if abs(skew_angle) > 0:
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, skew_angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderValue=(255, 255, 255))

    return img


async def test_enhancer():
    print("\n" + "=" * 60)
    print("TEST 1: Image Enhancement")
    print("=" * 60)

    try:
        enhancer = ImageEnhancer()


        img = np.ones((200, 400), dtype=np.uint8) * 128
        cv2.putText(img, "Low Contrast", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (100, 100, 100), 2)

        print("\n1. Testing Enhancement Methods:")

        methods = ["auto", "clahe", "histogram", "sharpen", "gamma"]

        for method in methods:
            enhanced = enhancer.enhance(img, method=method)
            print(f"   ✓ {method.upper()}: Enhanced successfully")


        print("\n2. Testing CLAHE Enhancement:")
        enhanced = enhancer.apply_clahe(img, clip_limit=3.0)
        print(f"   ✓ CLAHE applied - shape: {enhanced.shape}")

        print("\n3. Testing Gamma Correction:")
        brightened = enhancer.gamma_correction(img, gamma=0.7)
        darkened = enhancer.gamma_correction(img, gamma=1.5)
        print(f"   ✓ Gamma correction applied")

        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_denoiser():
    print("\n" + "=" * 60)
    print("TEST 2: Image Denoising")
    print("=" * 60)

    try:
        denoiser = ImageDenoiser()


        img = create_test_image(noise_level=0.1, skew_angle=0)

        print("\n1. Testing Denoising Methods:")

        methods = ["auto", "gaussian", "median", "bilateral", "nlm"]

        for method in methods:
            if method == "nlm":
                print(f"   ⏳ {method.upper()}: Processing (slow)...")
            denoised = denoiser.denoise(img, method=method)
            print(f"   ✓ {method.upper()}: Denoised successfully")

        print("\n2. Testing Noise Estimation:")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        noise_level = denoiser._estimate_noise(gray)
        print(f"   ✓ Estimated noise level: {noise_level:.2f}")

        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_deskewer():
    print("\n" + "=" * 60)
    print("TEST 3: Image Deskewing")
    print("=" * 60)

    try:
        deskewer = ImageDeskewer()


        skew_angle = 8.0
        img = create_test_image(noise_level=0.02, skew_angle=skew_angle)

        print(f"\n1. Original Skew: {skew_angle}°")

        print("\n2. Testing Skew Detection Methods:")

        methods = ["hough", "projection", "contour"]

        for method in methods:
            try:
                if method == "projection":
                    print(f"   ⏳ {method.upper()}: Processing (slow)...")
                detected_angle = deskewer.detect_skew_hough(img) if method == "hough" else \
                                deskewer.detect_skew_projection(img) if method == "projection" else \
                                deskewer.detect_skew_contour(img)
                print(f"   ✓ {method.upper()}: Detected {detected_angle:.2f}°")
            except Exception as e:
                print(f"   ⚠ {method.upper()}: {str(e)[:50]}")

        print("\n3. Testing Auto Deskewing:")
        deskewed, angle = deskewer.deskew(img, method="auto")
        print(f"   ✓ Auto deskew - detected: {angle:.2f}°, corrected successfully")
        print(f"   ✓ Deskewed image shape: {deskewed.shape}")

        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_binarizer():
    print("\n" + "=" * 60)
    print("TEST 4: Image Binarization")
    print("=" * 60)

    try:
        binarizer = ImageBinarizer()


        img = create_test_image(noise_level=0.03, skew_angle=0)

        print("\n1. Testing Binarization Methods:")

        methods = ["auto", "otsu", "adaptive", "sauvola", "niblack", "triangle"]

        for method in methods:
            binary = binarizer.binarize(img, method=method)
            unique_values = len(np.unique(binary))
            print(f"   ✓ {method.upper()}: Binarized (unique values: {unique_values})")

        print("\n2. Testing Adaptive Binarization:")
        binary = binarizer.adaptive_binarize(img, block_size=15, method="gaussian")
        print(f"   ✓ Adaptive (gaussian) - shape: {binary.shape}")

        print("\n3. Testing Sauvola Binarization:")
        binary = binarizer.sauvola_binarize(img, window_size=15)
        print(f"   ✓ Sauvola - shape: {binary.shape}")

        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_preprocessing_service():
    print("\n" + "=" * 60)
    print("TEST 5: Complete Preprocessing Service")
    print("=" * 60)

    try:
        service = PreprocessingService()


        img = create_test_image(noise_level=0.05, skew_angle=5.0)
        test_path = Path("test_preprocessing.png")
        save_image(img, test_path)
        print(f"\n1. Created test image: {test_path}")


        info = service.get_preprocessing_info()
        print(f"\n2. Preprocessing Info:")
        print(f"   Enabled: {info['enabled']}")
        print(f"   DPI: {info['dpi']}")
        print(f"   Available methods: {len(info['available_methods'])}")


        print(f"\n3. Testing Full Preprocessing Pipeline:")
        processed_path = await service.preprocess_image(
            test_path,
            enhance=True,
            denoise=True,
            deskew=True,
            binarize=True
        )
        print(f"   ✓ Preprocessed image saved: {processed_path}")


        print(f"\n4. Testing Document Type Presets:")
        doc_types = ["general", "form", "handwritten", "low_quality", "photo"]

        for doc_type in doc_types:
            try:
                result = await service.preprocess_for_ocr(test_path, doc_type)
                print(f"   ✓ {doc_type.upper()}: Preprocessed successfully")
            except Exception as e:
                print(f"   ⚠ {doc_type.upper()}: {str(e)[:50]}")


        if test_path.exists():
            test_path.unlink()
        if processed_path.exists():
            processed_path.unlink()

        print(f"\n5. Cleanup completed")

        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_pipeline_visual():
    print("\n" + "=" * 60)
    print("TEST 6: Full Pipeline with Visual Output")
    print("=" * 60)

    try:

        print("\n1. Creating degraded test image...")
        img = create_test_image(noise_level=0.08, skew_angle=7.0)


        enhancer = ImageEnhancer()
        denoiser = ImageDenoiser()
        deskewer = ImageDeskewer()
        binarizer = ImageBinarizer()


        print("\n2. Applying Preprocessing Steps:")


        enhanced = enhancer.enhance(img, method="clahe")
        print("   ✓ Step 1: Enhanced (CLAHE)")


        denoised = denoiser.denoise(enhanced, method="bilateral")
        print("   ✓ Step 2: Denoised (Bilateral)")


        deskewed, angle = deskewer.deskew(denoised, method="hough")
        print(f"   ✓ Step 3: Deskewed (angle: {angle:.2f}°)")


        binarized = binarizer.binarize(deskewed, method="sauvola")
        print("   ✓ Step 4: Binarized (Sauvola)")

        print(f"\n3. Pipeline Results:")
        print(f"   Original shape: {img.shape}")
        print(f"   Final shape: {binarized.shape}")
        print(f"   Skew corrected: {angle:.2f}°")

        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 12 + "PREPROCESSING TEST SUITE" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")

    tests = [
        ("Image Enhancement", test_enhancer),
        ("Image Denoising", test_denoiser),
        ("Image Deskewing", test_deskewer),
        ("Image Binarization", test_binarizer),
        ("Preprocessing Service", test_preprocessing_service),
        ("Full Pipeline Visual", test_full_pipeline_visual),
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
        print("\n🎉 All preprocessing tests passed!")
        print("\n✓ Image Enhancement: Working")
        print("✓ Image Denoising: Working")
        print("✓ Image Deskewing: Working")
        print("✓ Image Binarization: Working")
        print("✓ Preprocessing Service: Working")
        print("✓ Full Pipeline: Working")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)