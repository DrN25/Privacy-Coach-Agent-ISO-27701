import os
import sys
import json
from typing import Dict, Any, List

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from scripts.graph_engine import PIMSGraphEngine

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
            return {"control": control_id, "detalles": {}, "subgrafo_nodos": []}

        principios_vinculados = []
        for p_str in ctrl.get("iso29100_principles", []):
            p_id = p_str.split(":")[0].strip()
            princ = self.engine.get_principle(p_id)
            if princ:
                principios_vinculados.append(princ)

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

        return {
            "control": control_id,
            "detalles": ctrl,
            "principios": principios_vinculados,
            "subgrafo_nodos": sub_nodos
        }

knowledge_bridge = KnowledgeBridge()
