from fastapi.testclient import TestClient

from backend.api.routers import files
from backend.app import app


def test_unsupported_upload_does_not_create_directories(tmp_path, monkeypatch):
    root = tmp_path / "workspace"
    monkeypatch.setattr(files, "obtener_base_dir", lambda: str(root))

    with TestClient(app) as client:
        response = client.post("/api/upload", files={"file": ("payload.exe", b"bad")})

    assert response.status_code == 400
    assert not root.exists()


def test_supported_upload_is_saved_and_available(tmp_path, monkeypatch):
    monkeypatch.setattr(files, "obtener_base_dir", lambda: str(tmp_path))
    content = b"Politica de privacidad y proteccion de datos personales."

    with TestClient(app) as client:
        response = client.post("/api/upload", files={"file": ("politica.txt", content)})
        assert response.status_code == 200
        raw = client.get(f"/api/documents/{response.json()['archivo_id']}/raw")

    assert (tmp_path / "media" / "uploads" / "politica.txt").read_bytes() == content
    assert raw.status_code == 200
    assert raw.content == content
