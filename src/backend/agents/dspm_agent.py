"""
Nodo Agente DSPM (Data Security Posture Management Agent).
Resuelve la correlación determinista entre el hallazgo auditado y el catálogo
canónico de la ISO/IEC 27701:2025 y la Ley 29733, de manera agnóstica al dominio
empresarial (banca, salud, retail, educación o servicios).
"""

import logging
import re
from typing import Dict, Any, Optional
from .state import AuditState
from ..core.rules_catalog import resolver_regla_con_fallback, CATALOGO_REGLAS, obtener_regla
from ..infrastructure.repository import repository

logger = logging.getLogger(__name__)


def _resolver_codigo_auditoria(state: AuditState) -> Optional[str]:
    """
    Identifica la regla o control aplicable a partir de la evidencia de auditoría
    o de referencias normativas formales (R-001..R-007, o controles ISO A.X.X).
    No utiliza palabras clave cableadas para garantizar generalización total.
    """
    ctx = state.get("contexto_brecha", {})
    
    # 1. Regla explícita del hallazgo auditado
    if ctx.get("codigo_regla"):
        return str(ctx["codigo_regla"]).upper()

    # 2. Búsqueda de identificadores normativos formales en el requerimiento del usuario
    historial = state.get("historial_mensajes", [])
    for m in reversed(historial):
        texto = m.get("content", "")
        # Coincidencia con código de regla canónico (R-001 a R-007)
        match_regla = re.search(r"\b(R-00[1-7])\b", texto, re.IGNORECASE)
        if match_regla:
            return match_regla.group(1).upper()

        # Coincidencia con código de control ISO 27701 (ej. A.3.24, A.1.4.5)
        match_iso = re.search(r"\b(A\.\d+\.\d+(?:\.\d+)?)\b", texto, re.IGNORECASE)
        if match_iso:
            ctrl_id = match_iso.group(1).upper()
            for r_cod, r_data in CATALOGO_REGLAS.items():
                if ctrl_id in r_data.get("control_iso27701", ""):
                    return r_cod

    # 3. Correlación por activo afectado contra los hallazgos registrados en la base de datos
    elemento = ctx.get("elemento_afectado", "").strip()
    if elemento:
        try:
            hallazgos = repository.obtener_todos_los_hallazgos()
            for h in hallazgos:
                if h.get("elemento_afectado", "").strip().lower() == elemento.lower():
                    return h.get("codigo_regla")
        except Exception as exc:
            logger.warning("No se pudieron correlacionar hallazgos (%s)", type(exc).__name__)

    # 4. Si hay hallazgos activos en el repositorio, tomar el hallazgo de mayor severidad
    try:
        hallazgos = repository.obtener_todos_los_hallazgos()
        if hallazgos:
            # Prioridad de severidad normalizada (soporta escalas LPDP e ISO)
            prioridad = {"MUY GRAVE": 4, "CRÍTICO": 4, "CRITICO": 4, "GRAVE": 3, "ALTO": 3, "MEDIO": 2, "LEVE": 1, "BAJO": 1}
            hallazgo_top = max(hallazgos, key=lambda h: prioridad.get(str(h.get("nivel_riesgo", "MEDIO")).upper(), 1))
            return hallazgo_top.get("codigo_regla")
    except Exception as exc:
        logger.warning("No se pudo consultar la severidad de hallazgos (%s)", type(exc).__name__)

    return None


def nodo_dspm_agent(state: AuditState) -> Dict[str, Any]:
    """
    Enriquece el estado del grafo con la regla canónica formal o el control ISO
    del incidente evaluado.
    """
    ctx = state.get("contexto_brecha", {})
    intencion = (state.get("intencion") or "").lower()

    if ctx.get("incident_code") and not ctx.get("codigo_regla") and not ctx.get("regla_codigo"):
        ctrl_id = ctx.get("iso27701_control_id") or ctx.get("control_iso27701") or "A.3.12"
        regla = dict(resolver_regla_con_fallback("R-999"))
        regla.update({
            "codigo": ctx.get("incident_code"),
            "titulo": ctx.get("title", regla["titulo"]),
            "control_iso27701": ctrl_id,
            "tipo_hallazgo": "DOCUMENTAL" if ctx.get("incident_type") == "PI" else "TECNICO",
            "multa_estimada_uit": float(ctx.get("multa_estimada_uit") or 0.0),
            "multa_estimada_pen": float(ctx.get("multa_estimada_pen") or 0.0),
            "precedente_anpd": ctx.get("precedente_anpd") or "Evaluación ISO/IEC 27701:2025",
        })
    elif intencion == "sql_query" and not ctx.get("codigo_regla") and not ctx.get("hallazgo_id"):
        regla = dict(resolver_regla_con_fallback("CONSULTA_SQL"))
        regla.update({
            "codigo": "SQL-LIVE",
            "titulo": "Consulta Operativa en Tiempo Real sobre PIMS UNSA",
            "control_iso27701": ctx.get("iso27701_control_id") or "A.3.12",
            "tipo_hallazgo": "DOCUMENTAL",
        })
    else:
        codigo = ctx.get("codigo_regla") or ctx.get("regla_codigo") or _resolver_codigo_auditoria(state)
        regla = resolver_regla_con_fallback(codigo or "R-001")

    trace = list(state.get("trazabilidad") or [])
    trace.append({
        "paso": len(trace) + 1,
        "agente": "DSPM Risk Engine",
        "accion": f"Resolución de control/regla ({regla.get('codigo', 'A.3.12')})",
        "detalle": f"Ref: {regla.get('codigo')} | Control ISO: {regla.get('control_iso27701')} | Nivel: {regla.get('nivel_riesgo')}",
        "estado": "ok"
    })

    return {"regla_canonica": regla, "trazabilidad": trace}
