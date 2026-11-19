"""
Subagente Inspector Documental IA (Document Inspector Agent).
Interpreta documentos SQL, PDF, DOCX, MD y TXT cargados en el Inspector
y detecta brechas o no conformidades adicionales contra los 78 controles oficiales ISO/IEC 27701:2025.
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.rules_catalog import VALOR_UIT_PEN
from ..infrastructure.llm_client import default_luna_client
from ..infrastructure.repository import repository
from ..knowledge_bridge import knowledge_bridge

logger = logging.getLogger("pims.doc_inspector_agent")


def _compact_controls_catalog() -> str:
    items = []
    for cid, c in sorted(knowledge_bridge.engine.controls_map.items()):
        items.append(f"{cid}: {c.get('title', '')}")
    return "\n".join(items)


def _normalize_control_id(raw_ctrl: str) -> Optional[str]:
    cid = (raw_ctrl or "").strip().upper()
    if cid.startswith("B."):
        cid = "A." + cid[2:]
    if cid in knowledge_bridge.engine.controls_map:
        return cid
    return None


def _normalize_risk(raw_risk: str) -> str:
    up = (raw_risk or "MEDIO").strip().upper()
    if "CRIT" in up or "MUY" in up:
        return "CRÍTICO"
    if "ALT" in up or "GRAV" in up:
        return "ALTO"
    if "BAJ" in up or "LEV" in up:
        return "BAJO"
    return "MEDIO"


def analizar_documentos_con_ia(archivo_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Ejecuta el subagente IA sobre los documentos/esquemas cargados en el Inspector
    para identificar el tipo de documento y detectar hallazgos más allá de R-001..R-007.
    """
    vista = repository.obtener_vista_completa_base_datos()
    archivos = vista.get("archivos", [])
    if archivo_id is not None:
        archivos = [a for a in archivos if a["id"] == archivo_id]

    if not archivos:
        return {
            "ai_executed": False,
            "tipo_documento": "Sin documentos",
            "resumen_ejecutivo": "No hay archivos indexados en el Inspector para analizar.",
            "hallazgos_nuevos": 0,
            "hallazgos": [],
        }

    file_ids = {a["id"] for a in archivos}
    target_names = {a["nombre_archivo"] for a in archivos}

    cols = [
        c for c in vista.get("inventario", [])
        if c.get("archivo_id") in file_ids
    ][:80]
    clausulas = [
        cl for cl in vista.get("clausulas", [])
        if cl.get("archivo_id") in file_ids or cl.get("documento") in target_names
    ][:60]

    context_parts = ["ARCHIVOS EN INSPECTOR:"]
    for a in archivos[:10]:
        context_parts.append(f"- {a['nombre_archivo']} ({a['tipo_archivo']}): {a.get('resumen_analisis', '')}")

    if cols:
        context_parts.append("\nCOLUMNAS SQL DETECTADAS:")
        for c in cols:
            context_parts.append(f"- {c['nombre_tabla']}.{c['nombre_columna']} ({c['tipo_sql']}) -> {c['categoria_sensible']}")

    if clausulas:
        context_parts.append("\nCLÁUSULAS / PÁRRAFOS EXTRAÍDOS:")
        for cl in clausulas:
            txt = (cl.get("texto_clausula") or "").replace("\n", " ")[:320]
            context_parts.append(f"- [{cl.get('documento')}] {cl.get('titulo_clausula')}: {txt}")

    existentes = vista.get("hallazgos", [])
    existentes_txt = "\n".join(
        f"- {h['codigo_regla']} ({h['control_iso27701']}): {h['titulo']} [{h['elemento_afectado']}]"
        for h in existentes[:20]
    ) or "Ninguno previo"

    prompt = (
        "Analiza el siguiente contenido documental/SQL cargado en el Inspector PIMS UNSA.\n"
        "1) Identifica el tipo de documento y redacta un breve resumen ejecutivo (máx 2 frases).\n"
        "2) Detecta hasta 5 hallazgos de brechas de privacidad o no conformidades REALES frente a los 78 controles oficiales "
        "ISO/IEC 27701:2025 (sin repetir los ya detectados).\n\n"
        f"HALLAZGOS YA DETECTADOS:\n{existentes_txt}\n\n"
        f"CONTENIDO CARGADO:\n{chr(10).join(context_parts)[:7500]}\n\n"
        f"CATÁLOGO DE 78 CONTROLES VÁLIDOS:\n{_compact_controls_catalog()}\n\n"
        "Responde ÚNICAMENTE con un objeto JSON válido con estas claves exactas:\n"
        '{"tipo_documento": "...", "resumen_ejecutivo": "...", "hallazgos": ['
        '{"control_iso27701": "A.3.31", "titulo": "...", "descripcion": "...", '
        '"elemento_afectado": "...", "origen_archivo": "...", "nivel_riesgo": "CRÍTICO|ALTO|MEDIO|BAJO", "recomendacion": "..."}]}'
    )

    resp = default_luna_client.generate(
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres el Subagente Inspector Documental PIMS (ISO/IEC 27701:2025). "
                    "Nunca inventes códigos de control fuera del catálogo oficial. Responde SOLO JSON válido."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.15,
        max_tokens=1100,
    )

    if resp.mode == "error":
        return {
            "ai_executed": False,
            "tipo_documento": ", ".join(sorted({a["tipo_archivo"] for a in archivos})),
            "resumen_ejecutivo": resp.content,
            "hallazgos_nuevos": 0,
            "hallazgos": [],
        }

    match = re.search(r"\{.*\}", resp.content or "", re.DOTALL)
    if not match:
        return {
            "ai_executed": False,
            "tipo_documento": ", ".join(sorted({a["tipo_archivo"] for a in archivos})),
            "resumen_ejecutivo": "El subagente IA no devolvió una estructura JSON válida.",
            "hallazgos_nuevos": 0,
            "hallazgos": [],
        }

    try:
        parsed = json.loads(match.group(0))
    except Exception:
        return {
            "ai_executed": False,
            "tipo_documento": ", ".join(sorted({a["tipo_archivo"] for a in archivos})),
            "resumen_ejecutivo": "No fue posible parsear la salida JSON del subagente IA.",
            "hallazgos_nuevos": 0,
            "hallazgos": [],
        }

    existing_keys = {
        (h.get("control_iso27701"), (h.get("titulo") or "").strip().lower()[:60])
        for h in existentes
    }

    default_origin = archivos[0]["nombre_archivo"]
    inserted: List[Dict[str, Any]] = []
    uit_map = {"CRÍTICO": 10.0, "ALTO": 6.0, "MEDIO": 3.0, "BAJO": 1.5}

    for item in parsed.get("hallazgos") or []:
        if not isinstance(item, dict):
            continue
        ctrl_id = _normalize_control_id(str(item.get("control_iso27701") or ""))
        if not ctrl_id:
            continue
        titulo = str(item.get("titulo") or "").strip()
        desc = str(item.get("descripcion") or "").strip()
        elem = str(item.get("elemento_afectado") or default_origin).strip()
        if not titulo or not desc:
            continue

        dedup_key = (ctrl_id, titulo.lower()[:60])
        if dedup_key in existing_keys:
            continue
        existing_keys.add(dedup_key)

        risk = _normalize_risk(str(item.get("nivel_riesgo") or "MEDIO"))
        ctrl_obj = knowledge_bridge.engine.get_control(ctrl_id) or {}
        bridge = ctrl_obj.get("peru_legal_bridge", {}) if isinstance(ctrl_obj, dict) else {}
        uit = uit_map.get(risk, 3.0)
        origen = str(item.get("origen_archivo") or default_origin).strip()
        if origen not in target_names:
            origen = default_origin

        hallazgo_row = {
            "codigo_regla": f"IA-{ctrl_id}",
            "titulo": titulo,
            "descripcion": desc,
            "nivel_riesgo": risk,
            "elemento_afectado": elem,
            "origen_archivo": origen,
            "control_iso27701": ctrl_id,
            "principio_iso29100": ", ".join(ctrl_obj.get("iso29100_principles", [])[:2]) or "ISO/IEC 27701:2025",
            "articulo_ley29733": bridge.get("ley_29733") or "Ley N° 29733 (Evaluación DPO)",
            "directiva_seguridad": bridge.get("directiva_seguridad") or f"ISO/IEC 27701:2025 Control {ctrl_id}",
            "multa_estimada_uit": uit,
            "multa_estimada_pen": round(uit * VALOR_UIT_PEN, 2),
            "precedente_anpd": f"Hallazgo Subagente IA — {item.get('recomendacion') or ctrl_obj.get('title', '')}",
            "fecha_deteccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        new_id = repository.insertar_hallazgo(hallazgo_row)
        hallazgo_row["id"] = new_id
        inserted.append(hallazgo_row)

    return {
        "ai_executed": True,
        "tipo_documento": parsed.get("tipo_documento") or default_origin,
        "resumen_ejecutivo": parsed.get("resumen_ejecutivo") or "Análisis documental completado.",
        "hallazgos_nuevos": len(inserted),
        "hallazgos": inserted,
    }
