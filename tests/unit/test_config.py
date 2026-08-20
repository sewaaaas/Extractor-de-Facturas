from invoice_extractor.core.config import Settings


def test_settings_load_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_env == "local"
    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 8000
    assert settings.max_upload_size_mb == 15
    assert settings.max_pdf_pages == 10
    assert settings.ocr_model == "PP-OCRv6_small"


def test_settings_allow_environment_override(monkeypatch) -> None:
    monkeypatch.setenv("APP_PORT", "9123")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    settings = Settings(_env_file=None)

    assert settings.app_port == 9123
    assert settings.log_level == "DEBUG"
