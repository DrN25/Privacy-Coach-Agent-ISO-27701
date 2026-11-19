"""
Agente Text-to-SQL en tiempo real con guardrail AST mediante SQLGlot y ejecución de solo lectura.
"""

import json
import logging
import os
import re
import sqlite3
from typing import Any, Dict, List, Optional, Tuple

import sqlglot
from sqlglot import exp

from .state import AuditState
from ..db import DEFAULT_DB_PATH
from ..infrastructure.llm_client import default_luna_client
from ..infrastructure.repository import repository

logger = logging.getLogger("pims.sql_agent")

ALLOWED_TABLES = {
    "core_incident",
    "core_incidentaction",
    "core_incidenthistory",
    "core_incidentattachment",
    "core_incidentrecipient",
    "core_securitylog",
    "core_asset",
    "core_process",
    "core_auditfinding",
    "auth_user",
    "core_userprofile",
    "a6_incident_ext",
    "a6_corrective_action",
    "a6_system_config",
    "hallazgos_dspm",
    "archivos_cargados",
    "inventario_activos_datos",
    "clausulas_documentales",
}

FORBIDDEN_EXPR_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.Command,
    exp.Pragma,
    exp.Attach,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
    exp.Into,
)

SCHEMA_GROUNDING = """ESQUEMA RELACIONAL AUTORIZADO (SOLO LECTURA - SQLITE / POSTGRESQL):
1. core_incident (id, incident_code, title, description, status, severity, impact, incident_type, involves_personal_data, incident_date, detection_date, resolved_date, reported_by, assigned_to, compromised_system, affected_url, num_affected_subjects, is_deleted)
   - status: 'I'=En Investigación (abierto/pendiente), 'E'=En Mitigación (abierto/pendiente), 'C'=Cerrado. (Pendientes o sin cerrar = status IN ('I', 'E') AND is_deleted = 0).
   - severity / impact: 'C'=Crítico, 'A'=Alto, 'M'=Medio, 'B'=Bajo.
   - incident_type: 'BF'=Brecha Confidencialidad, 'BI'=Brecha Integridad, 'BD'=Brecha Disponibilidad, 'PI'=No Conformidad Principios PII, 'IT'=Incidente Técnico sin PII.
   - involves_personal_data: 1=Afecta PII, 0=Técnico sin PII.
   - Año de registro: COALESCE(detection_date, incident_date) en formato 'YYYY-MM-DD' (ej. strftime('%Y', COALESCE(detection_date, incident_date)) BETWEEN '2023' AND '2025', o detection_date >= '2023-01-01' AND detection_date < '2026-01-01').
2. a6_incident_ext (incident_id PK, involves_personal_data, iso27701_control_id, regla_codigo, asset_id, consequences_summary, data_recovered_status, data_recovered_detail, anpd_notified, anpd_notified_at, anpd_official_ref, anpd_delay_justification, subjects_notified, subjects_notified_at, multa_estimada_uit, precedente_anpd)
3. core_incidentaction (id, incident_id, action_type ['C'=Contención,'R'=Remediación,'M'=Mitigación], responsible, action_date, description, evidence, position)
4. core_incidenthistory (id, incident_id, event_type, changed_at, actor, description, recipients_snapshot)
5. core_incidentattachment (id, incident_id, file, file_name, uploaded_at)
6. a6_corrective_action (id, incident_id, mc_code, nonconformity_desc, identified_on, identified_by_name, root_cause, similar_mc_ref, action_required, action_to_implement, notify_who, approved_by_name, due_date, responsible_name, implemented_on, effectiveness_reviewed_on, doc_changes_required, status ['ABIERTA','EN_PROGRESO','IMPLEMENTADA','VERIFICADA','NO_REQUIERE'])
7. core_asset (id, code, name, category, classification, owner, custodians, location)
8. core_securitylog (id, username, action, module, object_type, object_id, detail, ip_address, created_at)
9. core_incidentrecipient (id, email, label, is_active)
10. auth_user (id, username, first_name, last_name, email, is_active) -- PROHIBIDO seleccionar password o usar auth_user.*
11. core_userprofile (id, user_id, area, position)
12. hallazgos_dspm (id, codigo_regla, titulo, nivel_riesgo, elemento_afectado, origen_archivo, control_iso27701, multa_estimada_uit, estado)
"""


