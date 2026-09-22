import asyncio

import mcp_server


def test_mcp_tools_use_current_schema():
    mcp_server.dspm_reset_repository()
    loaded = mcp_server.dspm_load_demo_case()
    status = mcp_server.dspm_get_status()
    classification = mcp_server.dspm_classify_column("password_hash", "VARCHAR(32)")
    normative = mcp_server.graphrag_query_normative("A.3.24")

    assert loaded["total_brechas_detectadas"] == 7
    assert status["brechas_abiertas"] == 7
    assert classification["categoria_lpdp"] == "CREDENCIALES_ACCESO"
    assert normative["control_encontrado"] is True
    assert "89 nodes" in mcp_server.get_graph_summary()
    assert mcp_server.anpd_search_sanctions("datos", limite=0)["casos"] == []


def test_mcp_registers_documented_protocol_surface():
    tools = asyncio.run(mcp_server.app.list_tools())
    resources = asyncio.run(mcp_server.app.list_resources())

    assert {tool.name for tool in tools} == {
        "dspm_get_status",
        "dspm_audit_repository",
        "dspm_classify_column",
        "graphrag_query_normative",
        "anpd_search_sanctions",
        "coach_consult",
        "dspm_apply_remediation",
        "dspm_reset_repository",
        "dspm_load_demo_case",
        "dspm_ingest_file",
    }
    assert len(resources) == 3
