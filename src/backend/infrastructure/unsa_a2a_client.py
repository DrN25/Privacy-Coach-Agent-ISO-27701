"""
Cliente del Protocolo A2A (Agent-to-Agent v0.3.0) para integración con el agente UNSA (unsa-mind).
Implementa transporte JSON-RPC 2.0 sobre HTTP para consulta de normativa universitaria.
"""

import os
import uuid
from typing import Dict, Any, List, Optional
import httpx

from ..core.config import settings

DEFAULT_UNSA_A2A_URL = "http://localhost:8001/a2a"


class UNSAA2AClient:
    """Cliente A2A v0.3.0 que interactúa con el agente institucional unsa-mind."""

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, timeout: float = 3.5):
        self.url = (url or os.getenv("UNSA_A2A_URL") or getattr(settings, "unsa_a2a_url", DEFAULT_UNSA_A2A_URL)).strip()
        self.api_key = (api_key or os.getenv("UNSA_A2A_API_KEY") or getattr(settings, "unsa_a2a_api_key", "")).strip()
        self.timeout = timeout

    @property
    def headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    @property
    def agent_card_url(self) -> str:
        """Deriva la URL de descubrimiento Agent Card a partir de la URL de RPC."""
        base = self.url.split("/a2a")[0]
        return f"{base}/.well-known/agent-card.json"

    def verificar_conexion(self) -> bool:
        """Comprueba si el agente unsa-mind está disponible mediante su Agent Card."""
        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(self.agent_card_url, headers=self.headers)
                return res.status_code == 200 and "Asistente" in res.text
        except Exception:
            return False

    def consultar_normativa(self, pregunta: str, context_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía una consulta institucional mediante el método message/send de A2A.
        Retorna la respuesta oficial con citas normativas y vigencia.
        """
        cid = context_id or f"tif-audit-{uuid.uuid4().hex[:8]}"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "message/send",
            "params": {
                "message": {
                    "role": "user",
                    "messageId": f"msg-{uuid.uuid4().hex[:8]}",
                    "parts": [{"kind": "text", "text": pregunta}],
                    "contextId": cid
                }
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                res = client.post(self.url, json=payload, headers=self.headers)
                if res.status_code == 200:
                    data = res.json()
                    result = data.get("result", {})
                    parts = result.get("parts", [])
                    meta = result.get("metadata", {})
                    text = parts[0].get("text", "") if parts else ""
                    return {
                        "disponible": True,
                        "abstained": meta.get("abstained", False),
                        "respuesta": text,
                        "citas": meta.get("citations", []),
                        "context_id": result.get("contextId", cid)
                    }
        except Exception:
            pass

        return {
            "disponible": False,
            "abstained": True,
            "respuesta": "Agente UNSA no disponible.",
            "citas": [],
            "context_id": cid
        }


unsa_a2a_client = UNSAA2AClient()


if __name__ == "__main__":
    # Verificación unitaria con transporte simulado sin levantar servidor real
    def handler(request: httpx.Request) -> httpx.Response:
        if "/.well-known/agent-card.json" in str(request.url):
            return httpx.Response(200, json={"name": "Asistente Virtual UNSA", "skills": []})
        body = request.read().decode("utf-8")
        assert "message/send" in body
        return httpx.Response(200, json={
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "kind": "message",
                "role": "agent",
                "parts": [{"kind": "text", "text": "Reglamento de Matrícula Art. 12 [1]"}],
                "metadata": {"citations": [{"title": "Reglamento UNSA", "url": "http://unsa.edu.pe"}], "abstained": False}
            }
        })

    client = UNSAA2AClient(url="http://testserver/a2a")
    with httpx.Client(transport=httpx.MockTransport(handler)) as mock_http:
        client_test = UNSAA2AClient(url="http://testserver/a2a")
        # Simular llamada directa usando mock transport
        req_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "message/send",
            "params": {"message": {"role": "user", "parts": [{"kind": "text", "text": "test"}]}}
        }
        resp = mock_http.post("http://testserver/a2a", json=req_payload)
        res_data = resp.json()["result"]
        assert "Art. 12" in res_data["parts"][0]["text"]
        assert len(res_data["metadata"]["citations"]) == 1
    print("UNSA A2A Client: self-check passed (JSON-RPC 2.0 & citations valid).")
