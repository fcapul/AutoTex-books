"""PDF page rendering to images using PyMuPDF."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pymupdf

if TYPE_CHECKING:
    from autotex.config import ProjectConfig


class PDFRenderer:
    """Renders PDF pages to PNG images for visual review."""

    def __init__(self, config: ProjectConfig) -> None:
        self.config = config
        self.dpi = config.review.review_dpi

    def render_page(self, pdf_path: Path, page_number: int) -> bytes:
        """Render a single page to PNG bytes."""
        doc = pymupdf.open(str(pdf_path))
        try:
            page = doc[page_number]
            zoom = self.dpi / 72
            mat = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            return pix.tobytes("png")
        finally:
            doc.close()

    def render_pages(self, pdf_path: Path, page_numbers: list[int]) -> list[bytes]:
        """Render multiple pages to PNG bytes."""
        doc = pymupdf.open(str(pdf_path))
        try:
            results = []
            for pn in page_numbers:
                page = doc[pn]
                zoom = self.dpi / 72
                mat = pymupdf.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                results.append(pix.tobytes("png"))
            return results
        finally:
            doc.close()

    def get_total_pages(self, pdf_path: Path) -> int:
        """Return the total number of pages in the PDF."""
        doc = pymupdf.open(str(pdf_path))
        try:
            return len(doc)
        finally:
            doc.close()

    def get_chapter_last_pages(
        self,
        pdf_path: Path,
        chapter_number: int,
        chapter_title: str,
        count: int = 2,
    ) -> list[int]:
        """Find the last N pages of a chapter.

        Searches for the chapter heading in the PDF text and identifies
        where the next chapter begins (or the document ends).
        """
        doc = pymupdf.open(str(pdf_path))
        try:
            chapter_start = None
            next_chapter_start = None

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                if chapter_title in text and f"Chapter {chapter_number}" in text:
                    chapter_start = page_num
                elif chapter_start is not None and "Chapter " in text:
                    # Found the start of the next chapter
                    next_chapter_start = page_num
                    break

            if chapter_start is None:
                raise ValueError(
                    f"Could not find Chapter {chapter_number} "
                    f"('{chapter_title}') in PDF"
                )

            end_page = (
                next_chapter_start - 1 if next_chapter_start else len(doc) - 1
            )
            start_page = max(chapter_start, end_page - count + 1)
            return list(range(start_page, end_page + 1))
        finally:
            doc.close()
