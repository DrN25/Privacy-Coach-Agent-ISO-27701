import os
import sys
import json
from typing import Dict, Any, List

try:
    from .graph_engine import PIMSGraphEngine
except ImportError:
    from backend.graph_engine import PIMSGraphEngine

class KnowledgeBridge:
    def __init__(self):
        self.engine = PIMSGraphEngine()
        self.controls_count = len(self.engine.controls_map)
        self.sanciones = self.engine.sanctions_dataset

    def extraer_subgrafo_control(self, control_id: str) -> Dict[str, Any]:
        ctrl = self.engine.get_control(control_id)
        if not ctrl:
            for cid, c in self.engine.controls_map.items():
                if control_id.lower() in cid.lower() or control_id.lower() in c.get("title", "").lower():
                    ctrl = c
                    control_id = cid
                    break

        if not ctrl:
            return {"control": control_id, "detalles": {}, "principios": [], "sanciones_anpd": [], "subgrafo_nodos": []}

        principios_vinculados = []
        for p_str in ctrl.get("iso29100_principles", []):
            p_id = p_str.split(":")[0].strip()
            princ = self.engine.get_principle(p_id)
            if princ:
                principios_vinculados.append(princ)

        # Precedentes sancionadores ANPD vinculados al control
        sanciones_raw = self.engine.find_sanctions_for_control(ctrl["id"], limit=3)
        sanciones_anpd = []
        for s in sanciones_raw:
            res_list = s.get("resoluciones", [])
            infracciones = []
            for inf in s.get("infracciones", [])[:2]:
                if isinstance(inf, dict):
                    infracciones.append(f"{inf.get('articulo_referencia', '')}: {inf.get('texto_infraccion', '')[:110]}")
                elif isinstance(inf, str):
                    infracciones.append(inf[:110])
            sanciones_anpd.append({
                "id": s.get("id"),
                "entidad": s.get("entidad"),
                "resolucion": res_list[0] if res_list else "Resolución Directoral ANPD",
                "sector": s.get("sector"),
                "multa_total_uit": s.get("multa_total_uit", 0),
                "infracciones": infracciones
            })

        sub_nodos = [
            {
                "id": ctrl["id"],
                "tipo": "ISO27701_CONTROL",
                "label": f"{ctrl['id']}: {ctrl['title']}",
                "rol": ctrl.get("role"),
                "peru_bridge": ctrl.get("peru_legal_bridge", {})
            }
        ]
        for p in principios_vinculados:
            sub_nodos.append({
                "id": p["id"],
                "tipo": "ISO29100_PRINCIPLE",
                "label": f"{p['id']}: {p.get('name', p.get('title', 'Principio'))}",
                "ley29733": p.get("ley_29733_principle", "")
            })

        for sc in sanciones_anpd:
            sub_nodos.append({
                "id": f"ANPD-{sc['id']}",
                "tipo": "ANPD_SANCTION",
                "label": f"ANPD: {sc['entidad']} ({sc['multa_total_uit']} UIT)",
                "resolucion": sc["resolucion"],
                "sector": sc["sector"]
            })

        return {
            "control": control_id,
            "detalles": ctrl,
            "principios": principios_vinculados,
            "sanciones_anpd": sanciones_anpd,
            "subgrafo_nodos": sub_nodos
        }

knowledge_bridge = KnowledgeBridge()
