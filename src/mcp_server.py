# -*- coding: utf-8 -*-
"""
Privacy Coach & DSPM Multi-Agent System — MCP Server
Model Context Protocol (MCP) server for automated privacy posture management,
deterministic DSPM rules (R-001..R-007), 3-padlock LPDP column classification,
ISO 27701:2025 / ISO 29100 GraphRAG traversal, 588 ANPD sanction precedents lookup,
and ISO/IEC 27701:2025 & Ley 29733 Compliance & DSPM remediation with DeepSeek Flash.
"""
import sys
import os
import json
import sqlite3
from typing import Dict, Any, List, Optional

# Ensure src directory is on sys.path
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from mcp.server.mcpserver import MCPServer

from backend.db import init_db, get_db_connection, DB_PATH
from backend.profiler import perfilar_columna, CategoriaDatoLPDP
from backend.dspm_engine import ejecutar_auditoria_dspm
from backend.router import resolver_enrutamiento, ROUTER_MAP
from backend.knowledge_bridge import knowledge_bridge
from backend.coach_agent import dialogar_coach
from backend.ingestion import procesar_archivo_sql, procesar_archivo_documento

app = MCPServer("privacy-dspm")

# Initialize database schema on startup
init_db()

@app.tool()
def dspm_get_status() -> Dict[str, Any]:
    """Get the current compliance and inventory status of the enterprise privacy repository.
    Returns counts of evaluated documents, categorized columns, legal clauses, active breach findings,
    calculated economic exposure in UIT and PEN (Ley 29733 / ANPD), and GraphRAG/ANPD metrics.
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM archivos_evaluados")
    archivos = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM inventario_datos")
    columnas = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM clausulas_analizadas")
    clausulas = c.fetchone()[0]
    
    c.execute("SELECT id_hallazgo, titulo, severidad, multa_uit_estimada, estado_remediacion FROM hallazgos_cumplimiento WHERE estado_remediacion = 'ABIERTO'")
    hallazgos_rows = c.fetchall()
    
    total_uit = sum(r[3] for r in hallazgos_rows)
    pen_valor = total_uit * 5150.0  # UIT 2024: S/ 5,150
    
    conn.close()
    
    return {
        "sistema": "Privacy Coach & DSPM Multi-Agent System (UNSA)",
        "normas_referencia": ["ISO/IEC 27701:2025", "ISO/IEC 29100:2024", "Ley 29733 (Perú)", "D.S. 003-2013-JUS"],
        "documentos_evaluados": archivos,
        "columnas_catalogadas": columnas,
        "clausulas_analizadas": clausulas,
        "brechas_abiertas": len(hallazgos_rows),
        "multa_total_uit": round(total_uit, 2),
        "exposicion_pen": round(pen_valor, 2),
        "kb1_nodos_grafo": len(knowledge_bridge.graph.nodes),
        "kb2_resoluciones_anpd": len(knowledge_bridge.anpd_cases),
        "hallazgos_resumen": [
            {"id": r[0], "titulo": r[1], "severidad": r[2], "multa_uit": r[3]} for r in hallazgos_rows
        ]
    }

@app.tool()
def dspm_audit_repository() -> Dict[str, Any]:
    """Run full deterministic DSPM audit (Rules R-001 through R-007) and O(1) normative routing.
    Evaluates database schemas and legal clauses in SQLite KB-3, correlates violations with ISO 27701:2025,
    calculates official UIT fine ranges according to Peruvian scale (Art. 39 Ley 29733),
    and updates the active findings database.
    """
    findings = ejecutar_auditoria_dspm()
    status = dspm_get_status()
    return {
        "resultado": "Auditoría completada exitosamente",
        "total_brechas": len(findings),
        "detalles_brechas": findings,
        "metricas_resumen": status
    }

@app.tool()
def dspm_classify_column(nombre_columna: str, tipo_dato: str = "VARCHAR(255)", comentario: str = "") -> Dict[str, Any]:
    """Classify a database column using the 3-Candados semantic profiler (AST + NLP regex + Statistical confidence).
    Categorizes the field into LPDP categories (Art. 2.5 Ley 29733) and outputs security recommendations.
    
    Args:
        nombre_columna: Name of the column (e.g. 'diagnostico_cie10', 'tarjeta_credito_cvv', 'password_hash')
        tipo_dato: SQL data type (e.g. 'VARCHAR(255)', 'BYTEA', 'SERIAL')
        comentario: Optional column comment or business description
    """
    res = perfilar_columna("custom_table", nombre_columna, tipo_dato, comentario)
    return {
        "columna": nombre_columna,
        "tipo_dato": tipo_dato,
        "categoria_lpdp": res.categoria_lpdp.value,
        "confianza": f"{res.confianza * 100:.1f}%",
        "candado_1_lexico": res.candado_1_lexico,
        "candado_2_tipo": res.candado_2_tipo,
        "candado_3_contexto": res.candado_3_contexto,
        "requiere_cifrado_reposo": res.requiere_cifrado,
        "recomendacion_tecnica": res.recomendacion
    }

@app.tool()
def graphrag_query_normative(codigo_control_o_termino: str) -> Dict[str, Any]:
    """Traverse the 78-node NetworkX Knowledge Graph.
    Maps an ISO 27701:2025 control (e.g. 'A.3.24', 'A.1.4.5', 'A.3.13'), ISO 29100 privacy principle,
    or Ley 29733 article to retrieve cross-standard requirements and Peruvian legal bridges.
    
    Args:
        codigo_control_o_termino: Control code (e.g. 'A.3.24', 'A.1.4.5') or keyword
    """
    node_data = knowledge_bridge.get_control_details(codigo_control_o_termino)
    subgraph = knowledge_bridge.get_subgraph(codigo_control_o_termino)
    return {
        "consulta": codigo_control_o_termino,
        "control_encontrado": node_data is not None,
        "detalles": node_data or {},
        "subgrafo_relaciones": subgraph
    }

@app.tool()
def anpd_search_sanctions(termino_busqueda: str, limite: int = 5) -> Dict[str, Any]:
    """Search the 588 official sanction resolutions of the Autoridad Nacional de Protección de Datos Personales (ANPD Perú).
    Returns real legal precedents, infractions, and historical penalties in UIT.
    
    Args:
        termino_busqueda: Keyword or concept (e.g. 'salud', 'medidas de seguridad', 'consentimiento', 'flujo transfronterizo')
        limite: Maximum number of matching cases to return (default: 5)
    """
    casos = knowledge_bridge.get_anpd_precedent(termino_busqueda)
    # Filter or return top cases
    q = termino_busqueda.lower()
    matches = []
    for c in knowledge_bridge.anpd_cases:
        desc = str(c.get("hechos", "")).lower() + " " + str(c.get("infraccion", "")).lower() + " " + str(c.get("sancionado", "")).lower()
        if q in desc:
            matches.append(c)
            if len(matches) >= limite:
                break
    
    return {
        "termino": termino_busqueda,
        "total_encontrados": len(matches),
        "precedente_destacado": casos,
        "casos": matches if matches else [casos] if casos else []
    }

@app.tool()
def coach_consult(id_hallazgo: str, consulta_usuario: str = "") -> Dict[str, Any]:
    """Consult the Senior AI Privacy Compliance Auditor (DeepSeek-v4.1-Flash) for ISO/IEC 27701:2025 & Ley 29733.
    Injects an exact 850-token payload containing the deterministic breach context, normative subgraph,
    and ANPD precedents, returning chain-of-thought reasoning, executive legal verdict, and remediation code.
    
    Args:
        id_hallazgo: Finding ID (e.g. 'R-001', 'R-002', 'R-003', 'R-004', 'R-005', 'R-006', 'R-007')
        consulta_usuario: Specific technical question or action requested (e.g. 'Genera el parche SQL', 'Explica la base legal')
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM hallazgos_cumplimiento WHERE id_hallazgo = ?", (id_hallazgo,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return {"error": f"Hallazgo {id_hallazgo} no encontrado en la base de datos."}
    
    # Build finding dict
    finding_dict = {
        "id_hallazgo": row["id_hallazgo"],
        "control_iso27701": row["control_iso27701"],
        "articulo_ley29733": row["articulo_ley29733"],
        "titulo": row["titulo"],
        "descripcion": row["descripcion"],
        "severidad": row["severidad"],
        "multa_uit_estimada": row["multa_uit_estimada"],
        "elemento_afectado": row["elemento_afectado"]
    }
    
    # Run Coach Dialog
    res = dialogar_coach(
        historial_mensajes=[{"role": "user", "content": consulta_usuario if consulta_usuario else f"Analiza y remedia la brecha {id_hallazgo}"}],
        contexto_brecha=finding_dict
    )
    
    return {
        "id_hallazgo": id_hallazgo,
        "control_iso27701": row["control_iso27701"],
        "articulo_ley29733": row["articulo_ley29733"],
        "multa_uit": row["multa_uit_estimada"],
        "dictamen_coach": res.get("content", ""),
        "reasoning": res.get("reasoning", ""),
        "sql_patch": res.get("sql_patch", "")
    }

