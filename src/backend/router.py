"""
Router de Reglas DSPM y Normativa (Compatibilidad hacia atrás).
Delega directamente en el catálogo canónico unificado `backend.core.rules_catalog`.
"""

from typing import Dict, Any
from .core.rules_catalog import (
    CATALOGO_REGLAS,
    resolver_regla_con_fallback,
    ReglaAuditoria
)

# Compatibilidad con código previo que accede a ROUTER_MAP directamente
ROUTER_MAP: Dict[str, Dict[str, Any]] = CATALOGO_REGLAS


def resolver_enrutamiento(codigo_regla: str) -> Dict[str, Any]:
    """Resuelve la regla canónica o fallback estructurado."""
    return dict(resolver_regla_con_fallback(codigo_regla))
