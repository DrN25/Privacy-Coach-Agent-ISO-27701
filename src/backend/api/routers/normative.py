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
    tipo: 'control' | 'articulo' | 'sancion'
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    datasets_dir = os.path.join(base_dir, "knowledge_base", "datasets")
    if not os.path.exists(datasets_dir):
        datasets_dir = os.path.join(os.path.dirname(base_dir), "knowledge_base", "datasets")

    if tipo == "control":
        ctrl = knowledge_bridge.engine.get_control(ref_id)
        if not ctrl:
            raise HTTPException(status_code=404, detail=f"Control {ref_id} no encontrado.")
        principios = []
        for p_str in ctrl.get("iso29100_principles", []):
            p_id = p_str.split(":")[0].strip()
            princ = knowledge_bridge.engine.get_principle(p_id)
            if princ:
                principios.append(princ)
        return {
            "tipo": "control",
            "data": ctrl,
            "principios_vinculados": principios
        }

    elif tipo == "articulo":
        ley_path = os.path.join(datasets_dir, "ley_29733_articulos.json")
        if not os.path.exists(ley_path):
            raise HTTPException(status_code=404, detail="Dataset de Ley 29733 no encontrado.")
        with open(ley_path, "r", encoding="utf-8") as f:
            ley_data = json.load(f)
        articulo = ley_data.get("articulos", {}).get(ref_id)
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
            "id": ref_id,
            "data": articulo
        }

    elif tipo == "sancion":
        try:
            sid = int(ref_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de sanción debe ser numérico.")
        for s in knowledge_bridge.engine.sanctions_dataset:
            if s.get("id") == sid:
                return {
                    "tipo": "sancion",
                    "data": s
                }
        raise HTTPException(status_code=404, detail=f"Sanción {ref_id} no encontrada.")

    else:
        raise HTTPException(status_code=400, detail="Tipo debe ser 'control', 'articulo' o 'sancion'.")
