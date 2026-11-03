"""
Módulo de Ingesta (Compatibilidad hacia atrás).
Delega directamente en el servicio de aplicación `backend.services.ingestion_service`.
"""

from .services.ingestion_service import (
    ingestion_service,
    procesar_archivo_sql,
    procesar_archivo_documento
)

__all__ = [
    "ingestion_service",
    "procesar_archivo_sql",
    "procesar_archivo_documento",
]