def validate_and_transpile_sql(sql_raw: str, dialect: str = "sqlite") -> str:
    """
    Valida por AST con SQLGlot que la consulta sea un único SELECT de solo lectura
    sobre tablas permitidas, sin columnas bloqueadas (auth_user.password), y con LIMIT <= 100.
    """
    cleaned = (sql_raw or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:sql)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()
    if not cleaned:
        raise ValueError("Consulta SQL vacía.")

    statements = None
    for read_dialect in ("postgres", "sqlite"):
        try:
            statements = sqlglot.parse(cleaned, read=read_dialect)
            break
        except Exception:
            statements = None
    if not statements or len(statements) != 1 or statements[0] is None:
        raise ValueError("Solo se permite exactamente una sentencia SELECT válida.")

    stmt = statements[0]
    if not isinstance(stmt, (exp.Select, exp.Union)):
        raise ValueError(f"Tipo de sentencia prohibida ({type(stmt).__name__}). Solo SELECT permitido.")

    for forbidden in FORBIDDEN_EXPR_TYPES:
        if any(True for _ in stmt.find_all(forbidden)):
            raise ValueError(f"Operación prohibida detectada en AST ({forbidden.__name__}).")

    cte_names = {
        c.alias_or_name.lower()
        for c in stmt.find_all(exp.CTE)
        if getattr(c, "alias_or_name", None)
    }

    for tbl in stmt.find_all(exp.Table):
        schema_name = (tbl.db or "").strip().lower()
        table_name = (tbl.name or "").strip().lower()
        if schema_name and schema_name != "demo":
            raise ValueError(f"Esquema no autorizado: {schema_name}")
        if schema_name == "demo":
            tbl.set("db", None)
        if table_name not in ALLOWED_TABLES and table_name not in cte_names:
            raise ValueError(f"Tabla no autorizada en consulta: {table_name}")

    for col in stmt.find_all(exp.Column):
        if (col.name or "").strip().lower() == "password":
            raise ValueError("Acceso prohibido a columna sensible 'password'.")

    for sel in stmt.find_all(exp.Select):
        has_auth_user = any((t.name or "").strip().lower() == "auth_user" for t in sel.find_all(exp.Table))
        if has_auth_user:
            for star in sel.find_all(exp.Star):
                parent = star.parent
                # Bloquea SELECT * o u.* cuando auth_user está en ese SELECT
                if isinstance(parent, exp.Select) or isinstance(parent, exp.Column):
                    raise ValueError("SELECT * está prohibido cuando participa la tabla auth_user.")

    existing_limit = stmt.args.get("limit")
    if existing_limit is None:
        stmt = stmt.limit(100)
    else:
        lim_expr = existing_limit.expression
        if isinstance(lim_expr, exp.Literal) and lim_expr.is_int:
            if int(lim_expr.this) > 100:
                stmt = stmt.limit(100)

    return stmt.sql(dialect=dialect)


def execute_readonly_sql(safe_sql: str) -> List[Dict[str, Any]]:
    """Ejecuta una consulta ya validada abriendo SQLite en modo estrictamente solo lectura."""
    repository._pims_conn().close()
    db_path = os.path.abspath(os.getenv("DATABASE_PATH", DEFAULT_DB_PATH))
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA query_only = ON;")
        rows = conn.execute(safe_sql).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def _should_run_sql_agent(state: AuditState) -> bool:
    intencion = (state.get("intencion") or "").lower()
    if intencion in ("sql_query", "hibrido"):
        return True
    ui_ctx = state.get("ui_context") or {}
    if ui_ctx.get("selected_incident_id"):
        msgs = state.get("historial_mensajes") or []
        q = (msgs[-1].get("content", "") if msgs else "").lower()
        if any(k in q for k in ("pendiente", "falta", "acción", "accion", "responsable", "estado", "cerrar", "medida", "correctiva", "este caso", "este expediente", "este incidente")):
            return True
    return False


def _extract_sql_from_llm(text: str) -> str:
    raw = (text or "").strip()
    m_json = re.search(r"\{.*\}", raw, re.DOTALL)
    if m_json:
        try:
            obj = json.loads(m_json.group(0))
            if isinstance(obj, dict) and obj.get("sql"):
                return str(obj["sql"]).strip()
        except Exception as exc:
            logger.debug("Fallback de extracción SQL sin JSON (%s)", type(exc).__name__)
    m_sql = re.search(r"```(?:sql)?\s*(.*?)\s*```", raw, re.DOTALL | re.IGNORECASE)
    if m_sql:
        return m_sql.group(1).strip()
    return raw


