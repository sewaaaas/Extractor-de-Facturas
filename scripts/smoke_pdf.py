"""Smoke test manual de PyMuPDF usando un PDF sintético temporal."""

import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

import pymupdf

from invoice_extractor.core.ids import new_processing_id
from invoice_extractor.domain.models import StoredDocument
from invoice_extractor.infrastructure.pymupdf_adapter import PyMuPDFTextExtractor


def _create_synthetic_pdf(path: Path) -> None:
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "PDF SINTETICO DOC-01")
        page.insert_text((72, 100), "Sin datos reales")
        pdf.save(path)


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(prefix="invoice-pdf-smoke-") as temporary_dir:
            pdf_path = Path(temporary_dir) / "synthetic.pdf"
            _create_synthetic_pdf(pdf_path)
            document = StoredDocument(
                processing_id=new_processing_id(),
                path=pdf_path,
                original_name="synthetic.pdf",
                media_type="application/pdf",
            )
            pages = PyMuPDFTextExtractor().extract_pages(document)

        print("PDF smoke test: OK")
        print(f"PyMuPDF: {version('pymupdf')}")
        print(f"Pages: {len(pages)}")
        print(f"Page 1 text: {pages[0].text.strip()!r}")
        if len(pages) != 1 or "PDF SINTETICO DOC-01" not in pages[0].text:
            print("ERROR: unexpected PDF extraction result", file=sys.stderr)
            return 1
        return 0
    except Exception as exc:
        print(f"PDF smoke test: FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
