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

REGLAS ESTRICTAS DE RESPUESTA (RIGOR TÉCNICO PERICIAL, DETERMINISMO Y CERO DUDAS):
1. CERTEZA Y DETERMINISMO PERICIAL: Eres un Auditor Forense Senior y Perito Oficial. Hablas con certeza absoluta y autoridad técnico-jurídica. Queda terminantemente PROHIBIDO usar frases de incertidumbre, duda o auto-desautorización como "no puedo verificar la cita", "conviene validar si corresponde", "según los datos proporcionados no estoy seguro". Todo el expediente, controles ISO 27701 y precedentes ANPD provistos son evidencia pericial oficial admitida.
2. PRECEDENTES Y MEDIDAS CORRECTIVAS ANPD: Cuando expliques resoluciones sancionadoras, utiliza la información provista en el expediente. Si una resolución no registra medidas correctivas accesorias, declara de forma certera y categórica: "La ANPD no impuso medidas correctivas accesorias en este expediente, limitándose a la sanción pecuniaria", sin sembrar dudas en el cliente.
3. CONTEXTO INSTITUCIONAL UNSA: Si el expediente contiene la consulta A2A a unsa-mind, responde con base en esa evidencia oficial: si se indica que la UNSA no cuenta con una norma interna específica en repositorio para este software de terceros, explica con claridad y rigor que rige de manera imperativa y supletoria la Ley 29733 (Arts. 7, 8 y 28 del Reglamento D.S. 003-2013-JUS) y el estándar ISO/IEC 27701:2025.
4. CUANTIFICACIÓN Y GRADUACIÓN DE MULTAS (Art. 39 Ley 29733 y D.S. 016-2024-JUS):
   Explica la escala legal (Infracción Leve 0.5 a 5 UIT, Grave más de 5 a 50 UIT, Muy Grave más de 50 a 100 UIT).
   Desglosa la graduación pericial: Multa base + Agravantes (+25% a +50% por salud/financiero) + Omisión de medidas nivel complejo. 1 UIT = S/ 5,150.
