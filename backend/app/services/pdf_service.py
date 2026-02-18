from typing import List, Optional, Dict, Any
from pathlib import Path
import fitz
import io
from PIL import Image
import numpy as np

from backend.app.config import get_logger, settings
from backend.app.utils.exceptions import (
    PDFException,
    PDFMergeError,
    PDFConversionError,
    PDFCorruptedError,
    PDFPasswordProtectedError,
    PDFEmptyError
)
from backend.app.utils.file_utils import ensure_directory, save_image

logger = get_logger(__name__)


class PDFService:
    def __init__(self):
        self.logger = logger
        self.dpi = settings.DPI_CONVERSION

    async def merge_pdfs(
        self,
        pdf_paths: List[Path],
        output_path: Path
    ) -> Path:
        if not pdf_paths:
            raise PDFMergeError(
                message="No PDF files provided for merging",
                details={"pdf_count": 0}
            )

        self.logger.info(
            "Merging PDFs",
            file_count=len(pdf_paths),
            output_path=str(output_path)
        )

        try:

            merged_pdf = fitz.open()

            total_pages = 0


            for i, pdf_path in enumerate(pdf_paths, 1):
                self.logger.debug(f"Processing PDF {i}/{len(pdf_paths)}: {pdf_path}")


                if not pdf_path.exists():
                    self.logger.warning(f"PDF not found, skipping: {pdf_path}")
                    continue

                try:

                    pdf_doc = fitz.open(pdf_path)


                    if pdf_doc.is_encrypted:
                        self.logger.warning(f"PDF is password protected: {pdf_path}")
                        pdf_doc.close()
                        continue


                    merged_pdf.insert_pdf(pdf_doc)
                    page_count = pdf_doc.page_count
                    total_pages += page_count

                    self.logger.debug(
                        f"Added {page_count} pages from {pdf_path.name}"
                    )


                    pdf_doc.close()

                except Exception as e:
                    self.logger.error(
                        f"Failed to process PDF: {pdf_path}",
                        error=str(e)
                    )
                    continue

            if total_pages == 0:
                raise PDFMergeError(
                    message="No pages were merged",
                    details={
                        "input_files": len(pdf_paths),
                        "total_pages": 0
                    }
                )


            output_path.parent.mkdir(parents=True, exist_ok=True)


            merged_pdf.save(str(output_path))
            merged_pdf.close()

            self.logger.info(
                "PDF merge completed",
                output_path=str(output_path),
                total_pages=total_pages,
                input_files=len(pdf_paths)
            )

            return output_path

        except PDFMergeError:
            raise
        except Exception as e:
            self.logger.error(
                "PDF merge failed",
                error=str(e),
                exc_info=True
            )
            raise PDFMergeError(
                message=f"Failed to merge PDFs: {str(e)}",
                details={
                    "input_files": len(pdf_paths),
                    "error": str(e)
                }
            )

    async def convert_pdf_to_images(
        self,
        pdf_path: Path,
        output_dir: Path,
        dpi: Optional[int] = None,
        image_format: str = "png"
    ) -> List[Path]:
        if dpi is None:
            dpi = self.dpi

        self.logger.info(
            "Converting PDF to images",
            pdf_path=str(pdf_path),
            dpi=dpi,
            format=image_format
        )

        try:

            if not pdf_path.exists():
                raise PDFConversionError(
                    message=f"PDF file not found: {pdf_path}",
                    details={"path": str(pdf_path)}
                )


            pdf_doc = fitz.open(pdf_path)


            if pdf_doc.is_encrypted:
                pdf_doc.close()
                raise PDFPasswordProtectedError(
                    message=f"PDF is password protected: {pdf_path}",
                    details={"path": str(pdf_path)}
                )


            if pdf_doc.page_count == 0:
                pdf_doc.close()
                raise PDFEmptyError(
                    message=f"PDF has no pages: {pdf_path}",
                    details={"path": str(pdf_path)}
                )


            ensure_directory(output_dir)



            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)

            image_paths = []


            for page_num in range(pdf_doc.page_count):
                self.logger.debug(
                    f"Converting page {page_num + 1}/{pdf_doc.page_count}"
                )


                page = pdf_doc[page_num]


                pix = page.get_pixmap(matrix=mat, alpha=False)


                output_filename = f"{pdf_path.stem}_page_{page_num + 1:04d}.{image_format}"
                output_path = output_dir / output_filename


                pix.save(str(output_path))
                image_paths.append(output_path)

                self.logger.debug(f"Saved page {page_num + 1} to {output_path}")


            pdf_doc.close()

            self.logger.info(
                "PDF to images conversion completed",
                pdf_path=str(pdf_path),
                pages_converted=len(image_paths),
                dpi=dpi
            )

            return image_paths

        except (PDFConversionError, PDFPasswordProtectedError, PDFEmptyError):
            raise
        except Exception as e:
            self.logger.error(
                "PDF to images conversion failed",
                pdf_path=str(pdf_path),
                error=str(e),
                exc_info=True
            )
            raise PDFConversionError(
                message=f"Failed to convert PDF to images: {str(e)}",
                details={
                    "pdf_path": str(pdf_path),
                    "error": str(e)
                }
            )

    async def extract_text_from_pdf(
        self,
        pdf_path: Path
    ) -> Dict[str, Any]:
        self.logger.info(
            "Extracting text from PDF",
            pdf_path=str(pdf_path)
        )

        try:

            if not pdf_path.exists():
                raise PDFConversionError(
                    message=f"PDF file not found: {pdf_path}",
                    details={"path": str(pdf_path)}
                )


            pdf_doc = fitz.open(pdf_path)


            if pdf_doc.is_encrypted:
                pdf_doc.close()
                raise PDFPasswordProtectedError(
                    message=f"PDF is password protected: {pdf_path}"
                )


            pages_text = []
            total_chars = 0

            for page_num in range(pdf_doc.page_count):
                page = pdf_doc[page_num]
                text = page.get_text()
                pages_text.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "char_count": len(text)
                })
                total_chars += len(text)


            full_text = "\n\n".join(
                f"--- Page {p['page_number']} ---\n{p['text']}"
                for p in pages_text
            )


            pdf_doc.close()

            result = {
                "pdf_path": str(pdf_path),
                "page_count": len(pages_text),
                "total_characters": total_chars,
                "full_text": full_text,
                "pages": pages_text,
                "is_text_based": total_chars > 100
            }

            self.logger.info(
                "Text extraction completed",
                pdf_path=str(pdf_path),
                pages=len(pages_text),
                total_chars=total_chars
            )

            return result

        except PDFPasswordProtectedError:
            raise
        except Exception as e:
            self.logger.error(
                "Text extraction failed",
                pdf_path=str(pdf_path),
                error=str(e),
                exc_info=True
            )
            raise PDFConversionError(
                message=f"Failed to extract text: {str(e)}",
                details={
                    "pdf_path": str(pdf_path),
                    "error": str(e)
                }
            )

    async def get_pdf_info(
        self,
        pdf_path: Path
    ) -> Dict[str, Any]:
        self.logger.info(
            "Getting PDF info",
            pdf_path=str(pdf_path)
        )

        try:

            if not pdf_path.exists():
                raise PDFException(
                    message=f"PDF file not found: {pdf_path}",
                    details={"path": str(pdf_path)}
                )


            pdf_doc = fitz.open(pdf_path)


            metadata = pdf_doc.metadata


            info = {
                "filename": pdf_path.name,
                "file_size_bytes": pdf_path.stat().st_size,
                "file_size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 2),
                "page_count": pdf_doc.page_count,
                "is_encrypted": pdf_doc.is_encrypted,
                "is_pdf": pdf_doc.is_pdf,
                "metadata": {
                    "format": metadata.get("format", ""),
                    "title": metadata.get("title", ""),
                    "author": metadata.get("author", ""),
                    "subject": metadata.get("subject", ""),
                    "keywords": metadata.get("keywords", ""),
                    "creator": metadata.get("creator", ""),
                    "producer": metadata.get("producer", ""),
                    "creation_date": metadata.get("creationDate", ""),
                    "mod_date": metadata.get("modDate", ""),
                }
            }


            if pdf_doc.page_count > 0:
                first_page = pdf_doc[0]
                rect = first_page.rect
                info["page_dimensions"] = {
                    "width": rect.width,
                    "height": rect.height,
                    "width_inches": round(rect.width / 72, 2),
                    "height_inches": round(rect.height / 72, 2)
                }


            try:
                sample_text = pdf_doc[0].get_text() if pdf_doc.page_count > 0 else ""
                info["is_text_based"] = len(sample_text.strip()) > 50
                info["sample_text_length"] = len(sample_text)
            except:
                info["is_text_based"] = False
                info["sample_text_length"] = 0


            pdf_doc.close()

            self.logger.info(
                "PDF info retrieved",
                pdf_path=str(pdf_path),
                pages=info["page_count"],
                size_mb=info["file_size_mb"]
            )

            return info

        except Exception as e:
            self.logger.error(
                "Failed to get PDF info",
                pdf_path=str(pdf_path),
                error=str(e),
                exc_info=True
            )
            raise PDFException(
                message=f"Failed to get PDF info: {str(e)}",
                details={
                    "pdf_path": str(pdf_path),
                    "error": str(e)
                }
            )

    async def is_pdf_scanned(
        self,
        pdf_path: Path,
        sample_pages: int = 3
    ) -> bool:
        try:
            pdf_doc = fitz.open(pdf_path)

            if pdf_doc.page_count == 0:
                pdf_doc.close()
                return False


            pages_to_check = min(sample_pages, pdf_doc.page_count)
            total_text_length = 0

            for i in range(pages_to_check):
                text = pdf_doc[i].get_text()
                total_text_length += len(text.strip())

            pdf_doc.close()


            avg_text_per_page = total_text_length / pages_to_check
            is_scanned = avg_text_per_page < 50

            self.logger.debug(
                f"PDF scan check: avg {avg_text_per_page:.0f} chars/page, "
                f"is_scanned: {is_scanned}"
            )

            return is_scanned

        except Exception as e:
            self.logger.error(f"Failed to check if PDF is scanned: {e}")
            return True

    async def split_pdf(
        self,
        pdf_path: Path,
        output_dir: Path,
        pages_per_split: int = 1
    ) -> List[Path]:
        self.logger.info(
            f"Splitting PDF into {pages_per_split} page chunks",
            pdf_path=str(pdf_path)
        )

        try:
            pdf_doc = fitz.open(pdf_path)
            ensure_directory(output_dir)

            output_paths = []
            total_pages = pdf_doc.page_count

            for start_page in range(0, total_pages, pages_per_split):
                end_page = min(start_page + pages_per_split, total_pages)


                new_pdf = fitz.open()
                new_pdf.insert_pdf(
                    pdf_doc,
                    from_page=start_page,
                    to_page=end_page - 1
                )


                output_filename = f"{pdf_path.stem}_part_{start_page + 1:04d}.pdf"
                output_path = output_dir / output_filename
                new_pdf.save(str(output_path))
                new_pdf.close()

                output_paths.append(output_path)

                self.logger.debug(
                    f"Created split PDF: {output_filename} "
                    f"(pages {start_page + 1}-{end_page})"
                )

            pdf_doc.close()

            self.logger.info(
                "PDF split completed",
                input_pdf=str(pdf_path),
                output_files=len(output_paths)
            )

            return output_paths

        except Exception as e:
            self.logger.error(
                "PDF split failed",
                error=str(e),
                exc_info=True
            )
            raise PDFException(
                message=f"Failed to split PDF: {str(e)}",
                details={"pdf_path": str(pdf_path), "error": str(e)}
            )
