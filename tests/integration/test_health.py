from fastapi.testclient import TestClient

from invoice_extractor.core.config import Settings
from invoice_extractor.main import create_app


def test_health_check_returns_expected_contract() -> None:
    client = TestClient(create_app(Settings(_env_file=None, app_env="test")))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "invoice-extractor"}
