"""Adaptador provisional de lectura PDF mediante PyMuPDF."""

from invoice_extractor.domain.errors import PDFProcessingError
from invoice_extractor.domain.models import PageText, StoredDocument


class PyMuPDFTextExtractor:
    """Extrae texto nativo sin filtrar tipos de PyMuPDF al dominio."""

    def extract_pages(self, document: StoredDocument) -> list[PageText]:
        """Abre el PDF y devuelve texto por página, numerada desde uno."""

        try:
            import pymupdf

            with pymupdf.open(document.path) as pdf:
                if pdf.needs_pass:
                    raise PDFProcessingError("Encrypted PDF is not supported by the DOC-01 spike")
                return [
                    PageText(page_number=index + 1, text=page.get_text("text"))
                    for index, page in enumerate(pdf)
                ]
        except PDFProcessingError:
            raise
        except Exception as exc:
            raise PDFProcessingError(f"PyMuPDF could not read the document: {exc}") from exc
