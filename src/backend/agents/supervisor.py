"""
Nodo Supervisor (Intention Router).
Determina el flujo del grafo analizando la consulta del auditor y el contexto del hallazgo.
"""

from typing import Dict, Any
from .state import AuditState


def nodo_supervisor(state: AuditState) -> Dict[str, Any]:
    """
    Clasifica la intención del usuario para optimizar la cadena de ejecución de agentes.
    """
    historial = state.get("historial_mensajes", [])
    ultimo_mensaje = historial[-1].get("content", "").lower() if historial else ""

    if any(k in ultimo_mensaje for k in ["parche", "remediar", "sql", "script", "corrige"]):
        intencion = "remediacion"
    elif any(k in ultimo_mensaje for k in ["norma", "iso", "control", "articulo", "ley", "precedente"]):
        intencion = "normativo"
    elif any(k in ultimo_mensaje for k in ["empresa", "tablas", "columnas", "esquema", "base de datos"]):
        intencion = "contexto"
    else:
        intencion = "dictamen"

    return {"intencion": intencion}
