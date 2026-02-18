from fastapi.testclient import TestClient

from app.main import app
from app.services import translation as translation_module
from app.services.translation import TranslationResult


client = TestClient(app)


async def _fake_translate_pdf_file(file, target_language: str, request_id: str | None = None) -> TranslationResult:
    """
    Fake translation implementation for tests.

    Returns static PDF bytes so no real OpenAI call happens.
    """

    fake_pdf_bytes = b"%PDF-1.4\n%fake-translated-pdf\n"
    return TranslationResult(
        pdf_bytes=fake_pdf_bytes,
        pages=1,
        chunks=1,
        duration_seconds=0.01,
        retry_count=0,
    )


def test_translate_success_returns_pdf(monkeypatch):
    """Happy path: /translate returns a PDF response when pipeline succeeds."""

    monkeypatch.setattr(
        translation_module,
        "translate_pdf_file",
        _fake_translate_pdf_file,
    )

    files = {
        "file": ("simple_test.pdf", b"%PDF-1.4\n%minimal\n", "application/pdf"),
    }
    data = {"target_language": "French"}

    response = client.post("/translate", files=files, data=data)

    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/pdf"

