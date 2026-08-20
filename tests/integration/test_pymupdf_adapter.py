from pathlib import Path

import pymupdf

from invoice_extractor.domain.models import StoredDocument
from invoice_extractor.infrastructure.pymupdf_adapter import PyMuPDFTextExtractor


def _write_pdf(path: Path) -> None:
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_text((72, 72), "PDF TEST DOC-01")
        pdf.save(path)


def test_adapter_extracts_text_without_leaking_provider_types(tmp_path: Path) -> None:
    path = tmp_path / "synthetic.pdf"
    _write_pdf(path)
    document = StoredDocument(processing_id="test", path=path)

    pages = PyMuPDFTextExtractor().extract_pages(document)

    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "PDF TEST DOC-01" in pages[0].text
