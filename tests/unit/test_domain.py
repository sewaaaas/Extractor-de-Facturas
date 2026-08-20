from pathlib import Path

from invoice_extractor.domain.models import ImageInput, OCRLine, OCRResult, PageText
from invoice_extractor.domain.ports import OCRService, PDFTextExtractor


class FakeOCRService:
    def recognize(self, image: ImageInput) -> OCRResult:
        return OCRResult(
            raw_text="DEMO",
            lines=(OCRLine(text="DEMO", score=0.99),),
            engine="fake",
            engine_version="1",
            model_name="fake-model",
            elapsed_ms=1.0,
            device="cpu",
        )


class FakePDFTextExtractor:
    def extract_pages(self, document) -> list[PageText]:
        return [PageText(page_number=1, text=str(document.path))]


def test_domain_models_can_be_constructed() -> None:
    result = FakeOCRService().recognize(ImageInput(path=Path("synthetic.png")))

    assert result.raw_text == "DEMO"
    assert result.lines[0].score == 0.99


def test_ports_accept_structural_fake_implementations() -> None:
    assert isinstance(FakeOCRService(), OCRService)
    assert isinstance(FakePDFTextExtractor(), PDFTextExtractor)
