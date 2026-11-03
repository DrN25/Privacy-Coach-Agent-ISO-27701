"""
Punto de Entrada Principal (FastAPI Application Facade).
Delega la arquitectura completa a la capa modular `backend.api.main.app`
preservando compatibilidad con uvicorn y tests unitarios previos.
"""

from .api.main import app
from .coach_agent import dialogar_coach
from .db import init_db, get_db_connection
from .ingestion import procesar_archivo_sql, procesar_archivo_documento
from .dspm_engine import ejecutar_auditoria_dspm
from .knowledge_bridge import knowledge_bridge

__all__ = [
    "app",
    "dialogar_coach",
    "init_db",
    "get_db_connection",
    "procesar_archivo_sql",
    "procesar_archivo_documento",
    "ejecutar_auditoria_dspm",
    "knowledge_bridge",
]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
