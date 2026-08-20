"""Puertos que desacoplan el dominio de OCR, PDF y futuros extractores."""

from typing import Protocol, runtime_checkable

from invoice_extractor.domain.models import (
    ExtractionResult,
    ImageInput,
    OCRResult,
    PageText,
    ParsedDocument,
    StoredDocument,
)


@runtime_checkable
class OCRService(Protocol):
    """Reconoce texto sin exponer el SDK utilizado."""

    def recognize(self, image: ImageInput) -> OCRResult: ...


@runtime_checkable
class PDFTextExtractor(Protocol):
    """Extrae texto nativo por página de un PDF controlado."""

    def extract_pages(self, document: StoredDocument) -> list[PageText]: ...


@runtime_checkable
class DocumentExtractor(Protocol):
    """Contrato futuro para obtener campos estructurados de un documento."""

    def extract(self, document: ParsedDocument) -> ExtractionResult: ...