5. PARCHE Y REMEDIACIÓN TÉCNICA: Entrega scripts SQL con bloque transaccional BEGIN; ... COMMIT; o cláusulas contractuales blindadas.
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
    """Genera el dictamen pericial o respuesta operativa SQL + normativa."""
    expediente = state.get("expediente_texto", "")
    historial = state.get("historial_mensajes", [])
    eval_previa = state.get("evaluacion_critica", {})
    iteracion = state.get("iteracion", 0) + 1
    intencion = (state.get("intencion") or "").lower()
    ui_ctx = state.get("ui_context") or {}
    ctx = state.get("contexto_brecha") or {}
    sql_ctx = state.get("sql_context_text") or ""

    extra_blocks: List[str] = []
    if ui_ctx:
        extra_blocks.append(
            f"[CONTEXTO ACTUAL DE INTERFAZ: módulo={ui_ctx.get('active_module', 'incidentes')}, "
            f"incidente_activo={ui_ctx.get('selected_incident_code') or ui_ctx.get('selected_incident_id') or 'ninguno'}, "
            f"pestaña={ui_ctx.get('active_tab', '')}, filtros={ui_ctx.get('active_filters', {})}]"
        )
    if ctx.get("incident_code"):
        mc = ctx.get("corrective_action") or {}
        actions_list = ctx.get("actions") or []
        actions_txt = "; ".join(
            f"[{a.get('action_type')}] {a.get('action_date')} ({a.get('responsible')}): {a.get('description')}"
            for a in actions_list[:8]
        ) or "Ninguna registrada"
        extra_blocks.append(
            "EXPEDIENTE ACTIVO EN PANTALLA:\n"
            f"- Código: {ctx.get('incident_code')} (ID={ctx.get('id')}) | Estado: {ctx.get('status')} | Severidad: {ctx.get('severity')} | Impacto: {ctx.get('impact')}\n"
            f"- Título: {ctx.get('title')}\n"
            f"- Hechos completos: {ctx.get('description') or 'Sin descripción adicional'}\n"
            f"- Control ISO/IEC 27701:2025: {ctx.get('iso27701_control_id')} | Afecta PII: {ctx.get('involves_personal_data')} | Tipo: {ctx.get('incident_type')}\n"
            f"- Activo comprometido: {ctx.get('compromised_system') or 'N/A'} | Titulares afectados: {ctx.get('num_affected_subjects', 0)}\n"
            f"- Responsable: {ctx.get('assigned_to')} | Reportado por: {ctx.get('reported_by')}\n"
            f"- Fecha incidente: {ctx.get('incident_date')} | Fecha detección/apertura: {ctx.get('detection_date')} | Cierre: {ctx.get('resolved_date') or 'Pendiente (Sin cerrar)'}\n"
            f"- Consecuencias: {ctx.get('consequences_summary') or 'En evaluación'}\n"
            f"- Recuperación datos: {ctx.get('data_recovered_status')} ({ctx.get('data_recovered_detail') or ''})\n"
            f"- Notificación ANPD: {'Sí' if ctx.get('anpd_notified') else 'No'} | Ref: {ctx.get('anpd_official_ref') or 'N/A'} | Fecha: {ctx.get('anpd_notified_at') or 'N/A'}\n"
            f"- Precedente y exposición estimada: {ctx.get('precedente_anpd') or 'N/A'} ({ctx.get('multa_estimada_uit', 0)} UIT)\n"
            f"- Acciones A.3.12 ({len(actions_list)}): {actions_txt}\n"
            f"- Medida Correctiva 10.2 (D34): {mc.get('mc_code', 'Sin asignar')} | Estado MC: {mc.get('status', 'N/A')} | Fecha límite: {mc.get('due_date', 'N/A')} | Causa raíz: {mc.get('root_cause', 'N/A')} | Plan: {mc.get('action_to_implement', 'N/A')}"
        )
    if sql_ctx:
        extra_blocks.append(
            f"{sql_ctx}\nINSTRUCCIÓN CRÍTICA DE VERACIDAD: Basa tus conteos, códigos de incidente, fechas, estados y nombres de responsables EXCLUSIVAMENTE en las filas SQL reales mostradas arriba. No inventes ni extrapoles registros."
        )

    base_context = "\n\n".join([b for b in [ "\n\n".join(extra_blocks), "" if intencion == "sql_query" and sql_ctx else expediente ] if b.strip()])

    messages: List[Dict[str, str]] = [{"role": "system", "content": obtener_system_prompt()}]

    if eval_previa and not eval_previa.get("aprobado", False):
        obs = eval_previa.get("observaciones", "")
        retroalimentacion = f"\n\n[OBSERVACIÓN DE REVISIÓN CRÍTICA - ITERACIÓN {iteracion}]:\nCorrige lo siguiente:\n{obs}"
        messages.append({"role": "user", "content": f"{base_context}{retroalimentacion}"})
    else:
        if not historial:
            messages.append({"role": "user", "content": f"{base_context}\n\nRequerimiento: Emitir dictamen pericial completo."})
        elif len(historial) == 1:
            primer_txt = historial[0].get("content", "")
            messages.append({"role": "user", "content": f"{base_context}\n\nRequerimiento del Auditor / Operador:\n{primer_txt}"})
        else:
            primer_txt = historial[0].get("content", "")
            messages.append({"role": "user", "content": f"{base_context}\n\nRequerimiento Inicial:\n{primer_txt}"})
            for m in historial[1:]:
                role = m.get("role", "user")
                if role not in ["user", "assistant"]:
                    role = "user"
                messages.append({"role": role, "content": m.get("content", "")})

    # Inferencia 100% con GPT-6 Luna
    resp: LLMResponse = default_luna_client.generate(messages=messages, temperature=0.2, max_tokens=4000)

    trace = list(state.get("trazabilidad") or [])
    trace.append({
        "paso": len(trace) + 1,
        "agente": "Forensic Coach Agent",
        "accion": "Generación de dictamen y estrategia pericial (GPT-6 Luna)",
        "detalle": f"Modelo: {resp.mode}. Razonamiento pericial estructurado. Longitud: {len(resp.content)} caracteres.",
        "estado": "ok"
    })

    return {
        "dictamen": resp.content,
        "razonamiento": resp.reasoning,
        "parche_sql": resp.extract_sql_patch(),
        "iteracion": iteracion,
        "modo": resp.mode,
        "trazabilidad": trace
    }