def _format_rows_markdown(rows: List[Dict[str, Any]], max_rows: int = 50) -> str:
    if not rows:
        return "(0 filas devueltas por la base de datos)"
    cols = list(rows[0].keys())
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for r in rows[:max_rows]:
        vals = [str(r.get(c, "") if r.get(c) is not None else "").replace("\n", " ").replace("|", "/")[:120] for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    if len(rows) > max_rows:
        lines.append(f"\n*(Mostrando {max_rows} de {len(rows)} filas)*")
    return "\n".join(lines)


def nodo_sql_agent(state: AuditState) -> Dict[str, Any]:
    """Genera SQL con LLM, valida AST con SQLGlot, ejecuta read-only y corrige hasta 2 veces."""
    if not _should_run_sql_agent(state):
        return {}

    msgs = state.get("historial_mensajes") or []
    user_q = msgs[-1].get("content", "") if msgs else ""
    ui_ctx = state.get("ui_context") or {}
    trace = list(state.get("trazabilidad") or [])

    ctx_note = ""
    if ui_ctx.get("selected_incident_id"):
        ctx_note = (
            f"\nContexto actual de interfaz: módulo='{ui_ctx.get('active_module', '')}', "
            f"selected_incident_id={ui_ctx.get('selected_incident_id')}, "
            f"tab='{ui_ctx.get('active_tab', '')}'."
        )

    prompt_msgs = [
        {
            "role": "system",
            "content": (
                "Eres un generador experto de consultas SQL SQLite/PostgreSQL de solo lectura para gestión de incidentes ISO/IEC 27701:2025.\n"
                f"{SCHEMA_GROUNDING}\n"
                "REGLAS ESTRICTAS:\n"
                "1. Devuelve únicamente JSON válido: {\"sql\": \"SELECT ...\"}.\n"
                "2. Incluye siempre `ci.is_deleted = 0` si consultas `core_incident`.\n"
                "3. Para 'pendientes' o 'sin cerrar', usa `status IN ('I', 'E')`.\n"
                "4. Para rango de años (ej. 2023-2025), filtra con `strftime('%Y', COALESCE(detection_date, incident_date)) BETWEEN '2023' AND '2025'`.\n"
                "5. Para responsables con críticos sin cerrar, agrupa o lista por `assigned_to` con `severity = 'C' AND status IN ('I', 'E')`.\n"
                "6. Si preguntan específicamente por 'esta incidencia'/'este expediente' con `selected_incident_id` presente, filtra `ci.id = <selected_incident_id>` incluyendo acciones o MC; si preguntan por totales, tablas globales o el más crítico de toda la BD, NO filtres por `selected_incident_id`.\n"
                "7. NO uses SELECT * sobre auth_user ni selecciones la columna password."
            ),
        },
        {"role": "user", "content": f"Pregunta del usuario: {user_q}{ctx_note}"},
    ]

    safe_sql = ""
    rows: List[Dict[str, Any]] = []
    last_err: Optional[str] = None

    for attempt in range(3):
        resp = default_luna_client.generate(messages=prompt_msgs, temperature=0.0, max_tokens=600)
        if resp.mode == "error":
            last_err = resp.raw.get("error", "LLM no disponible")
            break
        candidate_sql = _extract_sql_from_llm(resp.content)
        try:
            safe_sql = validate_and_transpile_sql(candidate_sql, dialect="sqlite")
            rows = execute_readonly_sql(safe_sql)
            last_err = None
            break
        except Exception as exc:
            last_err = str(exc)
            prompt_msgs.append({"role": "assistant", "content": resp.content})
            prompt_msgs.append({
                "role": "user",
                "content": f"La consulta falló ({last_err}). Corrige el SQL y responde solo JSON {{\"sql\": \"SELECT ...\"}}.",
            })

    if last_err:
        trace.append({
            "paso": len(trace) + 1,
            "agente": "SQL Query Agent (SQLGlot)",
            "accion": "Consulta SQL en tiempo real omitida por error",
            "detalle": f"Error validando/ejecutando SQL: {last_err}",
            "sql": safe_sql,
            "row_count": 0,
            "estado": "warn",
        })
        return {"sql_executed": safe_sql, "sql_rows": [], "sql_context_text": "", "trazabilidad": trace}

    table_md = _format_rows_markdown(rows)
    sql_context_text = (
        f"RESULTADOS REALES DE BASE DE DATOS EN TIEMPO REAL ({len(rows)} filas):\n"
        f"```sql\n{safe_sql}\n```\n"
        f"{table_md}\n"
    )
    trace.append({
        "paso": len(trace) + 1,
        "agente": "SQL Query Agent (SQLGlot)",
        "accion": f"Consulta SQL verificada por AST ({len(rows)} filas recuperadas)",
        "detalle": f"SQL ejecutado: {safe_sql}",
        "sql": safe_sql,
        "row_count": len(rows),
        "estado": "ok",
    })

    return {
        "sql_executed": safe_sql,
        "sql_rows": rows,
        "sql_context_text": sql_context_text,
        "trazabilidad": trace,
    }
