"""
Nodo Agente Normativo (ISO 27701 & ANPD Jurisprudence Agent).
Consulta el grafo NetworkX y la base de 588 resoluciones sancionadoras de la ANPD.
"""

from typing import Dict, Any, List, Optional
from .state import AuditState
from ..graph_engine import PIMSGraphEngine

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

    # Formatear líneas de precedentes ANPD
    anpd_lineas: List[str] = []
    for s in sanciones:
        raw_infr = s.get("infracciones", [])
        infr_tokens = []
        if isinstance(raw_infr, list):
            for item in raw_infr:
                if isinstance(item, dict):
                    infr_tokens.append(f"{item.get('articulo_referencia', '')} - {item.get('texto_infraccion', '')[:80]}")
                elif isinstance(item, str):
                    infr_tokens.append(item[:80])
        else:
            infr_tokens.append(str(raw_infr)[:80])
        infr_str = "; ".join(infr_tokens)
        anpd_lineas.append(
            f"  * {s.get('entidad')} | Res: {s.get('resolucion')} | Sector: {s.get('sector')} | Multa: {s.get('multa_total_uit')} UIT | Infracción: {infr_str}"
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

    return {
        "subgrafo_normativo": subgrafo,
        "precedentes_anpd": sanciones,
        "expediente_texto": expediente
    }
