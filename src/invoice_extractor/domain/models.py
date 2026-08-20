"""Modelos mínimos y neutrales para los límites de DOC-01."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType

type Point = tuple[float, float]
type Polygon = tuple[Point, ...]


@dataclass(frozen=True, slots=True)
class ImageInput:
    """Referencia local a una imagen autorizada para OCR."""

    path: Path


@dataclass(frozen=True, slots=True)
class StoredDocument:
    """Referencia interna a un documento ya almacenado de forma controlada."""

    processing_id: str
    path: Path
    original_name: str | None = None
    media_type: str | None = None


@dataclass(frozen=True, slots=True)
class OCRLine:
    """Línea reconocida con evidencia espacial opcional."""

    text: str
    score: float | None = None
    polygon: Polygon = ()


@dataclass(frozen=True, slots=True)
class OCRResult:
    """Resultado OCR estable que no expone tipos internos del proveedor."""

    raw_text: str
    lines: tuple[OCRLine, ...]
    engine: str
    engine_version: str
    model_name: str
    elapsed_ms: float
    device: str


@dataclass(frozen=True, slots=True)
class PageText:
    """Texto nativo de una página, numerada desde uno."""

    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """Documento expresado como páginas de texto para extractores futuros."""

    pages: tuple[PageText, ...]


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Contenedor neutral reservado para implementaciones de fases posteriores."""

    fields: Mapping[str, str | None] = field(default_factory=lambda: MappingProxyType({}))
