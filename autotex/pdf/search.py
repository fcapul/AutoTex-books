"""Text search within compiled PDFs using PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import pymupdf


class PDFSearch:
    """Search for text within a compiled PDF document."""

    def find_pages_with_text(self, pdf_path: Path, text: str) -> list[int]:
        """Return 0-based page numbers containing the given text."""
        doc = pymupdf.open(str(pdf_path))
        try:
            found_pages = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                matches = page.search_for(text)
                if matches:
                    found_pages.append(page_num)
            return found_pages
        finally:
            doc.close()

    def get_page_text(self, pdf_path: Path, page_number: int) -> str:
        """Extract full text from a single page."""
        doc = pymupdf.open(str(pdf_path))
        try:
            page = doc[page_number]
            return page.get_text()
        finally:
            doc.close()

    def get_all_text(self, pdf_path: Path) -> dict[int, str]:
        """Extract text from all pages. Returns {page_number: text}."""
        doc = pymupdf.open(str(pdf_path))
        try:
            return {i: doc[i].get_text() for i in range(len(doc))}
        finally:
            doc.close()
