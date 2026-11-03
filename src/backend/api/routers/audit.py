"""
Router de Auditoría y Estado del Sistema.
Endpoints: /api/status, /api/database-view, /api/reset, /api/reanalyze, /api/load-mockups.
"""

import os
from fastapi import APIRouter, HTTPException

from ...core.config import settings
from ...infrastructure.repository import repository
from ...knowledge_bridge import knowledge_bridge
from ...services.audit_service import audit_service
from ...services.ingestion_service import ingestion_service
from ...services.document_processor import document_processor

router = APIRouter(tags=["Audit"])


@router.get("/api/status")
def get_status():
    stats = repository.obtener_estadisticas_globales()
    return {
        "status": "online",
        "llm_model": settings.openrouter_model,
        "provider": "OpenRouter",
        "zero_cost_local_kbs": {
            "iso27701_nodes": knowledge_bridge.controls_count,
            "iso27701_edges": len(knowledge_bridge.engine.adj),
            "anpd_cases": len(knowledge_bridge.sanciones)
        },
        "empresa_database": {
            "archivos": stats["num_archivos"],
            "columnas_inventariadas": stats["num_activos"],
            "hallazgos_activos": stats["num_hallazgos"]
        }
    }


@router.get("/api/database-view")
def get_database_view():
    data = repository.obtener_vista_completa_base_datos()
    hallazgos = data["hallazgos"]
    
    total_uit = sum(h["multa_estimada_uit"] for h in hallazgos if h.get("estado") == "PENDIENTE")
    total_pen = sum(h["multa_estimada_pen"] for h in hallazgos if h.get("estado") == "PENDIENTE")

    return {
        "archivos": data["archivos"],
        "inventario": data["inventario"],
        "clausulas": data["clausulas"],
        "hallazgos": hallazgos,
        "resumen_impacto": {
            "total_brechas": len(hallazgos),
            "brechas_criticas": len([h for h in hallazgos if h.get("nivel_riesgo") == "CRÍTICO"]),
            "multa_total_uit": round(total_uit, 1),
            "multa_total_pen": round(total_pen, 2)
        }
    }


@router.post("/api/reset")
def reset_database():
    repository.resetear_base_de_datos()
    return {"mensaje": "Base de datos reiniciada a cero. Espacio listo para nueva empresa."}


@router.post("/api/reanalyze")
def reanalyze_audit():
    hallazgos = audit_service.ejecutar_auditoria_completa()
    return {
        "mensaje": "Reanálisis de Privacidad completado (DSPM + Router O(1)).",
        "total_brechas": len(hallazgos)
    }


def obtener_base_dir() -> str:
    p = os.path.abspath(__file__)
    for _ in range(5):
        p = os.path.dirname(p)
    return p


@router.post("/api/load-mockups")
def load_mockups():
    base_dir = obtener_base_dir()
    mockups_dir = os.path.join(base_dir, "media", "documents")
    if not os.path.exists(mockups_dir) or not os.listdir(mockups_dir):
        mockups_dir = os.path.join(base_dir, "mockups")
        if not os.path.exists(mockups_dir):
            mockups_dir = os.path.join(base_dir, "src", "mockups")

    if not os.path.exists(mockups_dir):
        raise HTTPException(status_code=404, detail="Directorio de documentos institucionales no encontrado.")

    procesados = []
    todos = sorted(os.listdir(mockups_dir))
    archivos_unicos = []
    for f in todos:
        stem, ext = os.path.splitext(f)
        ext = ext.lower()
        if ext not in [".sql", ".pdf", ".md", ".txt"]:
            continue
        if ext == ".md" and f"{stem}.pdf" in todos:
            continue
        archivos_unicos.append(f)

    for f in archivos_unicos:
        fpath = os.path.join(mockups_dir, f)
        if not os.path.isfile(fpath):
            continue
        try:
            document_processor.procesar_archivo(fpath, f)
            procesados.append(f)
        except Exception as e:
            logger_err = str(e)
            # Fallback legacy si document_processor reporta error
            ext = os.path.splitext(f)[1].lower()
            if ext == ".sql":
                ingestion_service.procesar_sql(fpath, f)
                procesados.append(f)
            elif ext in [".pdf", ".txt", ".md"]:
                ingestion_service.procesar_documento(fpath, f)
                procesados.append(f)

    hallazgos = audit_service.ejecutar_auditoria_completa()
    return {
        "mensaje": f"Se cargaron y auditaron {len(procesados)} documentos institucionales de la UNSA con éxito.",
        "archivos_procesados": procesados,
        "total_brechas": len(hallazgos)
    }


@router.post("/api/load-single-mockup/{filename}")
def load_single_mockup(filename: str):
    if filename != os.path.basename(filename):
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")

    base_dir = obtener_base_dir()
    mockups_dir = os.path.join(base_dir, "media", "documents")
    file_path = os.path.join(mockups_dir, filename)
    if not os.path.exists(file_path):
        mockups_dir = os.path.join(base_dir, "mockups")
        file_path = os.path.join(mockups_dir, filename)
        if not os.path.exists(file_path):
            mockups_dir = os.path.join(base_dir, "src", "mockups")
            file_path = os.path.join(mockups_dir, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Documento {filename} no encontrado.")

    try:
        document_processor.procesar_archivo(file_path, filename)
    except Exception:
        if filename.endswith(".sql"):
            ingestion_service.procesar_sql(file_path, filename)
        else:
            ingestion_service.procesar_documento(file_path, filename)

    return {
        "mensaje": f"Documento institucional '{filename}' ingresado al repositorio.",
        "necesita_reanalisis": True
    }
