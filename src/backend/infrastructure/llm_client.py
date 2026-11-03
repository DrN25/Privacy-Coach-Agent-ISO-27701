"""
Cliente de Inferencia LLM unificado para OpenRouter.
Configurado para GPT-6 Luna (openai/gpt-6-luna).

Características:
- Utiliza `httpx` para HTTP síncrono con pooling y retries exponenciales.
- Modelo único por defecto: openai/gpt-6-luna.
- Separación limpia entre llamadas de red y lógica de agentes (favorece testing unitario e inyección).
"""

import os
import re
import json
import time
from typing import Dict, Any, List, Optional
import httpx
from ..core.config import settings

DEFAULT_MODEL = "openai/gpt-6-luna"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMResponse:
    def __init__(self, content: str, reasoning: str = "", raw: Optional[Dict[str, Any]] = None, mode: str = "openrouter"):
        self.content = content
        self.reasoning = reasoning
        self.raw = raw or {}
        self.mode = mode

    def extract_sql_patch(self) -> str:
        """Extrae de forma robusta cualquier bloque SQL transaccional o DDL del dictamen."""
        content = self.content
        if not content:
            return ""

        # Intento 1: Buscar bloque de código ```sql ... ```
        sql_match = re.search(
            r"```(?:sql|SQL)?\s*(ALTER TABLE.*?|CREATE EXTENSION.*?|UPDATE .*?|CREATE TABLE.*?|BEGIN.*?)\s*```",
            content,
            re.DOTALL | re.IGNORECASE
        )
        if sql_match:
            return sql_match.group(1).strip()

        # Intento 2: Buscar cualquier bloque delimitado que contenga comandos SQL críticos
        for tag in ["```sql", "```SQL", "```"]:
            if tag in content:
                partes = content.split(tag)
                for chunk in partes[1:]:
                    candidate = chunk.split("```")[0].strip()
                    if any(k in candidate.upper() for k in ["ALTER TABLE", "UPDATE ", "CREATE ", "PGP_SYM_ENCRYPT", "DROP "]):
                        return candidate
        return ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "reasoning": self.reasoning,
            "sql_patch": self.extract_sql_patch(),
            "mode": self.mode
        }


class LunaLLMClient:
    """Cliente para GPT-6 Luna a través de OpenRouter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout_seconds: float = 60.0
    ):
        self._explicit_api_key = api_key
        self._explicit_base_url = base_url
        self._explicit_model = model
        self.timeout_seconds = timeout_seconds

    @property
    def api_key(self) -> str:
        key = self._explicit_api_key or os.getenv("OPENROUTER_API_KEY") or settings.openrouter_api_key or ""
        return key.strip()

    @property
    def base_url(self) -> str:
        return (self._explicit_base_url or os.getenv("OPENROUTER_URL") or settings.openrouter_url or OPENROUTER_BASE_URL).strip()

    @property
    def model(self) -> str:
        return (self._explicit_model or os.getenv("OPENROUTER_MODEL") or settings.openrouter_model or DEFAULT_MODEL).strip()

    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4000,
        extra_payload: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Ejecuta la inferencia contra GPT-6 Luna con retries exponenciales en fallos de red.
        """
        resolved_key = self.api_key
        if not resolved_key:
            return LLMResponse(
                content="No fue posible generar el dictamen mediante GPT-6 Luna: OPENROUTER_API_KEY no está configurada o está vacía en el archivo .env. Verifique su archivo de configuración.",
                reasoning="",
                raw={"error": "OPENROUTER_API_KEY missing or empty"},
                mode="error"
            )

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if extra_payload:
            payload.update(extra_payload)

        headers = {
            "Authorization": f"Bearer {resolved_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://unsa.edu.pe/auditoria-tif",
            "X-Title": "TIF Auditoria PIMS UNSA"
        }

        max_intentos = 3
        ultimo_error: Optional[Exception] = None

        with httpx.Client(timeout=self.timeout_seconds) as client:
            for intento in range(max_intentos):
                try:
                    resp = client.post(self.base_url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [{}])
                        if choices:
                            msg = choices[0].get("message", {})
                            content = msg.get("content") or ""
                            reasoning = msg.get("reasoning") or msg.get("reasoning_details") or ""
                            if not content.strip() and reasoning and isinstance(reasoning, str):
                                content = f"### Dictamen Técnico Pericial\n\n{reasoning.strip()}"
                            return LLMResponse(content=content, reasoning=str(reasoning), raw=data, mode="openrouter")

                    # Error de cuota o rate limit
                    if resp.status_code in [429, 502, 503, 504]:
                        time.sleep(1.5 * (intento + 1))
                        continue
                    else:
                        resp.raise_for_status()

                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    ultimo_error = e
                    if intento < max_intentos - 1:
                        time.sleep(1.5 * (intento + 1))
                        continue
                except Exception as e:
                    ultimo_error = e
                    break

        # Fallback estructurado en caso de error de red o falta de API key
        err_msg = str(ultimo_error) if ultimo_error else "Error desconocido de API"
        return LLMResponse(
            content=f"No fue posible generar el dictamen mediante GPT-6 Luna ({err_msg}). Verifique la conexión local y la cuota de API.",
            reasoning="",
            raw={"error": err_msg},
            mode="error"
        )


# Singleton reutilizable por defecto
default_luna_client = LunaLLMClient()


if __name__ == "__main__":
    # Autochequeo: comprobar extracción de SQL y tipado sin llamadas de red reales
    dummy = LLMResponse(
        content="Dictamen pericial...\n```sql\nBEGIN;\nALTER TABLE cuentas_usuario DROP COLUMN token_secreto;\nCOMMIT;\n```\nFin.",
        reasoning="Pensamiento"
    )
    if "BEGIN;" not in dummy.extract_sql_patch():
        raise ValueError("Error extrayendo SQL transaccional")
    if dummy.to_dict()["mode"] != "openrouter":
        raise ValueError("Modo incorrecto en to_dict")
    print("LLM Client: self-check passed (parsing & SQL extraction valid).")
