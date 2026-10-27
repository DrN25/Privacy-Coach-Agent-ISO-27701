# -*- coding: utf-8 -*-
"""
Auditor Senior de Cumplimiento & DSPM (ISO/IEC 27701:2025 y Ley 29733 ANPD).
Punto de acceso unificado al sistema multi-agente basado en LangGraph y GPT-6 Luna.

Diseño:
- Delega la orquestación pericial al StateGraph de LangGraph (`backend.agents.graph`).
- Mantiene compatibilidad total de API y firmas para evitar rotura de contratos o tests existentes.
- Inferencia optimizada sobre openai/gpt-6-luna.
"""

import os
from typing import Dict, Any, List

from .agents.graph import ejecutar_flujo_multiagente
from .agents.coach_agent import (
    obtener_system_prompt,
    SYSTEM_PROMPT,
    ADAPTIVE_OUTPUT_RULES
)
from .infrastructure.llm_client import DEFAULT_MODEL

MODEL = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)


def dialogar_coach(historial_mensajes: list, contexto_brecha: dict) -> dict:
    """
    Punto de entrada compatible para la interacción con el Coach de Privacidad.
    Orquesta la ejecución a través del grafo multi-agente de LangGraph.
    """
    return ejecutar_flujo_multiagente(historial_mensajes, contexto_brecha)


__all__ = [
    "dialogar_coach",
    "obtener_system_prompt",
    "SYSTEM_PROMPT",
    "ADAPTIVE_OUTPUT_RULES",
    "MODEL",
]
