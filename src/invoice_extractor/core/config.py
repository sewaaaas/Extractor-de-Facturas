"""Configuración tipada y centralizada de la aplicación."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración cargada desde entorno y, opcionalmente, desde ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["local", "test", "development", "production"] = "local"
    app_host: str = "127.0.0.1"
    app_port: int = Field(default=8000, ge=1, le=65535)
    data_dir: Path = Path("data")
    max_upload_size_mb: int = Field(default=15, ge=1)
    max_pdf_pages: int = Field(default=10, ge=1)
    ocr_model: str = "PP-OCRv6_small"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Devuelve una única instancia inmutable por proceso de la configuración."""

    return Settings()
