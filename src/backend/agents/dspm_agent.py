"""
Nodo Agente DSPM (Data Security Posture Management Agent).
Resuelve la correlación determinista entre el hallazgo auditado y el catálogo
canónico de la ISO/IEC 27701:2025 y la Ley 29733, de manera agnóstica al dominio
empresarial (banca, salud, retail, educación o servicios).
"""

import re
from typing import Dict, Any, Optional
from .state import AuditState
from ..core.rules_catalog import resolver_regla_con_fallback, CATALOGO_REGLAS, obtener_regla
from ..infrastructure.repository import repository


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
        except Exception:
            pass

    # 4. Si hay hallazgos activos en el repositorio, tomar el hallazgo de mayor severidad
    try:
        hallazgos = repository.obtener_todos_los_hallazgos()
        if hallazgos:
            # Prioridad de severidad normalizada (soporta escalas LPDP e ISO)
            prioridad = {"MUY GRAVE": 4, "CRÍTICO": 4, "CRITICO": 4, "GRAVE": 3, "ALTO": 3, "MEDIO": 2, "LEVE": 1, "BAJO": 1}
            hallazgo_top = max(hallazgos, key=lambda h: prioridad.get(str(h.get("nivel_riesgo", "MEDIO")).upper(), 1))
            return hallazgo_top.get("codigo_regla")
    except Exception:
        pass

    return None


def nodo_dspm_agent(state: AuditState) -> Dict[str, Any]:
    """
    Enriquece el estado del grafo con la regla canónica formal aplicable
    al activo o consulta de auditoría bajo evaluación.
    """
    codigo = _resolver_codigo_auditoria(state)
    regla = resolver_regla_con_fallback(codigo or "R-001")
    return {"regla_canonica": regla}
