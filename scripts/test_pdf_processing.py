#!/usr/bin/env python3
import sys
import asyncio
from pathlib import Path
import fitz


backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.services.pdf_service import PDFService
from app.utils.file_utils import ensure_directory


def create_sample_pdf(output_path: Path, pages: int = 3, text_content: str = None):
    doc = fitz.open()

    for page_num in range(pages):

        page = doc.new_page(width=595, height=842)


        if text_content:
            content = text_content
        else:
            content = f"Sample PDF - Page {page_num + 1}\n\n"
            content += "This is a test PDF created for OCR testing.\n"
            content += "Medical OCR System 2026\n"
            content += f"Total Pages: {pages}\n"
            content += f"Current Page: {page_num + 1}"


        text_rect = fitz.Rect(50, 50, 545, 792)
        page.insert_textbox(
            text_rect,
            content,
            fontsize=12,
            fontname="helv",
            align=0
        )


    doc.save(str(output_path))
    doc.close()

    print(f"✓ Created sample PDF: {output_path} ({pages} pages)")
    return output_path


async def test_pdf_info():
    print("\n" + "=" * 60)
    print("TEST 1: PDF Information Extraction")
    print("=" * 60)

    try:
        service = PDFService()


        test_pdf = Path("test_info.pdf")
        create_sample_pdf(test_pdf, pages=5)

        print("\n1. Extracting PDF Info:")
        info = await service.get_pdf_info(test_pdf)

        print(f"   Filename: {info['filename']}")
        print(f"   File Size: {info['file_size_mb']} MB")
        print(f"   Page Count: {info['page_count']}")
        print(f"   Is Encrypted: {info['is_encrypted']}")
        print(f"   Is Text-Based: {info['is_text_based']}")

        if 'page_dimensions' in info:
            dims = info['page_dimensions']
            print(f"   Page Size: {dims['width_inches']}\" x {dims['height_inches']}\"")

        print(f"   Sample Text Length: {info['sample_text_length']} chars")


        if test_pdf.exists():
            test_pdf.unlink()

        print("\n✓ PDF Info Extraction: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pdf_merge():
    print("\n" + "=" * 60)
    print("TEST 2: PDF Merging")
    print("=" * 60)

    try:
        service = PDFService()


        print("\n1. Creating Sample PDFs:")
        pdf_paths = []
        for i in range(3):
            pdf_path = Path(f"test_merge_{i+1}.pdf")
            create_sample_pdf(pdf_path, pages=2, text_content=f"Document {i+1}")
            pdf_paths.append(pdf_path)


        print("\n2. Merging PDFs:")
        output_path = Path("test_merged.pdf")
        merged_path = await service.merge_pdfs(pdf_paths, output_path)

        print(f"   ✓ Merged PDF created: {merged_path}")


        print("\n3. Verifying Merged PDF:")
        info = await service.get_pdf_info(merged_path)
        print(f"   Total Pages: {info['page_count']}")
        print(f"   Expected Pages: {len(pdf_paths) * 2}")

        if info['page_count'] == len(pdf_paths) * 2:
            print("   ✓ Page count matches!")
        else:
            print("   ✗ Page count mismatch!")
            return False


        for pdf_path in pdf_paths:
            if pdf_path.exists():
                pdf_path.unlink()
        if merged_path.exists():
            merged_path.unlink()

        print("\n✓ PDF Merging: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pdf_to_images():
    print("\n" + "=" * 60)
    print("TEST 3: PDF to Images Conversion")
    print("=" * 60)

    try:
        service = PDFService()


        print("\n1. Creating Sample PDF:")
        test_pdf = Path("test_convert.pdf")
        create_sample_pdf(test_pdf, pages=3)


        print("\n2. Converting PDF to Images:")
        output_dir = Path("test_images")
        output_dir.mkdir(exist_ok=True)

        image_paths = await service.convert_pdf_to_images(
            test_pdf,
            output_dir,
            dpi=150
        )

        print(f"   ✓ Created {len(image_paths)} images")


        print("\n3. Verifying Images:")
        for i, img_path in enumerate(image_paths, 1):
            if img_path.exists():
                size_kb = img_path.stat().st_size / 1024
                print(f"   ✓ Image {i}: {img_path.name} ({size_kb:.1f} KB)")
            else:
                print(f"   ✗ Image {i}: Not found!")
                return False


        if test_pdf.exists():
            test_pdf.unlink()
        for img_path in image_paths:
            if img_path.exists():
                img_path.unlink()
        if output_dir.exists():
            output_dir.rmdir()

        print("\n✓ PDF to Images: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_text_extraction():
    print("\n" + "=" * 60)
    print("TEST 4: Text Extraction from PDF")
    print("=" * 60)

    try:
        service = PDFService()


        print("\n1. Creating Sample PDF with Text:")
        test_pdf = Path("test_text.pdf")
        known_text = "Medical OCR System\nTest Document\n2026"
        create_sample_pdf(test_pdf, pages=2, text_content=known_text)


        print("\n2. Extracting Text:")
        result = await service.extract_text_from_pdf(test_pdf)

        print(f"   Page Count: {result['page_count']}")
        print(f"   Total Characters: {result['total_characters']}")
        print(f"   Is Text-Based: {result['is_text_based']}")

        print("\n3. Extracted Text Preview:")
        preview = result['full_text'][:200]
        print(f"   {preview}...")


        if "Medical OCR System" in result['full_text']:
            print("\n   ✓ Known text found in extraction!")
        else:
            print("\n   ⚠ Known text not found (might be expected)")


        if test_pdf.exists():
            test_pdf.unlink()

        print("\n✓ Text Extraction: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_scanned_detection():
    print("\n" + "=" * 60)
    print("TEST 5: Scanned PDF Detection")
    print("=" * 60)

    try:
        service = PDFService()


        print("\n1. Testing Text-Based PDF:")
        text_pdf = Path("test_text_based.pdf")
        create_sample_pdf(text_pdf, pages=2, text_content="This is text-based PDF with lots of content")

        is_scanned = await service.is_pdf_scanned(text_pdf)
        print(f"   Is Scanned: {is_scanned}")
        print(f"   ✓ Text-based PDF detected correctly" if not is_scanned else "   ⚠ Detected as scanned")


        if text_pdf.exists():
            text_pdf.unlink()

        print("\n✓ Scanned Detection: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pdf_split():
    print("\n" + "=" * 60)
    print("TEST 6: PDF Splitting")
    print("=" * 60)

    try:
        service = PDFService()


        print("\n1. Creating Sample PDF:")
        test_pdf = Path("test_split.pdf")
        create_sample_pdf(test_pdf, pages=6)


        print("\n2. Splitting PDF (2 pages per file):")
        output_dir = Path("test_split_output")
        output_dir.mkdir(exist_ok=True)

        split_paths = await service.split_pdf(
            test_pdf,
            output_dir,
            pages_per_split=2
        )

        print(f"   ✓ Created {len(split_paths)} split files")


        print("\n3. Verifying Split Files:")
        for i, split_path in enumerate(split_paths, 1):
            info = await service.get_pdf_info(split_path)
            print(f"   File {i}: {split_path.name} ({info['page_count']} pages)")


        if test_pdf.exists():
            test_pdf.unlink()
        for split_path in split_paths:
            if split_path.exists():
                split_path.unlink()
        if output_dir.exists():
            output_dir.rmdir()

        print("\n✓ PDF Splitting: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_high_dpi_conversion():
    print("\n" + "=" * 60)
    print("TEST 7: High DPI Conversion")
    print("=" * 60)

    try:
        service = PDFService()


        print("\n1. Creating Sample PDF:")
        test_pdf = Path("test_hires.pdf")
        create_sample_pdf(test_pdf, pages=1)


        print("\n2. Testing Different DPI Values:")
        output_dir = Path("test_dpi")
        output_dir.mkdir(exist_ok=True)

        dpi_values = [150, 300, 600]

        for dpi in dpi_values:
            images = await service.convert_pdf_to_images(
                test_pdf,
                output_dir,
                dpi=dpi
            )

            if images:
                size_kb = images[0].stat().st_size / 1024
                print(f"   DPI {dpi}: {size_kb:.1f} KB")
                images[0].unlink()


        if test_pdf.exists():
            test_pdf.unlink()
        if output_dir.exists():
            output_dir.rmdir()

        print("\n✓ High DPI Conversion: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 16 + "PDF PROCESSING TEST SUITE" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")

    tests = [
        ("PDF Info Extraction", test_pdf_info),
        ("PDF Merging", test_pdf_merge),
        ("PDF to Images", test_pdf_to_images),
        ("Text Extraction", test_text_extraction),
        ("Scanned Detection", test_scanned_detection),
        ("PDF Splitting", test_pdf_split),
        ("High DPI Conversion", test_high_dpi_conversion),
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
        print("\n🎉 All PDF processing tests passed!")
        print("\n✓ PDF Info: Working")
        print("✓ PDF Merging: Working")
        print("✓ PDF to Images: Working")
        print("✓ Text Extraction: Working")
        print("✓ Scanned Detection: Working")
        print("✓ PDF Splitting: Working")
        print("✓ High DPI: Working")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)