@app.tool()
def dspm_apply_remediation(id_hallazgo: str) -> Dict[str, Any]:
    """Mark a finding as remediated in SQLite (KB-3), immediately updating the enterprise risk balance
    and deducting the estimated fine from total exposure.
    
    Args:
        id_hallazgo: Finding ID to resolve (e.g. 'R-001', 'R-003')
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE hallazgos_cumplimiento SET estado_remediacion = 'REMEDIADO' WHERE id_hallazgo = ?", (id_hallazgo,))
    conn.commit()
    conn.close()
    
    # Recalculate status
    status = dspm_get_status()
    return {
        "resultado": f"Hallazgo {id_hallazgo} marcado como REMEDIADO exitosamente.",
        "nuevo_estado": status
    }

@app.tool()
def dspm_reset_repository() -> Dict[str, Any]:
    """Wipe all enterprise documents, column inventories, clauses, and findings from SQLite (KB-3)
    to start a pristine audit from scratch (0 documents, 0 UIT fines).
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM archivos_evaluados")
    c.execute("DELETE FROM inventario_datos")
    c.execute("DELETE FROM clausulas_analizadas")
    c.execute("DELETE FROM hallazgos_cumplimiento")
    conn.commit()
    conn.close()
    return {
        "resultado": "Repositorio reiniciado a 0. Listo para una nueva auditoría empresarial.",
        "estado": dspm_get_status()
    }

