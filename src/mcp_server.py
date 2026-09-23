# -*- coding: utf-8 -*-
"""MCP server for Privacy Coach and deterministic DSPM auditing."""
import json
import os
import re
import sys
from typing import Any, Dict, Optional

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    # MCP >= 1 exposes FastMCP; retain the documented MCPServer name locally.
    from mcp.server.fastmcp import FastMCP

    class MCPServer(FastMCP):
        pass

from backend.db import get_db_connection, init_db
from backend.dspm_engine import ejecutar_auditoria_dspm
from backend.ingestion import procesar_archivo_documento, procesar_archivo_sql
from backend.knowledge_bridge import knowledge_bridge
from backend.profiler import perfilar_columna
from backend.coach_agent import dialogar_coach
from backend.router import ROUTER_MAP


app = MCPServer("privacy-dspm")
init_db()


def _rows(query: str, params=()) -> list:
    conn = get_db_connection()
    try:
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


@app.tool()
def dspm_get_status() -> Dict[str, Any]:
    """Get current counts, open DSPM findings, exposure, and knowledge-base metrics."""
    archivos = _rows("SELECT COUNT(*) AS total FROM archivos_cargados")[0]["total"]
    columnas = _rows("SELECT COUNT(*) AS total FROM inventario_activos_datos")[0]["total"]
    clausulas = _rows("SELECT COUNT(*) AS total FROM clausulas_documentales")[0]["total"]
    hallazgos = _rows(
        """SELECT id, codigo_regla, titulo, nivel_riesgo, multa_estimada_uit, estado
           FROM hallazgos_dspm WHERE estado <> 'REMEDIADO'"""
    )
    total_uit = sum(row["multa_estimada_uit"] for row in hallazgos)
    return {
        "sistema": "Privacy Coach & DSPM Multi-Agent System (UNSA)",
        "normas_referencia": ["ISO/IEC 27701:2025", "ISO/IEC 29100:2024", "Ley 29733 (Perú)"],
        "documentos_evaluados": archivos,
        "columnas_catalogadas": columnas,
        "clausulas_analizadas": clausulas,
        "brechas_abiertas": len(hallazgos),
        "multa_total_uit": round(total_uit, 2),
        "exposicion_pen": round(total_uit * 5150.0, 2),
        "kb1_nodos": len(knowledge_bridge.engine.controls_map) + len(knowledge_bridge.engine.principles_map),
        "kb2_resoluciones_anpd": len(knowledge_bridge.sanciones),
        "hallazgos_resumen": hallazgos,
    }


@app.tool()
def dspm_audit_repository() -> Dict[str, Any]:
    """Run deterministic DSPM rules R-001 through R-007."""
    findings = ejecutar_auditoria_dspm() or []
    return {
        "resultado": "Auditoría completada exitosamente",
        "total_brechas": len(findings),
        "detalles_brechas": findings,
        "metricas_resumen": dspm_get_status(),
    }


@app.tool()
def dspm_classify_column(nombre_columna: str, tipo_dato: str = "VARCHAR(255)", comentario: str = "") -> Dict[str, Any]:
    """Classify a SQL column with the three-lock LPDP profiler."""
    res = perfilar_columna(nombre_columna, "custom_table", tipo_dato)
    return {
        "columna": nombre_columna,
        "tipo_dato": tipo_dato,
        "comentario": comentario,
        "categoria_lpdp": res.categoria.value,
        "confianza": f"{res.nivel_confianza * 100:.1f}%",
        "candado_deteccion": res.candado,
        "requiere_cifrado_reposo": res.es_sensible,
        "recomendacion_tecnica": res.recomendacion,
    }


@app.tool()
def graphrag_query_normative(codigo_control_o_termino: str) -> Dict[str, Any]:
    """Query ISO 27701, ISO 29100, and Ley 29733 knowledge relations."""
    engine = knowledge_bridge.engine
    control = engine.get_control(codigo_control_o_termino)
    if control is None:
        matches = engine.search_controls(codigo_control_o_termino, limit=1)
        control = matches[0] if matches else None
    control_id = control.get("id") if control else codigo_control_o_termino
    subgraph = engine.get_subgraph([control_id]) if control else {
        "requested_control_ids": [codigo_control_o_termino], "controls": [],
        "iso29100_principles": [], "anpd_precedents": [],
    }
    return {"consulta": codigo_control_o_termino, "control_encontrado": control is not None,
            "detalles": control or {}, "subgrafo_relaciones": subgraph}


@app.tool()
def anpd_search_sanctions(termino_busqueda: str, limite: int = 5) -> Dict[str, Any]:
    """Search loaded ANPD sanction records by text."""
    if limite <= 0:
        return {"termino": termino_busqueda, "total_encontrados": 0, "casos": []}
    q = termino_busqueda.lower()
    matches = []
    for caso in knowledge_bridge.sanciones:
        texto = json.dumps(caso, ensure_ascii=False).lower()
        if q in texto:
            matches.append(caso)
            if len(matches) >= limite:
                break
    return {"termino": termino_busqueda, "total_encontrados": len(matches), "casos": matches}


