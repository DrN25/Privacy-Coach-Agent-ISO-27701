"""
Motor de Auditoría DSPM (Compatibilidad hacia atrás).
Delega directamente en el servicio de aplicación `backend.services.audit_service`.
"""

from .services.audit_service import audit_service, ejecutar_auditoria_dspm

__all__ = ["ejecutar_auditoria_dspm", "audit_service"]
