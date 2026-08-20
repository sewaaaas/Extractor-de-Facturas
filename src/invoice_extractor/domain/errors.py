"""Errores estables del dominio y sus adaptadores."""


class InvoiceExtractorError(Exception):
    """Error base controlado de la aplicación."""


class OCRProcessingError(InvoiceExtractorError):
    """El motor OCR no pudo producir un resultado válido."""


class PDFProcessingError(InvoiceExtractorError):
    """El adaptador PDF no pudo leer el documento."""