@app.tool()
def dspm_load_demo_case(case_name: str = "saludtotal") -> Dict[str, Any]:
    """Ingest the 4 realistic enterprise mockups for 'Clínica SaludTotal S.A.C.' into SQLite (KB-3):
    1. schema_clinica_saludtotal.sql (DDL with sensitive health data, plain CVV, MD5 passwords)
    2. politica_privacidad_saludtotal.pdf (Policy with tacit consent, indefinite retention, ARCO fee)
    3. contrato_encargo_sla_cloud.pdf (Cloud SLA with unnotified cross-border transfer to US servers)
    4. diccionario_datos_negocio.txt (Business glossary with developer field definitions)
    
    Automatically triggers DSPM rule evaluation and normative routing.
    """
    mockups_dir = os.path.join(SISTEMA_DIR, "mockups")
    if not os.path.exists(mockups_dir):
        return {"error": f"Directorio de mockups no encontrado en {mockups_dir}"}
        
    ingested = []
    # 1. SQL
    sql_path = os.path.join(mockups_dir, "schema_clinica_saludtotal.sql")
    if os.path.exists(sql_path):
        procesar_archivo_sql(sql_path)
        ingested.append("schema_clinica_saludtotal.sql")
        
    # 2. Documents
    for doc in ["politica_privacidad_saludtotal.pdf", "contrato_encargo_sla_cloud.pdf", "diccionario_datos_negocio.txt"]:
        p = os.path.join(mockups_dir, doc)
        if os.path.exists(p):
            procesar_archivo_documento(p)
            ingested.append(doc)
            
    # Run audit
    findings = ejecutar_auditoria_dspm()
    status = dspm_get_status()
    
    return {
        "resultado": f"Caso demo '{case_name}' cargado exitosamente.",
        "archivos_procesados": ingested,
        "total_brechas_detectadas": len(findings),
        "multa_total_estimada_uit": status["multa_total_uit"],
        "exposicion_pen": status["exposicion_pen"]
    }

