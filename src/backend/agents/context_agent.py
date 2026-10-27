"""
Nodo Agente de Contexto Empresarial (Corporate Context Agent).
Recupera el inventario de datos, tablas y cláusulas desde SQLite (Local Knowledge Base).
"""

from typing import Dict, Any
from .state import AuditState
from ..infrastructure.repository import repository


def nodo_context_agent(state: AuditState) -> Dict[str, Any]:
    """Recupera los activos del caso para enriquecer el expediente."""
    ctx = state.get("contexto_brecha", {})
    elemento = ctx.get("elemento_afectado", "")
    
    # Traer vista de activos
    data = repository.obtener_vista_completa_base_datos()
    
    archivos = [a.get("nombre_archivo", "") for a in data.get("archivos", []) if a.get("nombre_archivo")]
    tablas = sorted(list(set(i.get("nombre_tabla", "") for i in data.get("inventario", []) if i.get("nombre_tabla"))))
    
    contexto_empresa = {
        "total_archivos": len(data.get("archivos", [])),
        "total_activos": len(data.get("inventario", [])),
        "total_clausulas": len(data.get("clausulas", [])),
        "activo_actual": elemento,
        "archivos_cargados": archivos,
        "tablas_identificadas": tablas
    }
    
    return {"contexto_empresa": contexto_empresa}
