from invoice_extractor.infrastructure.paddleocr_adapter import PaddleOCRAdapter


def test_adapter_translates_provider_payload_to_domain_lines() -> None:
    payload = {
        "rec_texts": ["FACTURA", "12345"],
        "rec_scores": [0.98, 0.91],
        "rec_polys": [
            [[0, 0], [20, 0], [20, 10], [0, 10]],
            [[0, 20], [20, 20], [20, 30], [0, 30]],
        ],
    }

    lines = PaddleOCRAdapter._lines_from_payload(payload)

    assert [line.text for line in lines] == ["FACTURA", "12345"]
    assert lines[0].score == 0.98
    assert lines[1].polygon[2] == (20.0, 30.0)


def test_adapter_accepts_json_envelope() -> None:
    payload = PaddleOCRAdapter._result_payload(
        '{"res": {"rec_texts": ["DEMO"], "rec_scores": [0.9]}}'
    )

    assert payload["rec_texts"] == ["DEMO"]