@app.tool()
def dspm_ingest_file(file_path: str) -> Dict[str, Any]:
    """Ingest an enterprise file (.sql, .pdf, .md, .txt) into SQLite (KB-3).
    Parses schemas with AST or extracts legal clauses, runs 3-candados classification,
    and updates repository metadata.
    
    Args:
        file_path: Absolute path to the file to ingest.
    """
    if not os.path.exists(file_path):
        return {"error": f"El archivo no existe: {file_path}"}
        
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".sql":
        doc_id = procesar_archivo_sql(file_path)
    elif ext in [".pdf", ".md", ".txt"]:
        doc_id = procesar_archivo_documento(file_path)
    else:
        return {"error": f"Formato no soportado: {ext}. Formatos válidos: .sql, .pdf, .md, .txt"}
        
    return {
        "resultado": f"Archivo {os.path.basename(file_path)} procesado exitosamente.",
        "id_documento": doc_id,
        "sugerencia": "Ejecuta 'dspm_audit_repository' para recalcular las brechas y multas."
    }

# =========================================================================
# MCP Resources
# =========================================================================
@app.resource("privacy://graph/summary")
def get_graph_summary() -> str:
    """Normative Knowledge Graph (KB-1) summary and coverage metrics."""
    nodes = len(knowledge_bridge.graph.nodes)
    edges = len(knowledge_bridge.graph.edges)
    return f"Knowledge Graph KB-1: {nodes} nodes, {edges} cross-standard edges covering ISO/IEC 27701:2025 (PIMS), ISO/IEC 29100:2024 (Privacy Framework), and Ley 29733 (ANPD Perú)."

@app.resource("privacy://dspm/rules-catalog")
def get_rules_catalog() -> str:
    """Catalog of deterministic DSPM rules R-001 through R-007."""
    catalog = {
        "R-001": {"titulo": "Datos de Salud Sensibles sin Cifrado en Reposo", "control": "A.3.24", "severidad": "CRÍTICO", "multa_uit": 12.5},
        "R-002": {"titulo": "Almacenamiento de Contraseñas con Algoritmo Hash Débil (MD5)", "control": "A.3.24", "severidad": "ALTO", "multa_uit": 8.0},
        "R-003": {"titulo": "Almacenamiento Ilegal de Código de Seguridad CVV de Tarjetas", "control": "A.1.4.5", "severidad": "CRÍTICO", "multa_uit": 15.0},
        "R-004": {"titulo": "Consentimiento Tácito o Automático por Mera Navegación Web", "control": "A.3.2", "severidad": "ALTO", "multa_uit": 10.0},
        "R-005": {"titulo": "Plazo de Conservación Indefinido de Datos Personales", "control": "A.3.13", "severidad": "MEDIO", "multa_uit": 7.0},
        "R-006": {"titulo": "Flujo Transfronterizo a Nube Extranjera sin Registro ante ANPD", "control": "A.3.22", "severidad": "ALTO", "multa_uit": 11.0},
        "R-007": {"titulo": "Cobro Indebido de Tarifas para Ejercicio de Derechos ARCO", "control": "A.3.12", "severidad": "MEDIO", "multa_uit": 7.0},
    }
    return json.dumps(catalog, indent=2, ensure_ascii=False)

@app.resource("privacy://anpd/statistics")
def get_anpd_statistics() -> str:
    """ANPD Sanction Precedents (KB-2) summary statistics."""
    total = len(knowledge_bridge.anpd_cases)
    return f"ANPD Enforcement Database KB-2: {total} official sanction resolutions cataloged with infraction types, affected sectors, and historical UIT fine amounts."

if __name__ == "__main__":
    app.run(transport="stdio")