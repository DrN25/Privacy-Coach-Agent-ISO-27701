"""
Ensamblado del Grafo Multi-Agente Principal (LangGraph Main Graph).
Conecta el Supervisor, Context Agent, Profiler, DSPM, Normative, Coach y Reflection loop.
"""

from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END

from .state import AuditState
from .supervisor import nodo_supervisor
from .context_agent import nodo_context_agent
from .profiler_agent import nodo_profiler_agent
from .dspm_agent import nodo_dspm_agent
from .normative_agent import nodo_normative_agent
from .coach_agent import nodo_coach_agent
from .reflection import nodo_reflection, ruta_condicional_reflexion


def compilar_grafo_auditoria():
    """Construye y compila el flujo StateGraph completo con todos los agentes."""
    workflow = StateGraph(AuditState)

    # 1. Registrar todos los agentes especializados como nodos
    workflow.add_node("supervisor", nodo_supervisor)
    workflow.add_node("context_agent", nodo_context_agent)
    workflow.add_node("profiler_agent", nodo_profiler_agent)
    workflow.add_node("dspm_agent", nodo_dspm_agent)
    workflow.add_node("normative_agent", nodo_normative_agent)
    workflow.add_node("coach_agent", nodo_coach_agent)
    workflow.add_node("reflection", nodo_reflection)

    # 2. Conectar la tubería del flujo
    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", "context_agent")
    workflow.add_edge("context_agent", "profiler_agent")
    workflow.add_edge("profiler_agent", "dspm_agent")
    workflow.add_edge("dspm_agent", "normative_agent")
    workflow.add_edge("normative_agent", "coach_agent")
    workflow.add_edge("coach_agent", "reflection")

    # 3. Bifurcación condicional de Reflexión (Auto-corrección pericial)
    workflow.add_conditional_edges(
        "reflection",
        ruta_condicional_reflexion,
        {
            "coach_agent": "coach_agent",
            "__end__": END
        }
    )

    return workflow.compile()


# Grafo singleton compilado
grafo_multiagente_principal = compilar_grafo_auditoria()


def ejecutar_flujo_multiagente(historial_mensajes: List[Dict[str, str]], contexto_brecha: Dict[str, Any]) -> Dict[str, Any]:
    """Punto de ejecución del grafo multi-agente con contrato de respuesta estándar."""
    estado_inicial: AuditState = {
        "historial_mensajes": historial_mensajes or [],
        "contexto_brecha": contexto_brecha or {},
        "iteracion": 0,
        "aprobado": False,
        "modo": "openrouter"
    }

    resultado_final = grafo_multiagente_principal.invoke(estado_inicial)

    return {
        "content": resultado_final.get("dictamen", ""),
        "reasoning": resultado_final.get("razonamiento", ""),
        "sql_patch": resultado_final.get("parche_sql", ""),
        "mode": resultado_final.get("modo", "openrouter"),
        "regla_canonica": resultado_final.get("regla_canonica", {}),
        "evaluacion_critica": resultado_final.get("evaluacion_critica", {}),
        "contexto_empresa": resultado_final.get("contexto_empresa", {})
    }


if __name__ == "__main__":
    assert grafo_multiagente_principal is not None
    print("Multi-agent LangGraph workflow compiled successfully.")