@app.tool()
def coach_consult(id_hallazgo: str, consulta_usuario: str = "") -> Dict[str, Any]:
    """Request a technical compliance opinion for a DSPM finding."""
    rows = _rows("SELECT * FROM hallazgos_dspm WHERE codigo_regla = ?", (id_hallazgo,))
    if not rows:
        return {"error": f"Hallazgo {id_hallazgo} no encontrado en la base de datos."}
    row = rows[0]
    row["contexto_normativo"] = knowledge_bridge.extraer_subgrafo_control(row["control_iso27701"])
    result = dialogar_coach(
        historial_mensajes=[{"role": "user", "content": consulta_usuario or f"Analiza y remedia la brecha {id_hallazgo}"}],
        contexto_brecha=row,
    )
    return {
        "id_hallazgo": id_hallazgo,
        "control_iso27701": row["control_iso27701"],
        "articulo_ley29733": row["articulo_ley29733"],
        "multa_uit": row["multa_estimada_uit"],
        "dictamen_coach": result.get("content", ""),
        "reasoning": result.get("reasoning", ""),
        "sql_patch": result.get("sql_patch", ""),
        "mode": result.get("mode", "openrouter"),
        "error": result.get("error"),
    }


@app.tool()
def dspm_apply_remediation(id_hallazgo: str, parche_sql: Optional[str] = None) -> Dict[str, Any]:
    """Mark R-xxx as REMEDIADO; optional SQL patch is recorded in the response, never executed."""
    if not re.fullmatch(r"R-\d{3}", id_hallazgo):
        return {"error": "El código de hallazgo debe tener formato R-xxx."}
    conn = get_db_connection()
    try:
        cur = conn.execute("UPDATE hallazgos_dspm SET estado = 'REMEDIADO' WHERE codigo_regla = ?", (id_hallazgo,))
        conn.commit()
        updated = cur.rowcount > 0
    finally:
        conn.close()
    return {"resultado": "Hallazgo marcado como REMEDIADO." if updated else "Hallazgo no encontrado.",
            "codigo_regla": id_hallazgo, "nuevo_estado": "REMEDIADO" if updated else None,
            "parche_sql_recibido": bool(parche_sql), "parche_sql_ejecutado": False,
            "estado": dspm_get_status()}


@app.tool()
def dspm_reset_repository() -> Dict[str, Any]:
    """Delete loaded documents, inventory, clauses, and DSPM findings."""
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM interacciones_coach")
        conn.execute("DELETE FROM hallazgos_dspm")
        conn.execute("DELETE FROM clausulas_documentales")
        conn.execute("DELETE FROM inventario_activos_datos")
        conn.execute("DELETE FROM archivos_cargados")
        conn.commit()
    finally:
        conn.close()
    return {"resultado": "Repositorio reiniciado a 0.", "estado": dspm_get_status()}


@app.tool()
def dspm_load_demo_case(case_name: str = "saludtotal") -> Dict[str, Any]:
    """Load demo files from the project's mockups directory, when present."""
    mockups_dir = os.path.join(SRC_DIR, "mockups")
    if not os.path.isdir(mockups_dir):
        return {"error": f"Directorio de mockups no encontrado en {mockups_dir}"}
    names = ["schema_clinica_saludtotal.sql", "politica_privacidad_saludtotal.pdf",
             "contrato_encargo_sla_cloud.pdf", "diccionario_datos_negocio.txt"]
    ingested = []
    for name in names:
        path = os.path.join(mockups_dir, name)
        if os.path.isfile(path):
            if name.endswith(".sql"):
                procesar_archivo_sql(path, name)
            else:
                procesar_archivo_documento(path, name)
            ingested.append(name)
    findings = ejecutar_auditoria_dspm() or []
    status = dspm_get_status()
    return {"resultado": f"Caso demo '{case_name}' cargado exitosamente.",
            "archivos_procesados": ingested, "total_brechas_detectadas": len(findings),
            "multa_total_estimada_uit": status["multa_total_uit"], "exposicion_pen": status["exposicion_pen"]}


@app.tool()
def dspm_ingest_file(file_path: str, nombre_archivo: Optional[str] = None) -> Dict[str, Any]:
    """Ingest SQL, PDF, Markdown, or text using its route and display name."""
    if not os.path.isfile(file_path):
        return {"error": f"El archivo no existe: {file_path}"}
    nombre = nombre_archivo or os.path.basename(file_path)
    ext = os.path.splitext(nombre)[1].lower()
    if ext == ".sql":
        doc_id = procesar_archivo_sql(file_path, nombre)
    elif ext in (".pdf", ".md", ".txt"):
        doc_id = procesar_archivo_documento(file_path, nombre)
    else:
        return {"error": f"Formato no soportado: {ext}. Formatos válidos: .sql, .pdf, .md, .txt"}
    return {"resultado": f"Archivo {nombre} procesado exitosamente.", "id_documento": doc_id,
            "sugerencia": "Ejecuta 'dspm_audit_repository' para recalcular las brechas."}


@app.resource("privacy://graph/summary")
def get_graph_summary() -> str:
    """Knowledge-base coverage summary."""
    engine = knowledge_bridge.engine
    edges = sum(len(values) for values in engine.adj.values())
    nodes = len(engine.controls_map) + len(engine.principles_map)
    return f"Knowledge base: {nodes} nodes, {edges} cross-standard edges."


@app.resource("privacy://dspm/rules-catalog")
def get_rules_catalog() -> str:
    """Catalog of deterministic DSPM rules R-001 through R-007."""
    return json.dumps({code: {"titulo": data["titulo"], "control": data["control_iso27701"],
                              "severidad": data["nivel_riesgo"], "multa_uit": data["multa_estimada_uit"]}
                      for code, data in ROUTER_MAP.items()},
                      indent=2, ensure_ascii=False)


@app.resource("privacy://anpd/statistics")
def get_anpd_statistics() -> str:
    """ANPD sanction dataset summary."""
    return f"ANPD enforcement database: {len(knowledge_bridge.sanciones)} sanction resolutions loaded."


if __name__ == "__main__":
    app.run(transport="stdio")
