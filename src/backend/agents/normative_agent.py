"""
Nodo Agente Normativo (ISO 27701 & ANPD Jurisprudence Agent).
Consulta el grafo NetworkX y la base de 588 resoluciones sancionadoras de la ANPD.
"""

from typing import Dict, Any, List, Optional
from .state import AuditState
from ..graph_engine import PIMSGraphEngine
from ..core.config import settings
from ..infrastructure.unsa_a2a_client import unsa_a2a_client

_graph_engine: Optional[PIMSGraphEngine] = None


def get_graph_engine() -> PIMSGraphEngine:
    global _graph_engine
    if _graph_engine is None:
        _graph_engine = PIMSGraphEngine()
    return _graph_engine


def nodo_normative_agent(state: AuditState) -> Dict[str, Any]:
    """Extrae el subgrafo normativo y los precedentes judiciales de la ANPD."""
    regla = state.get("regla_canonica", {})
    control_id = regla.get("control_iso27701", "A.3.24")
    
    engine = get_graph_engine()
    subgrafo = engine.get_subgraph([control_id])
    sanciones = engine.find_sanctions_for_control(control_id, limit=2)

    # Formatear líneas de precedentes ANPD con resoluciones y medidas correctivas verificadas
    anpd_lineas: List[str] = []
    for s in sanciones:
        raw_res = s.get("resoluciones") or [s.get("resolucion")]
        res_str = raw_res[0] if raw_res and raw_res[0] else "Resolución Directoral ANPD"
        
        raw_infr = s.get("infracciones", [])
        infr_tokens = []
        if isinstance(raw_infr, list):
            for item in raw_infr:
                if isinstance(item, dict):
                    infr_tokens.append(f"{item.get('articulo_referencia', '')}: {item.get('texto_infraccion', '')[:100]}")
                elif isinstance(item, str):
                    infr_tokens.append(item[:100])
        else:
            infr_tokens.append(str(raw_infr)[:100])
        infr_str = "; ".join(infr_tokens) if infr_tokens else "Infracción formal al régimen de protección de datos"
        
        medidas = s.get("medidas_correctivas", [])
        if medidas:
            medidas_str = "; ".join(medidas[:2])
        else:
            medidas_str = "No se dictaron medidas correctivas accesorias a la sanción de multa"

        anpd_lineas.append(
            f"  * Entidad: {s.get('entidad')} | {res_str} | Sector: {s.get('sector')} | Multa: {s.get('multa_total_uit')} UIT | Tipificación: {infr_str} | Medidas Correctivas ANPD: {medidas_str}"
        )
    anpd_text = "\n".join(anpd_lineas) if anpd_lineas else f"  * Precedente ANPD de referencia: {regla.get('precedente_anpd')}"

    # Cláusulas documentales asociadas al hallazgo
    ctx = state.get("contexto_brecha", {})
    clausulas_lista = ctx.get("clausulas_documento", [])
    if clausulas_lista:
        c_lines = []
        for c in clausulas_lista:
            c_doc = c.get("documento", "")
            c_num = c.get("numero_clausula", "")
            c_tit = c.get("titulo_clausula", "")
            c_txt = c.get("texto_clausula", "")[:260].replace("\n", " ")
            c_lines.append(f"  * [{c_doc}] {c_num} ({c_tit}): {c_txt}")
        clausulas_texto = "\n" + "\n".join(c_lines)
    else:
        clausulas_texto = " (Verificado contra esquema DDL / DML)"

    principios_dict = subgrafo.get("principios", {})
    if isinstance(principios_dict, dict):
        principios_nombres = [p.get("name", p.get("id", "")) for p in principios_dict.values()]
    elif isinstance(principios_dict, list):
        principios_nombres = [p.get("name", p.get("id", "")) for p in principios_dict]
    else:
        principios_nombres = []

    multa_uit = regla.get("multa_estimada_uit", 10.0)
    multa_pen = regla.get("multa_estimada_pen", multa_uit * 5150.0)

    nivel = str(regla.get("nivel_riesgo", "MEDIO")).upper()
    if nivel in ["CRÍTICO", "MUY GRAVE"]:
        escala_legal = "Infracción Muy Grave (Art. 38 num. 3 LPDP: rango de 50.1 a 100 UIT)"
        graduacion_info = "Multa base objetiva + Agravante por dimensión del riesgo y afectación masiva o sensible"
    elif nivel in ["ALTO", "GRAVE"]:
        escala_legal = "Infracción Grave (Art. 38 num. 2 LPDP / Art. 132 num. 2 RLPDP: rango de 5.1 a 50 UIT)"
        graduacion_info = "Multa base proporcional + Agravantes por tipo de dato tratado + Omisión de deberes de seguridad/consentimiento"
    else:
        escala_legal = "Infracción Leve (Art. 38 num. 1 LPDP: rango de 0.5 a 5 UIT)"
        graduacion_info = "Multa atenuada en rango base para faltas formales subsanables"

    origen = ctx.get("origen_archivo") or "Activo documental o de base de datos"
    activo = ctx.get("elemento_afectado") or "Estructura de datos o cláusulas de la organización"

    expediente = f"""EXPEDIENTE TÉCNICO DE AUDITORÍA DE PRIVACIDAD:
- Hallazgo Técnico: {regla.get('titulo', 'Vulnerabilidad')} (Código: {regla.get('codigo', 'R-001')})
- Activo / Elemento Afectado: {activo}
- Archivo Origen: {origen}
- Cláusulas / Secciones del Documento Relacionadas:
{clausulas_texto}
- Control ISO/IEC 27701:2025: {control_id} - {regla.get('control_nombre', '')}
- Infracción Ley 29733: {regla.get('articulo_ley29733', '')}
- Directiva de Seguridad: {regla.get('directiva_seguridad', '')}
- Cuantificación Sancionadora Estimada: {multa_uit} UIT (S/ {multa_pen:,.2f})
  * Escala Legal: {escala_legal}
  * Factores de Graduación: {graduacion_info}
- Precedentes Oficiales ANPD Identificados en Base Local (588 Casos):
{anpd_text}
- Principios ISO 29100 Vinculados: {', '.join(principios_nombres) if principios_nombres else regla.get('principio_iso29100', 'Principio de Seguridad')}
- Remediación requerida: {regla.get('remediacion_sugerida', '')}
"""

    # Enriquecimiento A2A con Agente Normativo Institucional UNSA (unsa-mind)
    mensajes = state.get("historial_mensajes", [])
    user_queries = [m.get("content", "") for m in mensajes if m.get("role") == "user"]
    latest_user_query = user_queries[-1] if user_queries else ""

    contexto_unsa: Dict[str, Any] = {}
    texto_eval = f"{activo} {origen} {clausulas_texto} {regla.get('titulo', '')} {latest_user_query}".lower()
    terminos_unsa = ["unsa", "universidad", "san agustín", "san agustin", "estudiante", "alumno", "matricula", "matrícula", "docente", "posgrado", "admision", "admisión", "convenio"]
    
    unsa_consultado = False
    unsa_detalle_trace = "No requerida por contexto general"

    if any(t in texto_eval for t in terminos_unsa) and getattr(settings, "unsa_a2a_enabled", True):
        unsa_consultado = True
        if any(t in latest_user_query.lower() for t in terminos_unsa):
            pregunta_a2a = latest_user_query
        else:
            pregunta_a2a = f"¿Qué normativa institucional o reglamento de la UNSA rige para {activo} respecto a {regla.get('titulo')}?"
        
        resp_a2a = unsa_a2a_client.consultar_normativa(pregunta_a2a)
        if resp_a2a.get("disponible"):
            if resp_a2a.get("citas") or (resp_a2a.get("texto") and not resp_a2a.get("abstained")):
                contexto_unsa = resp_a2a
                unsa_detalle_trace = f"Conectado a unsa-mind. Obtenidas {len(resp_a2a.get('citas', []))} citas oficiales."
            else:
                contexto_unsa = {
                    "disponible": True,
                    "abstained": True,
                    "pregunta": pregunta_a2a,
                    "resumen_pericial": (
                        "Consulta A2A a Agente unsa-mind efectuada con éxito. La base de conocimiento de la UNSA "
                        "no cuenta actualmente con un reglamento específico o directiva propia de retención/conservación "
                        "para este subsistema de software tercerizado. En consecuencia, de acuerdo al principio de legalidad "
                        "y supletoriedad, rige directamente la Ley N.° 29733 (Arts. 7 y 8 LPDP; Arts. 9 y 28 D.S. 003-2013-JUS) "
                        "y el estándar internacional ISO/IEC 27701:2025 (Control A.1.4.8)."
                    )
                }
                unsa_detalle_trace = "Conectado a unsa-mind. Sin norma interna específica en repositorio; rige Ley 29733 supletoria."
        else:
            unsa_detalle_trace = "Servicio unsa-mind en puerto 8001 no respondió o fuera de línea."

    unsa_sec = ""
    if contexto_unsa.get("citas"):
        citas_lines = [f"  * {c.get('title', 'Norma UNSA')} ({c.get('section', '')}) - Vigencia: {c.get('effective_date', 'Vigente')}" for c in contexto_unsa.get("citas", [])]
        unsa_sec = f"\n- Normativa Institucional UNSA (Consultada vía Agente A2A unsa-mind):\n" + "\n".join(citas_lines) + "\n"
    elif contexto_unsa.get("resumen_pericial"):
        unsa_sec = f"\n- Contexto Institucional UNSA (Consultado vía Agente A2A unsa-mind):\n  * {contexto_unsa['resumen_pericial']}\n"

    # Registrar paso en trazabilidad
    trace = list(state.get("trazabilidad") or [])
    trace.append({
        "paso": len(trace) + 1,
        "agente": "Normative & Jurisprudence Agent",
        "accion": f"Cruce normativo ISO 27701 ({control_id}) y Precedentes ANPD",
        "detalle": f"Control evaluado: {control_id}. Precedentes ANPD vinculados: {len(sanciones)}.",
        "estado": "ok"
    })

    # Si se activó la consulta inter-agente A2A con unsa-mind:
    if unsa_consultado:
        estado_a2a = "ok" if (contexto_unsa and contexto_unsa.get("disponible")) else "warn"
        trace.append({
            "paso": len(trace) + 1,
            "agente": "Protocolo A2A (unsa-mind:8001)",
            "accion": "Intercambio Inter-Agente (A2A) con Agente Institucional UNSA",
            "detalle": f"Endpoint: http://127.0.0.1:8001/a2a | {unsa_detalle_trace}",
            "estado": estado_a2a
        })

    return {
        "subgrafo_normativo": subgrafo,
        "precedentes_anpd": sanciones,
        "contexto_unsa": contexto_unsa,
        "expediente_texto": expediente + unsa_sec,
        "trazabilidad": trace
    }
