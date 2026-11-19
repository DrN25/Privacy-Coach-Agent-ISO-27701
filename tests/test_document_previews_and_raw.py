"""
Pruebas exhaustivas para la inspección y visualización nativa de documentos
institucionales de la UNSA (PDFs auténticos, esquemas SQL y directivas).
"""

import pytest
from fastapi.testclient import TestClient
from src.backend.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_mockups_structure_and_fields(client):
    """Verifica que el listado de documentos del repositorio institucional incluya metadatos completos."""
    response = client.get("/api/mockups")
    assert response.status_code == 200
    data = response.json()
    assert "mockups" in data
    mockups = data["mockups"]
    assert len(mockups) >= 20

    first = mockups[0]
    assert "nombre" in first
    assert "tamano" in first
    assert "tipo" in first
    assert "descripcion" in first
    assert "es_original_unsa" in first
    assert "cargado_en_db" in first
    assert "raw_url" in first


def test_get_raw_document_by_query_filename(client):
    """Verifica la visualización nativa de archivos por parámetro filename."""
    res_sql = client.get("/api/documents/raw?filename=schema_unsa_servicios_centrales.sql")
    assert res_sql.status_code == 200
    assert "text/plain" in res_sql.headers["content-type"]
    assert "CREATE TABLE" in res_sql.text

    res_pdf = client.get("/api/documents/raw?filename=Convenios_Oficiales_Suscritos_UNSA_2009_2026.pdf")
    assert res_pdf.status_code == 200
    assert "application/pdf" in res_pdf.headers["content-type"]
    assert len(res_pdf.content) > 100000


def test_get_raw_document_not_found(client):
    """Verifica que solicitar un archivo inexistente retorne 404."""
    response = client.get("/api/documents/raw?filename=archivo_que_no_existe_en_unsa.pdf")
    assert response.status_code == 404


def test_preview_document_existing_by_name(client):
    """Verifica que la inspección de documento por nombre devuelva la estructura de cláusulas y columnas."""
    response = client.get("/api/documents/Convenios_Oficiales_Suscritos_UNSA_2009_2026.pdf/preview")
    assert response.status_code == 200
    data = response.json()
    assert "archivo" in data
    assert "clausulas" in data
    assert "columnas_sensibles" in data
    assert "raw_url" in data
    assert data["archivo"]["nombre_archivo"] == "Convenios_Oficiales_Suscritos_UNSA_2009_2026.pdf"
    assert data["tiene_archivo_fisico"] is True


def test_preview_sql_schema_detects_columns(client):
    """Verifica que la inspección del esquema SQL retorne columnas sensibles detectadas por AST."""
    response = client.get("/api/documents/schema_unsa_servicios_centrales.sql/preview")
    assert response.status_code == 200
    data = response.json()
    assert data["archivo"]["tipo_archivo"] == "SQL"
    assert data["total_columnas"] > 0
    col_names = [c["nombre_columna"] for c in data["columnas_sensibles"]]
    assert any("password" in c.lower() or "cvv" in c.lower() or "huella" in c.lower() for c in col_names)

