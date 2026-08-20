"""Smoke test manual de PaddleOCR local sobre una imagen sintética."""

import os
import platform
import sys
import tempfile
from importlib.metadata import version
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from invoice_extractor.core.config import get_settings
from invoice_extractor.domain.models import ImageInput
from invoice_extractor.infrastructure.paddleocr_adapter import PaddleOCRAdapter


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    windows_font = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "arial.ttf"
    if windows_font.is_file():
        return ImageFont.truetype(str(windows_font), size=size)
    return ImageFont.load_default()


def _create_synthetic_image(path: Path) -> None:
    image = Image.new("RGB", (1400, 360), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 70), "FACTURA DEMO", fill="black", font=_font(72))
    draw.text((70, 190), "DOCUMENTO 12345", fill="black", font=_font(64))
    image.save(path, format="PNG")


def main() -> int:
    settings = get_settings()
    cache_dir = Path.home() / ".paddlex"
    try:
        with tempfile.TemporaryDirectory(prefix="invoice-ocr-smoke-") as temporary_dir:
            image_path = Path(temporary_dir) / "synthetic-invoice.png"
            _create_synthetic_image(image_path)

            adapter = PaddleOCRAdapter(model_name=settings.ocr_model, device="cpu")
            result = adapter.recognize(ImageInput(path=image_path))

        print("OCR smoke test: OK")
        print(f"Python: {platform.python_version()} ({platform.machine()})")
        print(f"PaddleOCR: {version('paddleocr')}")
        print(f"PaddlePaddle: {version('paddlepaddle')}")
        print(f"OCR model: {result.model_name}")
        print(f"Device: {result.device}")
        print(f"Model cache: {cache_dir}")
        print(f"Elapsed ms (load + inference): {result.elapsed_ms:.2f}")
        print("Recognized lines:")
        for line in result.lines:
            score = "n/a" if line.score is None else f"{line.score:.4f}"
            print(f"  - {line.text!r} (score={score})")

        if not result.raw_text.strip():
            print("ERROR: PaddleOCR returned no text", file=sys.stderr)
            return 1
        return 0
    except Exception as exc:
        print(f"OCR smoke test: FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
