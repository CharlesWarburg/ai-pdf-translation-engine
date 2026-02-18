from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_translate_rejects_unsupported_language():
    """Unsupported target_language should return 400 with clean JSON."""

    files = {"file": ("doc.pdf", b"%PDF-1.4\n", "application/pdf")}
    data = {"target_language": "Italian"}

    response = client.post("/translate", files=files, data=data)

    assert response.status_code == 400
    body = response.json()
    assert body.get("code") == "bad_request"
    assert "Unsupported target language" in body.get("message", "")


def test_translate_rejects_non_pdf_extension():
    """Uploading a non-PDF file should return 400."""

    files = {
        "file": ("test.txt", b"not a pdf", "text/plain"),
    }
    data = {"target_language": "French"}

    response = client.post("/translate", files=files, data=data)

    assert response.status_code == 400

