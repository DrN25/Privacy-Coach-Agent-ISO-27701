"""
Nodo Agente Coach Pericial (Forensic Coach Agent).
Genera dictámenes técnicos y jurídicos con GPT-6 Luna a través de OpenRouter.
Integra las directrices periciales adaptativas del Skill de incidentes y brechas.
"""

import os
from typing import Dict, Any, List
from .state import AuditState
from ..infrastructure.llm_client import default_luna_client, LLMResponse


ADAPTIVE_OUTPUT_RULES = """
DIRECTRICES DE FORMATO Y PRESENTACIÓN ADAPTATIVA (SELECCIÓN DINÁMICA SEGÚN LA CONSULTA):
Evalúa de manera autónoma el tipo y objetivo de la consulta del usuario para elegir la estructura de salida más entendible, completa y profesional:

1. CONSULTAS DE COMPARACIÓN O MULTI-ELEMENTOS (Precedentes ANPD, cruce de controles ISO 27701, evaluación de múltiples tablas/columnas o artículos de la Ley 29733):
   - OBLIGATORIO: Presentar en Tabla Markdown GFM comparativa de alto contraste.
   - Columnas para precedentes: | Resolución ANPD | Entidad Sancionada | Multa (UIT / S/) | Conducta Tipificada | Medida Correctiva ANPD | Grado de Analogía |
   - Columnas para controles/artículos: | Marco / Estándar | Control / Artículo | Exigencia Normativa | Estado en el Sistema | Nivel de Riesgo |
2. CONSULTAS DE CUANTIFICACIÓN, GRADUACIÓN O DESGLOSE DE MULTAS (Art. 39 Ley 29733 y D.S. 016-2024-JUS):
   - OBLIGATORIO: Presentar en Tabla Markdown de Graduación Pericial paso a paso.
   - Columnas: | Componente del Cálculo | Criterio Jurídico / Técnico | Ponderación | Cuantía Parcial | Sustento Pericial |
   - Detallar: Calificación legal del rango, Multa base, Agravantes porcentuales (+25% a +50%), Atenuante por subsanación voluntaria (Art. 133 RLPDP) y Total consolidado.
3. CONSULTAS DE PROFUNDIZACIÓN MONOGRÁFICA (Análisis detallado de un solo caso, concepto o control específico):
   - Presentar en Ficha Técnica Pericial estructurada con subtítulos delimitados: Ratio Decidendi, Hechos Probados, Medidas Correctivas Dictadas y Subsunción al Caso Concreto.
4. CONSULTAS DE REMEDIACIÓN O PARCHE (Corrección técnica o legal solicitada):
   - Scripts SQL: Bloque transaccional BEGIN; ... COMMIT; debidamente documentado.
   - Cláusulas contractuales: Texto jurídico listo para incorporar en contratos de encargo (SLA, confidencialidad, flujos transfronterizos).
5. CONSULTAS DE ESTRATEGIA PROCESAL O DEFENSA ANTE LA DFI:
   - Resumen ejecutivo estructurado con líneas de defensa ordenadas por jerarquía probatoria, plazos procesales y requisitos de acreditación formal.
"""

