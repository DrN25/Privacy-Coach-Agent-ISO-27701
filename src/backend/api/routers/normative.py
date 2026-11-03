"""
Router de Consultas Normativas y Grafo de Conocimiento (PIMS & Redes Legales).
Endpoints: /api/subgraph/{control_id}, /api/legal-reference/{tipo}/{ref_id}.
"""

import os
import json
from fastapi import APIRouter, HTTPException

from ...knowledge_bridge import knowledge_bridge

router = APIRouter(tags=["Normative"])


@router.get("/api/subgraph/{control_id}")
def get_subgraph(control_id: str):
    return knowledge_bridge.extraer_subgrafo_control(control_id)


@router.get("/api/legal-reference/{tipo}/{ref_id}")
def get_legal_reference(tipo: str, ref_id: str):
    """
    Devuelve contenido original de controles ISO 27701, artículos de Ley 29733 o sanciones ANPD.
    Acepta alias: 'control' | 'iso27701', 'articulo' | 'ley29733', 'sancion' | 'anpd'.
    """
    tipo_lower = tipo.lower()
    if tipo_lower in ["control", "iso27701", "iso_27701", "iso"]:
        tipo_normalizado = "control"
    elif tipo_lower in ["articulo", "ley29733", "ley_29733", "ley"]:
        tipo_normalizado = "articulo"
    elif tipo_lower in ["sancion", "anpd", "caso"]:
        tipo_normalizado = "sancion"
    else:
        raise HTTPException(status_code=400, detail="Tipo debe ser 'control', 'articulo' o 'sancion'.")

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    datasets_dir = os.path.join(base_dir, "knowledge_base", "datasets")
    if not os.path.exists(datasets_dir):
        datasets_dir = os.path.join(os.path.dirname(base_dir), "knowledge_base", "datasets")

    if tipo_normalizado == "control":
        ctrl = knowledge_bridge.engine.get_control(ref_id)
        if not ctrl:
            for k, v in getattr(knowledge_bridge.engine, "controls_map", {}).items():
                if ref_id.lower() == k.lower() or ref_id.replace("A.", "").lower() == k.replace("A.", "").lower():
                    ctrl = v
                    ref_id = k
                    break

        if not ctrl:
            raise HTTPException(status_code=404, detail=f"Control ISO {ref_id} no encontrado.")

        principios = []
        for p_str in ctrl.get("iso29100_principles", []):
            p_id = p_str.split(":")[0].strip()
            princ = knowledge_bridge.engine.get_principle(p_id)
            if princ:
                principios.append(princ)

        bridge = ctrl.get("peru_legal_bridge", {})
        texto_legal = bridge.get("ley_29733", "")
        if bridge.get("ds_003_2013_jus"):
            texto_legal += f"\n\nReglamento: {bridge['ds_003_2013_jus']}"

        return {
            "tipo": "control",
            "control_id": ctrl.get("id") or ref_id,
            "titulo": f"Control {ctrl.get('id', ref_id)}: {ctrl.get('title', 'Control de Privacidad')}",
            "nombre": f"Control {ctrl.get('id', ref_id)}: {ctrl.get('title', 'Control de Privacidad')}",
            "texto_oficial": texto_legal or ctrl.get("title", ""),
            "descripcion": f"Estándar {ctrl.get('standard', 'ISO/IEC 27701:2025')} - Rol: {ctrl.get('role', 'Controller/Processor')}",
            "guia_implementacion": bridge.get("directiva_seguridad", "Aplicación de controles técnicos y organizativos obligatorios."),
            "data": ctrl,
            "principios_vinculados": principios
        }

    elif tipo_normalizado == "articulo":
        ley_path = os.path.join(datasets_dir, "ley_29733_articulos.json")
        if not os.path.exists(ley_path):
            raise HTTPException(status_code=404, detail="Dataset de Ley 29733 no encontrado.")
        with open(ley_path, "r", encoding="utf-8") as f:
            ley_data = json.load(f)

        clean_digits = "".join(filter(str.isdigit, ref_id))
        articulo = ley_data.get("articulos", {}).get(ref_id)
        if not articulo and clean_digits:
            articulo = ley_data.get("articulos", {}).get(f"Art_{clean_digits}")
            if articulo:
                ref_id = f"Art_{clean_digits}"

        if not articulo:
            for k, v in ley_data.get("articulos", {}).items():
                if ref_id.replace("Art. ", "Art_").replace("Art ", "Art_") == k or str(v.get("articulo")) == ref_id:
                    articulo = v
                    ref_id = k
                    break

        if not articulo:
            raise HTTPException(status_code=404, detail=f"Artículo {ref_id} no encontrado.")

        return {
            "tipo": "articulo",
            "articulo": str(articulo.get("articulo", ref_id)),
            "titulo": f"Artículo {articulo.get('articulo', ref_id)} - {articulo.get('titulo', 'Ley N° 29733')}",
            "nombre": f"Artículo {articulo.get('articulo', ref_id)} - {articulo.get('titulo', 'Ley N° 29733')}",
            "texto_oficial": articulo.get("texto", ""),
            "descripcion": articulo.get("texto", ""),
            "guia_implementacion": "Mandato legal imperativo supervisado por la Autoridad Nacional de Protección de Datos Personales (ANPD Perú).",
            "data": articulo
        }

    elif tipo_normalizado == "sancion":
        try:
            sid = int(ref_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de sanción debe ser numérico.")
        for s in knowledge_bridge.engine.sanctions_dataset:
            if s.get("id") == sid:
                return {
                    "tipo": "sancion",
                    "id": sid,
                    "titulo": s.get("resolucion", f"Precedente Sancionador #{sid}"),
                    "nombre": s.get("resolucion", f"Precedente Sancionador #{sid}"),
                    "texto_oficial": s.get("resumen") or s.get("conducta_infractora") or "",
                    "descripcion": s.get("conducta_infractora") or "",
                    "guia_implementacion": f"Multa firme ANPD: {s.get('multa_uit', 'N/A')} UIT impuesta a {s.get('entidad', 'entidad supervisada')}.",
                    "data": s
                }
        raise HTTPException(status_code=404, detail=f"Sanción {ref_id} no encontrada.")
