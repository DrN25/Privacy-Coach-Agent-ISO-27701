import pytest
from fastapi.testclient import TestClient

from backend.agents.sql_agent import execute_readonly_sql, validate_and_transpile_sql
from backend.app import app
from backend.infrastructure.llm_client import LLMResponse


@pytest.mark.parametrize(
    "bad_sql",
    [
        "DROP TABLE core_incident",
        "DELETE FROM core_incident",
        "UPDATE core_incident SET status='C'",
        "INSERT INTO core_incidentrecipient (email, label, is_active, created_at) VALUES ('a@b.com', 'x', 1, '2026-01-01')",
        "PRAGMA table_info(auth_user)",
        "SELECT 1; DROP TABLE core_incident;",
        "SELECT * FROM auth_user",
        "SELECT id, password FROM auth_user",
        "SELECT * FROM sqlite_master",
        "SELECT * FROM other_schema.core_incident",
    ],
)
def test_validate_and_transpile_sql_rejects_dangerous_queries(bad_sql):
    with pytest.raises(ValueError):
        validate_and_transpile_sql(bad_sql)


def test_validate_and_transpile_sql_allows_demo_schema_and_cte():
    sql_demo = "SELECT id, incident_code FROM demo.core_incident WHERE status IN ('I', 'E')"
    out_demo = validate_and_transpile_sql(sql_demo, dialect="sqlite")
    assert "demo." not in out_demo.lower()
    assert out_demo.upper().startswith("SELECT")
    assert "LIMIT 100" in out_demo.upper()

    sql_cte = "WITH abiertos AS (SELECT id FROM demo.core_incident WHERE status != 'C') SELECT COUNT(*) AS total FROM abiertos"
    out_cte = validate_and_transpile_sql(sql_cte, dialect="sqlite")
    assert "demo." not in out_cte.lower()
    assert "ABIERTO" in out_cte.upper()
    assert "LIMIT 100" in out_cte.upper()


def test_execute_readonly_sql_pendientes_2023_2025():
    sql = (
        "SELECT id, incident_code FROM core_incident "
        "WHERE is_deleted = 0 AND status IN ('I', 'E') "
        "AND strftime('%Y', COALESCE(detection_date, incident_date)) BETWEEN '2023' AND '2025' "
        "ORDER BY id"
    )
    safe_sql = validate_and_transpile_sql(sql, dialect="sqlite")
    rows = execute_readonly_sql(safe_sql)
    assert [r["id"] for r in rows] == [608, 610, 611, 613, 614]


def test_execute_readonly_sql_responsables_criticos_sin_cerrar():
    sql = (
        "SELECT assigned_to, COUNT(*) AS abiertos FROM core_incident "
        "WHERE is_deleted = 0 AND status IN ('I', 'E') AND severity = 'C' "
        "GROUP BY assigned_to ORDER BY abiertos DESC"
    )
    safe_sql = validate_and_transpile_sql(sql, dialect="sqlite")
    rows = execute_readonly_sql(safe_sql)
    counts = {r["assigned_to"]: r["abiertos"] for r in rows}
    assert counts == {
        "Ing. Marcos Ruiz Benavente": 2,
        "Ing. Manuel Soto Paredes": 1,
        "Ing. Pedro Cornejo Quispe": 1,
    }


def test_chat_supervisor_sql_agent_langgraph_integration(monkeypatch):
    calls = {"n": 0}

    def fake_generate(messages, temperature=0.2, max_tokens=4000, extra_payload=None):
        calls["n"] += 1
        if calls["n"] == 1:
            return LLMResponse(
                content=(
                    '{"sql": "SELECT id, incident_code, status, detection_date '
                    'FROM core_incident WHERE is_deleted = 0 AND status IN (\'I\', \'E\') '
                    'AND strftime(\'%Y\', COALESCE(detection_date, incident_date)) BETWEEN \'2023\' AND \'2025\' '
                    'ORDER BY id"}'
                ),
                mode="openrouter",
            )
        return LLMResponse(
            content=(
                "### Incidentes pendientes del periodo 2023-2025\n"
                "Se identificaron **5 registros pendientes** en base de datos:\n"
                "- `INC-UNSA-2023-001` (ID 608)\n"
                "- `INC-UNSA-2024-001` (ID 610)\n"
                "- `INC-UNSA-2024-002` (ID 611)\n"
                "- `INC-UNSA-2025-001` (ID 613)\n"
                "- `INC-UNSA-2025-002` (ID 614)"
            ),
            reasoning="Resultados verificados por SQL Query Agent (SQLGlot).",
            mode="openrouter",
        )

    monkeypatch.setattr("backend.infrastructure.llm_client.default_luna_client.generate", fake_generate)

    with TestClient(app) as client:
        resp = client.post(
            "/api/chat",
            json={
                "mensaje_usuario": "¿Cuáles son los registros pendientes del 2023-2025?",
                "ui_context": {"active_module": "incidentes", "selected_incident_id": 604},
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["sql_executed"].strip().upper().startswith("SELECT")

    sql_steps = [t for t in data["trazabilidad"] if t.get("agente") == "SQL Query Agent (SQLGlot)"]
    assert len(sql_steps) == 1
    assert sql_steps[0]["estado"] == "ok"
    assert sql_steps[0]["row_count"] == 5
