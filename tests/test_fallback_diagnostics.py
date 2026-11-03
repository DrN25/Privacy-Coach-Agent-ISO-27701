import httpx

from backend.agents.dspm_agent import _resolver_codigo_auditoria
from backend.agents.profiler_agent import nodo_profiler_agent
from backend.infrastructure.repository import repository
from backend.infrastructure.unsa_a2a_client import UNSAA2AClient


def test_repository_failure_is_reported_and_agents_keep_fallback(monkeypatch, caplog):
    def fail():
        raise RuntimeError("detalle privado que no debe aparecer en el log")

    monkeypatch.setattr(repository, "obtener_todos_los_hallazgos", fail)
    state = {"contexto_brecha": {"elemento_afectado": "activo"}, "historial_mensajes": []}

    assert _resolver_codigo_auditoria(state) is None
    assert nodo_profiler_agent(state)["perfil_activos"] == []
    assert "No se pudieron correlacionar hallazgos (RuntimeError)" in caplog.text
    assert "No se pudieron obtener activos para perfilar (RuntimeError)" in caplog.text
    assert "detalle privado" not in caplog.text


def test_unsamind_connection_failure_is_reported_without_secrets(monkeypatch, caplog):
    def fail(*args, **kwargs):
        raise httpx.ConnectError("secret-key no debe aparecer en el log")

    monkeypatch.setattr(httpx, "Client", fail)
    result = UNSAA2AClient(url="http://unsa-mind.invalid/a2a", api_key="secret-key").consultar_normativa("prueba")

    assert result["disponible"] is False
    assert result["abstained"] is True
    assert "No se pudo consultar el agente UNSA (ConnectError)" in caplog.text
    assert "secret-key" not in caplog.text
