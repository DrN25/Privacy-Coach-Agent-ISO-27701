import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from backend.app import app

client = TestClient(app)

def test_api_status():
    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"

def test_legal_reference_control():
    resp = client.get("/api/legal-reference/control/A.1.4.5")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tipo"] == "control"
    assert data["data"]["id"] == "A.1.4.5"
    assert "PII minimization" in data["data"]["title"]
    assert len(data["principios_vinculados"]) > 0

def test_legal_reference_articulo():
    resp = client.get("/api/legal-reference/articulo/Art_13")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tipo"] == "articulo"
    assert data["data"]["articulo"] == 13

def test_legal_reference_sancion():
    resp = client.get("/api/legal-reference/sancion/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["tipo"] == "sancion"
    assert "entidad" in data["data"]
    assert data["data"]["multa_total_uit"] > 0

def test_export_dictamen_markdown():
    resp = client.get("/api/export-dictamen/R-003")
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers.get("content-type", "")
    assert "attachment; filename=" in resp.headers.get("content-disposition", "")
    content = resp.text
    assert "DICTAMEN PERICIAL DE AUDITORÍA Y CUMPLIMIENTO DSPM" in content
    assert "R-003" in content
    assert "ISO/IEC 27701:2025" in content
