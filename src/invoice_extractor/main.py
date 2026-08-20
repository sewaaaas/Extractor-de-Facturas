"""Punto de entrada ASGI de DOC-01."""

from fastapi import FastAPI

from invoice_extractor import __version__
from invoice_extractor.api.health import router as health_router
from invoice_extractor.core.config import Settings, get_settings
from invoice_extractor.core.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construye la aplicación sin activar OCR, PDF ni fases futuras."""

    active_settings = settings or get_settings()
    configure_logging(active_settings.log_level)

    application = FastAPI(
        title="Invoice Extractor",
        version=__version__,
        description="Base técnica DOC-01; no procesa comprobantes todavía.",
    )
    application.include_router(health_router)
    return application


app = create_app()
