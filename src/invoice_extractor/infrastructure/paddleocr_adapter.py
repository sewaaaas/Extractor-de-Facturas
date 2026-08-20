"""Adaptador reemplazable para la API Python de PaddleOCR 3.x."""

import json
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Any

from invoice_extractor.domain.errors import OCRProcessingError
from invoice_extractor.domain.models import ImageInput, OCRLine, OCRResult, Polygon

_BASELINE_MODELS: dict[str, tuple[str, str]] = {
    "PP-OCRv6_small": ("PP-OCRv6_small_det", "PP-OCRv6_small_rec"),
}


class PaddleOCRAdapter:
    """Ejecuta PP-OCR localmente y traduce su respuesta al modelo del dominio."""

    def __init__(self, model_name: str = "PP-OCRv6_small", device: str = "cpu") -> None:
        if model_name not in _BASELINE_MODELS:
            supported = ", ".join(sorted(_BASELINE_MODELS))
            raise ValueError(f"Unsupported OCR model {model_name!r}; supported: {supported}")
        if device != "cpu":
            raise ValueError("DOC-01 only validates local CPU inference")
        self.model_name = model_name
        self.device = device
        self._pipeline: Any | None = None

    def preload(self) -> None:
        """Carga pesos explícitamente antes de aceptar trabajo."""

        self._get_pipeline()

    def recognize(self, image: ImageInput) -> OCRResult:
        """Reconoce una imagen local y devuelve tipos internos del proyecto."""

        image_path = Path(image.path)
        if not image_path.is_file():
            raise OCRProcessingError(f"OCR input does not exist: {image_path}")

        started = perf_counter()
        try:
            pipeline = self._get_pipeline()
            provider_results = list(pipeline.predict(str(image_path)))
        except Exception as exc:
            raise OCRProcessingError(f"PaddleOCR inference failed: {exc}") from exc

        elapsed_ms = (perf_counter() - started) * 1000
        lines: list[OCRLine] = []
        for provider_result in provider_results:
            payload = self._result_payload(provider_result)
            lines.extend(self._lines_from_payload(payload))

        return OCRResult(
            raw_text="\n".join(line.text for line in lines),
            lines=tuple(lines),
            engine="PaddleOCR",
            engine_version=version("paddleocr"),
            model_name=self.model_name,
            elapsed_ms=elapsed_ms,
            device=self.device,
        )

    def _get_pipeline(self) -> Any:
        if self._pipeline is None:
            try:
                from paddleocr import PaddleOCR

                detection_model, recognition_model = _BASELINE_MODELS[self.model_name]
                self._pipeline = PaddleOCR(
                    text_detection_model_name=detection_model,
                    text_recognition_model_name=recognition_model,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                    device=self.device,
                    # PaddlePaddle 3.3.1 on native Windows fails while converting
                    # PP-OCRv6 PIR attributes in the oneDNN executor. The regular
                    # CPU executor is slower but works without changing models.
                    enable_mkldnn=False,
                )
            except Exception as exc:
                raise OCRProcessingError(f"PaddleOCR initialization failed: {exc}") from exc
        return self._pipeline

    @staticmethod
    def _result_payload(provider_result: Any) -> dict[str, Any]:
        payload = getattr(provider_result, "json", provider_result)
        if callable(payload):
            payload = payload()
        if isinstance(payload, str):
            payload = json.loads(payload)
        if not isinstance(payload, dict):
            try:
                payload = dict(payload)
            except (TypeError, ValueError) as exc:
                raise OCRProcessingError("Unexpected PaddleOCR result type") from exc
        result = payload.get("res", payload)
        if not isinstance(result, dict):
            raise OCRProcessingError("Unexpected PaddleOCR JSON payload")
        return result

    @classmethod
    def _lines_from_payload(cls, payload: dict[str, Any]) -> list[OCRLine]:
        texts = cls._as_list(payload.get("rec_texts", []))
        scores = cls._as_list(payload.get("rec_scores", []))
        polygons = cls._as_list(payload.get("rec_polys", payload.get("dt_polys", [])))

        lines: list[OCRLine] = []
        for index, text in enumerate(texts):
            score = float(scores[index]) if index < len(scores) else None
            polygon = cls._to_polygon(polygons[index]) if index < len(polygons) else ()
            lines.append(OCRLine(text=str(text), score=score, polygon=polygon))
        return lines

    @staticmethod
    def _as_list(value: Any) -> list[Any]:
        if value is None:
            return []
        if hasattr(value, "tolist"):
            value = value.tolist()
        return list(value)

    @staticmethod
    def _to_polygon(value: Any) -> Polygon:
        if hasattr(value, "tolist"):
            value = value.tolist()
        try:
            return tuple((float(point[0]), float(point[1])) for point in value)
        except (TypeError, ValueError, IndexError):
            return ()