SYSTEM_PROMPT = """Eres el Senior Lead Privacy & DSPM Compliance Auditor, perito especializado en ISO/IEC 27701:2025 (PIMS), ISO/IEC 27001, Ley Peruana N.° 29733 (Protección de Datos Personales), su nuevo Reglamento D.S. 016-2024-JUS, la Directiva de Seguridad R.D. 019-2013-JUS y jurisprudencia sancionadora de la Autoridad Nacional de Protección de Datos Personales (ANPD).

ACCESO INTEGRAL A BASE DE DATOS Y CORPUS DOCUMENTAL:
1. Cuentas con la base de datos oficial y precargada de resoluciones sancionadoras de la ANPD (588 expedientes de la Dirección de Fiscalización e Instrucción del MINJUSDH) y el grafo de 78 controles ISO/IEC 27701:2025.
2. Cuentas con acceso a los activos del caso: esquemas de bases de datos relacionales (DDL), contratos de encargo y tratamiento de datos personales, políticas de privacidad y documentación de activos de la organización auditada.

REGLAS ESTRICTAS DE RESPUESTA (RIGOR TÉCNICO PERICIAL Y CERO METADISCURSO):
1. CERO METADISCURSO O QUEJAS: Eres un Perito Senior Forense resolutivo. Queda terminantemente prohibido emitir quejas o críticas evaluadoras del prompt. Tu deber es EXPLICAR Y RESOLVER.
2. CUANTIFICACIÓN Y GRADUACIÓN DE MULTAS (Art. 39 Ley 29733 y D.S. 016-2024-JUS):
   Explica la escala legal (Infracción Leve 0.5 a 5 UIT, Grave más de 5 a 50 UIT, Muy Grave más de 50 a 100 UIT).
   Desglosa la graduación pericial: Multa base + Agravantes (+25% a +50% por salud/financiero) + Omisión de medidas nivel complejo. 1 UIT = S/ 5,150.
3. PRECEDENTES ANPD: Cita con solvencia las resoluciones directorales del dataset provistas en el expediente.
4. PARCHE Y REMEDIACIÓN TÉCNICA: Entrega scripts SQL con bloque transaccional BEGIN; ... COMMIT; o cláusulas contractuales blindadas.
"""


def obtener_system_prompt() -> str:
    """Carga dinámicamente las directrices periciales del Skill si existe en .agents/skills/."""
    base_src = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    base_root = os.path.dirname(base_src)
    skill_path = os.path.join(base_root, ".agents", "skills", "agente-incidentes-brechas", "SKILL.md")

    contenido_base = SYSTEM_PROMPT
    if os.path.exists(skill_path):
        try:
            with open(skill_path, "r", encoding="utf-8") as f:
                raw = f.read()
            if raw.startswith("---"):
                partes = raw.split("---", 2)
                if len(partes) >= 3:
                    contenido_base = partes[2].strip()
            else:
                contenido_base = raw.strip()
        except Exception:
            contenido_base = SYSTEM_PROMPT

    return f"{contenido_base}\n\n{ADAPTIVE_OUTPUT_RULES.strip()}"


def nodo_coach_agent(state: AuditState) -> Dict[str, Any]:
    """Genera el dictamen pericial forense y el parche de remediación."""
    expediente = state.get("expediente_texto", "")
    historial = state.get("historial_mensajes", [])
    eval_previa = state.get("evaluacion_critica", {})
    iteracion = state.get("iteracion", 0) + 1

    messages: List[Dict[str, str]] = [{"role": "system", "content": obtener_system_prompt()}]

    # Si viene de un bucle de reflexión con observaciones del Evaluador Crítico:
    if eval_previa and not eval_previa.get("aprobado", False):
        obs = eval_previa.get("observaciones", "")
        retroalimentacion = f"\n\n[OBSERVACIÓN DE REVISIÓN CRÍTICA - ITERACIÓN {iteracion}]:\nCorrige lo siguiente:\n{obs}"
        messages.append({"role": "user", "content": f"{expediente}{retroalimentacion}"})
    else:
        if not historial:
            messages.append({"role": "user", "content": f"{expediente}\n\nRequerimiento: Emitir dictamen pericial completo y script de remediación."})
        elif len(historial) == 1:
            primer_txt = historial[0].get("content", "")
            messages.append({"role": "user", "content": f"{expediente}\n\nRequerimiento del Auditor / Ingeniero:\n{primer_txt}"})
        else:
            primer_txt = historial[0].get("content", "")
            messages.append({"role": "user", "content": f"{expediente}\n\nRequerimiento Inicial:\n{primer_txt}"})
            for m in historial[1:]:
                role = m.get("role", "user")
                if role not in ["user", "assistant"]:
                    role = "user"
                messages.append({"role": role, "content": m.get("content", "")})

    # Inferencia 100% con GPT-6 Luna
    resp: LLMResponse = default_luna_client.generate(messages=messages, temperature=0.2, max_tokens=4000)

    return {
        "dictamen": resp.content,
        "razonamiento": resp.reasoning,
        "parche_sql": resp.extract_sql_patch(),
        "iteracion": iteracion,
        "modo": resp.mode
    }
