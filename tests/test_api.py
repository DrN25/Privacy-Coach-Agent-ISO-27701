from fastapi.testclient import TestClient

from backend.app import app


def test_demo_end_to_end_and_normative_subgraph():
    with TestClient(app) as client:
        assert client.post("/api/reset").status_code == 200
        loaded = client.post("/api/load-mockups")
        view = client.get("/api/database-view").json()
        subgraph = client.get("/api/subgraph/A.3.24").json()

    assert loaded.status_code == 200
    assert len(view["archivos"]) == 4
    assert len(view["inventario"]) >= 40
    assert {finding["codigo_regla"] for finding in view["hallazgos"]} == {
        "R-001", "R-002", "R-003", "R-004", "R-005", "R-006", "R-007"
    }
    assert subgraph["control"] == "A.3.24"
    assert subgraph["subgrafo_nodos"]


def test_chat_injects_normative_context_without_real_llm(monkeypatch):
    captured = {}

    def fake_coach(messages, finding):
        captured.update(finding)
        return {
            "content": "dictamen simulado",
            "reasoning": "",
            "sql_patch": "SELECT 1;",
            "mode": "openrouter",
        }

    monkeypatch.setattr("backend.app.dialogar_coach", fake_coach)

    with TestClient(app) as client:
        client.post("/api/reset")
        client.post("/api/load-mockups")
        finding_id = client.get("/api/database-view").json()["hallazgos"][0]["id"]
        response = client.post(
            "/api/chat",
            json={"hallazgo_id": finding_id, "mensaje_usuario": "Analiza", "historial": []},
        )

    assert response.status_code == 200
    assert response.json()["mode"] == "openrouter"
    assert captured["contexto_normativo"]["subgrafo_nodos"]


def test_upload_rejects_unsupported_extension():
    with TestClient(app) as client:
        response = client.post("/api/upload", files={"file": ("payload.exe", b"bad")})

    assert response.status_code == 400


def test_production_requires_basic_auth(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("APP_USERNAME", "auditor")
    monkeypatch.setenv("APP_PASSWORD", "secret")

    with TestClient(app) as client:
        assert client.get("/api/status").status_code == 200
        assert client.get("/").status_code == 401
        assert client.get("/", auth=("auditor", "secret")).status_code == 200
