from backend.services.export_service import export_service
from backend.services.audit_service import audit_service
from backend.infrastructure.repository import repository


def test_export_service_generates_markdown_report():
    reporte = export_service.generar_reporte_consolidado_markdown()
    assert "# INFORME TÉCNICO PERICIAL" in reporte
    assert "ISO/IEC 27701:2025" in reporte
    assert "Ley Peruana N.° 29733" in reporte


def test_audit_service_structure():
    assert audit_service is not None
    assert hasattr(audit_service, "ejecutar_auditoria_completa")


def test_repository_methods_exist():
    assert hasattr(repository, "obtener_estadisticas_globales")
    assert hasattr(repository, "obtener_vista_completa_base_datos")
    assert hasattr(repository, "obtener_todos_los_hallazgos")
