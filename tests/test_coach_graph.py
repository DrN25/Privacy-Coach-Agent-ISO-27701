from unittest.mock import patch, MagicMock
from backend.agents.state import AuditState
from backend.agents.supervisor import nodo_supervisor
from backend.agents.context_agent import nodo_context_agent
from backend.agents.profiler_agent import nodo_profiler_agent
from backend.agents.dspm_agent import nodo_dspm_agent
from backend.agents.normative_agent import nodo_normative_agent
from backend.agents.coach_agent import nodo_coach_agent
from backend.agents.reflection import nodo_reflection, ruta_condicional_reflexion
from backend.agents.graph import compilar_grafo_auditoria, ejecutar_flujo_multiagente
from backend.infrastructure.llm_client import LLMResponse


def test_supervisor_routes_intentions():
    assert nodo_supervisor({"historial_mensajes": [{"content": "remediar con script"}]})["intencion"] == "remediacion"
    assert nodo_supervisor({"historial_mensajes": [{"content": "qué norma o iso aplica"}]})["intencion"] == "normativo"
    assert nodo_supervisor({"historial_mensajes": [{"content": "ver tablas y base de datos"}]})["intencion"] == "contexto"
    assert nodo_supervisor({"historial_mensajes": [{"content": "emite dictamen general"}]})["intencion"] == "dictamen"


def test_context_and_profiler_agents():
    ctx_res = nodo_context_agent({"contexto_brecha": {"elemento_afectado": "pacientes.diagnostico"}})
    assert "contexto_empresa" in ctx_res

    prof_res = nodo_profiler_agent({"contexto_brecha": {"elemento_afectado": "pacientes.diagnostico"}})
    assert len(prof_res["perfil_activos"]) >= 1
    assert prof_res["perfil_activos"][0]["tabla"] == "pacientes"


def test_dspm_and_normative_agents():
    dspm_res = nodo_dspm_agent({"contexto_brecha": {"codigo_regla": "R-001"}})
    assert dspm_res["regla_canonica"]["codigo"] == "R-001"

    norm_res = nodo_normative_agent({
        "contexto_brecha": {"codigo_regla": "R-001", "elemento_afectado": "pacientes.diagnostico"},
        "regla_canonica": dspm_res["regla_canonica"]
    })
    assert "subgrafo_normativo" in norm_res
    assert "EXPEDIENTE TÉCNICO" in norm_res["expediente_texto"]
    assert "A.3.26" in norm_res["expediente_texto"]


def test_reflection_evaluator_rejects_and_approves():
    estado_corto: AuditState = {
        "dictamen": "Corto",
        "parche_sql": "",
        "regla_canonica": {"tipo_hallazgo": "TECNICO"},
        "iteracion": 1
    }
    crit_res = nodo_reflection(estado_corto)
    assert crit_res["aprobado"] is False
    assert ruta_condicional_reflexion(crit_res) == "coach_agent"

    estado_valido: AuditState = {
        "dictamen": "### Dictamen Técnico Pericial\nSe constató la vulnerabilidad en la columna diagnosticada conforme a la norma ISO 27701 y Ley 29733.\n```sql\nBEGIN;\nALTER TABLE pacientes DROP COLUMN cvv;\nCOMMIT;\n```\nSustento pericial completo.",
        "parche_sql": "BEGIN;\nALTER TABLE pacientes DROP COLUMN cvv;\nCOMMIT;",
        "regla_canonica": {"tipo_hallazgo": "TECNICO"},
        "iteracion": 1
    }
    crit_aprobado = nodo_reflection(estado_valido)
    assert crit_aprobado["aprobado"] is True
    assert ruta_condicional_reflexion(crit_aprobado) == "__end__"


@patch("backend.agents.coach_agent.default_luna_client.generate")
def test_ejecutar_flujo_multiagente_end_to_end(mock_generate):
    mock_generate.return_value = LLMResponse(
        content="""### Dictamen Técnico Pericial
Diagnóstico: Se detectó vulnerabilidad R-001 de datos clínicos no cifrados.
Controles: ISO 27701 A.3.24 y Ley 29733 Art. 38.
Cuantificación: 12.5 UIT conforme a precedentes ANPD.
```sql
BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
ALTER TABLE pacientes ALTER COLUMN diagnostico TYPE bytea USING pgp_sym_encrypt(diagnostico::text, 'secret');
COMMIT;
```
Dictamen formal culminado.""",
        reasoning="Análisis de controles y graduación de multa.",
        mode="openrouter",
    )

    resultado = ejecutar_flujo_multiagente(
        historial_mensajes=[{"role": "user", "content": "Analiza"}],
        contexto_brecha={"codigo_regla": "R-001", "elemento_afectado": "pacientes.diagnostico"},
    )

    assert "Dictamen Técnico Pericial" in resultado["content"]
    assert "BEGIN;" in resultado["sql_patch"]
    assert "COMMIT;" in resultado["sql_patch"]
    assert resultado["regla_canonica"]["codigo"] == "R-001"
    assert resultado["evaluacion_critica"]["aprobado"] is True
