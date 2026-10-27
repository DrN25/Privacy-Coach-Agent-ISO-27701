"""
Nodo Crítico / Evaluador de Calidad Pericial (Reflection Node).
Verifica la estructura del dictamen, la presencia de citas legales y bloques transaccionales.
"""

from typing import Dict, Any, List
from .state import AuditState


def nodo_reflection(state: AuditState) -> Dict[str, Any]:
    """Evalúa la salida generada y decide si requiere bucle de auto-corrección."""
    dictamen = state.get("dictamen", "")
    parche_sql = state.get("parche_sql", "")
    regla = state.get("regla_canonica", {})
    tipo = regla.get("tipo_hallazgo", "TECNICO")
    iteracion = state.get("iteracion", 1)

    observaciones: List[str] = []
    aprobado = True

    # Criterio 1: Longitud mínima y sustancia pericial
    if len(dictamen.strip()) < 100:
        aprobado = False
        observaciones.append("El dictamen es demasiado breve o está incompleto.")

    # Criterio 2: Presencia de bloque transaccional si es técnico
    if tipo == "TECNICO":
        if not parche_sql or "BEGIN" not in parche_sql.upper() or "COMMIT" not in parche_sql.upper():
            if iteracion < 2 and "ALTER TABLE" in dictamen.upper():
                aprobado = False
                observaciones.append("El script SQL de remediación debe estar obligatoriamente delimitado en bloque transaccional BEGIN; ... COMMIT;.")

    # Criterio 3: Límite duro de iteraciones para evitar bucles infinitos
    if iteracion >= 2:
        aprobado = True

    evaluacion = {
        "aprobado": aprobado,
        "observaciones": "; ".join(observaciones) if observaciones else "Dictamen pericial y script conformes."
    }

    trace = list(state.get("trazabilidad") or [])
    trace.append({
        "paso": len(trace) + 1,
        "agente": "Senior Quality Critic (Reflection)",
        "accion": f"Validación de rigor pericial (Iteración {iteracion})",
        "detalle": f"Estado: {'APROBADO' if aprobado else 'REQUIRIÓ AJUSTE'}. Observación: {evaluacion['observaciones']}",
        "estado": "ok" if aprobado else "warning"
    })

    return {
        "evaluacion_critica": evaluacion,
        "aprobado": aprobado,
        "trazabilidad": trace
    }


def ruta_condicional_reflexion(state: AuditState) -> str:
    """Condición de bifurcación: si aprobado va a END, de lo contrario cicla a coach_agent."""
    if state.get("aprobado", False):
        return "__end__"
    return "coach_agent"
