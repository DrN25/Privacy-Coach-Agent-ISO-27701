"""
Nodo Supervisor (Intention Router).
Determina si la consulta es operativa SQL en tiempo real, normativa ISO/ANPD,
de remediación, contexto o híbrida.
"""

from typing import Dict, Any
from .state import AuditState


def nodo_supervisor(state: AuditState) -> Dict[str, Any]:
    """Clasifica la intención del usuario para optimizar la cadena de ejecución de agentes."""
    historial = state.get("historial_mensajes", [])
    ultimo_mensaje = historial[-1].get("content", "").lower() if historial else ""

    sql_keywords = [
        "pendiente", "sin cerrar", "abiert", "cerrad", "crític", "critic",
        "responsable", "cuánt", "cuant", "cuál", "cual", "listar", "listado",
        "tabla con", "una tabla", "2023", "2024", "2025", "2026",
        "medida correctiva", "medidas correctivas", "qué falta", "que falta",
        "quién", "quien", "cuándo", "cuando", "abrió", "abrio",
        "incidenc", "incident", "brecha", "de qué trata", "de que trata",
        "pronóstico", "pronostico", "estado actual", "acciones",
        "este expediente", "este caso", "esta incidencia", "historial de",
    ]
    norm_keywords = ["norma", "iso", "control", "articulo", "artículo", "ley", "precedente", "anpd", "27701"]
    rem_keywords = ["parche", "remediar", "script", "corrige"]

    es_sql = any(k in ultimo_mensaje for k in sql_keywords)
    es_norm = any(k in ultimo_mensaje for k in norm_keywords)
    es_rem = any(k in ultimo_mensaje for k in rem_keywords)

    if es_rem and not es_sql:
        intencion = "remediacion"
    elif es_sql and (es_norm or es_rem):
        intencion = "hibrido"
    elif es_sql:
        intencion = "sql_query"
    elif es_norm:
        intencion = "normativo"
    elif any(k in ultimo_mensaje for k in ["empresa", "tablas", "columnas", "esquema", "base de datos"]):
        intencion = "contexto"
    else:
        intencion = "dictamen"

    trace = list(state.get("trazabilidad") or [])
    trace.append({
        "paso": len(trace) + 1,
        "agente": "Supervisor (Orquestador)",
        "accion": f"Enrutamiento de intención pericial ({intencion})",
        "detalle": f"Intención clasificada: {intencion.upper()}.",
        "estado": "ok",
    })

    return {"intencion": intencion, "trazabilidad": trace}
