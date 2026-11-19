"""
Patrón Repositorio Unificado (Repository Pattern).
Opera contra la base SQLite unificada PIMS (con esquema idéntico al modelo PostgreSQL institucional)
para gestión CRUD de Incidentes A.3.12, Medidas Correctivas 10.2, Activos, Usuarios y Hallazgos DSPM.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from .db import (
    PSYCOPG2_AVAILABLE,
    RealDictCursor,
    check_postgres_alive,
    get_db_connection,
    get_postgres_connection,
    get_sqlite_connection,
)
from .pims_schema import ensure_pims_migrations, init_pims_tables
from ..core.rules_catalog import VALOR_UIT_PEN, resolver_regla_con_fallback

logger = logging.getLogger("pims.repository")

MAPA_SEVERIDAD_HALLAZGO = {
    "CRÍTICO": "C",
    "CRITICO": "C",
    "MUY GRAVE": "C",
    "ALTO": "A",
    "GRAVE": "A",
    "MEDIO": "M",
    "LEVE": "B",
    "BAJO": "B",
}


def _safe_json_loads(raw: Any, default: Any):
    if raw is None:
        return default
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return default


class AuditRepository:
    def __init__(self, connection_factory=get_db_connection):
        self.get_conn = connection_factory

    def _pims_conn(self) -> sqlite3.Connection:
        """Retorna conexión SQLite garantizando inicialización de tablas y semilla PIMS."""
        # ponytail: SQLite primary for local Agente 6 CRUD (compatible con tests temp DB)
        conn = get_sqlite_connection()
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='core_incident'"
        ).fetchone()
        if not row:
            init_pims_tables(conn)
        else:
            ensure_pims_migrations(conn)
        return conn

    def _actor_label(self, conn: sqlite3.Connection, actor_id: Optional[int]) -> str:
        if actor_id:
            row = conn.execute(
                """
                SELECT u.first_name, u.last_name, p.position
                FROM auth_user u
                LEFT JOIN core_userprofile p ON p.user_id = u.id
                WHERE u.id = ?
                """,
                (actor_id,),
            ).fetchone()
            if row:
                full_name = f"{row['first_name']} {row['last_name']}".strip()
                return f"{full_name} ({row['position']})" if row["position"] else full_name
        cfg = conn.execute("SELECT dpo_name FROM a6_system_config WHERE id = 1").fetchone()
        return cfg["dpo_name"] if cfg else "Abog. Carlos Mendoza Valdivia (DPO UNSA)"

    def _config_row(self, conn: sqlite3.Connection) -> Dict[str, Any]:
        row = conn.execute("SELECT * FROM a6_system_config WHERE id = 1").fetchone()
        if row:
            return dict(row)
        return {
            "id": 1,
            "org_name": "Universidad Nacional de San Agustín de Arequipa",
            "org_ruc": "20140798781",
            "legal_rep_name": "Dr. Hugo Rojas Flores",
            "dpo_user_id": 601,
            "dpo_name": "Abog. Carlos Mendoza Valdivia (DPO UNSA)",
            "dpo_email": "dpo@unsa.edu.pe",
            "ciso_user_id": 604,
            "uit_value_pen": VALOR_UIT_PEN,
        }

    def _hydrate_incident(self, row: sqlite3.Row, uit_value: float) -> Dict[str, Any]:
        d = dict(row)
        d["affected_data_types"] = _safe_json_loads(d.get("affected_data_types"), [])
        d["security_measures_adopted"] = _safe_json_loads(d.get("security_measures_adopted"), {})
        d["affected_cid"] = _safe_json_loads(d.get("affected_cid"), {})

        det_date = d.get("detection_date") or d.get("incident_date") or ""
        d["year"] = int(det_date[:4]) if len(det_date) >= 4 and det_date[:4].isdigit() else 2026
        d["involves_personal_data"] = bool(
            d.get("ext_involves_personal_data")
            if d.get("ext_involves_personal_data") is not None
            else d.get("involves_personal_data", 1)
        )
        d["anpd_notified"] = bool(d.get("anpd_notified", 0))
        d["subjects_notified"] = bool(d.get("subjects_notified", 0))
        multa_uit = float(d.get("multa_estimada_uit") or 0.0)
        d["multa_estimada_uit"] = multa_uit
        d["multa_estimada_pen"] = round(multa_uit * float(uit_value or VALOR_UIT_PEN), 2)
        d["iso27701_control_id"] = d.get("iso27701_control_id") or "A.3.12"
        d["data_recovered_status"] = d.get("data_recovered_status") or "NO_APLICA"
        return d

    # =========================================================================
    # 1. INCIDENTES Y BRECHAS ISO/IEC 27701:2025 (core_incident + a6_incident_ext)
    # =========================================================================

    def listar_incidentes_unsa(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retorna incidentes y brechas desde SQLite con filtros opcionales."""
        conn = self._pims_conn()
        try:
            cfg = self._config_row(conn)
            rows = conn.execute(
                """
                SELECT ci.*,
                       ext.involves_personal_data AS ext_involves_personal_data,
                       ext.iso27701_control_id, ext.regla_codigo, ext.asset_id, ext.source_finding_id,
                       ext.consequences_summary, ext.data_recovered_status, ext.data_recovered_detail,
                       ext.anpd_notified, ext.anpd_notified_at, ext.anpd_official_ref, ext.anpd_delay_justification,
                       ext.subjects_notified, ext.subjects_notified_at, ext.subjects_notice_channel,
                       ext.multa_estimada_uit, ext.precedente_anpd,
                       ca.code AS asset_code, ca.name AS asset_name,
                       mc.id AS mc_id, mc.mc_code, mc.status AS mc_status, mc.due_date AS mc_due_date,
                       (SELECT COUNT(*) FROM core_incidentaction a WHERE a.incident_id = ci.id) AS actions_count,
                       (SELECT COUNT(*) FROM core_incidentattachment att WHERE att.incident_id = ci.id) AS attachments_count
                FROM core_incident ci
                LEFT JOIN a6_incident_ext ext ON ext.incident_id = ci.id
                LEFT JOIN core_asset ca ON ca.id = ext.asset_id
                LEFT JOIN a6_corrective_action mc ON mc.incident_id = ci.id
                WHERE ci.is_deleted = 0
                ORDER BY COALESCE(ci.detection_date, ci.incident_date) DESC, ci.id ASC
                """
            ).fetchall()
            items = [self._hydrate_incident(r, cfg["uit_value_pen"]) for r in rows]
        finally:
            conn.close()

        if not filters:
            return items

        res = items
        year = str(filters.get("year") or "").strip()
        if year and year != "ALL":
            res = [i for i in res if str(i.get("year")) == year]

        status = str(filters.get("status") or "").strip().upper()
        if status == "OPEN":
            res = [i for i in res if i.get("status") in ("I", "E")]
        elif status in ("I", "E", "C"):
            res = [i for i in res if i.get("status") == status]

        severity = str(filters.get("severity") or "").strip().upper()
        if severity in ("C", "A", "M", "B"):
            res = [i for i in res if i.get("severity") == severity]

        cls = str(filters.get("classification") or "").strip().upper()
        if cls == "PII_BREACH":
            res = [i for i in res if i["involves_personal_data"] and i.get("incident_type") in ("BF", "BI", "BD")]
        elif cls == "PI":
            res = [i for i in res if i.get("incident_type") == "PI"]
        elif cls == "TECH":
            res = [i for i in res if not i["involves_personal_data"] or i.get("incident_type") == "IT"]

        ctrl = str(filters.get("control_id") or "").strip().upper()
        if ctrl:
            res = [i for i in res if (i.get("iso27701_control_id") or "").upper() == ctrl]

        resp = str(filters.get("assigned_to") or "").strip().lower()
        if resp:
            res = [i for i in res if resp in (i.get("assigned_to") or "").lower()]

        has_mc = str(filters.get("has_mc") or "").strip().upper()
        if has_mc == "WITH_MC":
            res = [i for i in res if i.get("mc_id")]
        elif has_mc == "WITHOUT_MC":
            res = [i for i in res if not i.get("mc_id")]

        q = str(filters.get("q") or "").strip().lower()
        if q:
            res = [
                i for i in res
                if q in (i.get("incident_code") or "").lower()
                or q in (i.get("title") or "").lower()
                or q in (i.get("description") or "").lower()
                or q in (i.get("compromised_system") or "").lower()
                or q in (i.get("assigned_to") or "").lower()
                or q in (i.get("iso27701_control_id") or "").lower()
            ]
        return res

    def obtener_kpis_incidentes(self) -> Dict[str, Any]:
        items = self.listar_incidentes_unsa()
        mc_list = self.listar_medidas_correctivas()
        today = datetime.now().strftime("%Y-%m-%d")
        mc_pend = [m for m in mc_list if m.get("status") in ("ABIERTA", "EN_PROGRESO")]
        mc_vencidas = [m for m in mc_pend if m.get("due_date") and m["due_date"] < today]
        open_items = [i for i in items if i.get("status") in ("I", "E")]
        return {
            "total": len(items),
            "abiertos": len(open_items),
            "en_investigacion": len([i for i in items if i.get("status") == "I"]),
            "en_mitigacion": len([i for i in items if i.get("status") == "E"]),
            "cerrados": len([i for i in items if i.get("status") == "C"]),
            "criticos_abiertos": len([i for i in open_items if i.get("severity") == "C"]),
            "brechas_pii": len([i for i in items if i.get("involves_personal_data")]),
            "incidentes_tecnicos": len([i for i in items if not i.get("involves_personal_data")]),
            "mc_pendientes": len(mc_pend),
            "mc_vencidas": len(mc_vencidas),
        }

    def obtener_incidente_unsa(self, incident_id: int) -> Optional[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            cfg = self._config_row(conn)
            row = conn.execute(
                """
                SELECT ci.*,
                       ext.involves_personal_data AS ext_involves_personal_data,
                       ext.iso27701_control_id, ext.regla_codigo, ext.asset_id, ext.source_finding_id,
                       ext.consequences_summary, ext.data_recovered_status, ext.data_recovered_detail,
                       ext.anpd_notified, ext.anpd_notified_at, ext.anpd_official_ref, ext.anpd_delay_justification,
                       ext.subjects_notified, ext.subjects_notified_at, ext.subjects_notice_channel,
                       ext.multa_estimada_uit, ext.precedente_anpd,
                       ca.code AS asset_code, ca.name AS asset_name,
                       mc.id AS mc_id, mc.mc_code, mc.status AS mc_status, mc.due_date AS mc_due_date,
                       (SELECT COUNT(*) FROM core_incidentaction a WHERE a.incident_id = ci.id) AS actions_count,
                       (SELECT COUNT(*) FROM core_incidentattachment att WHERE att.incident_id = ci.id) AS attachments_count
                FROM core_incident ci
                LEFT JOIN a6_incident_ext ext ON ext.incident_id = ci.id
                LEFT JOIN core_asset ca ON ca.id = ext.asset_id
                LEFT JOIN a6_corrective_action mc ON mc.incident_id = ci.id
                WHERE ci.id = ? AND ci.is_deleted = 0
                """,
                (incident_id,),
            ).fetchone()
            return self._hydrate_incident(row, cfg["uit_value_pen"]) if row else None
        finally:
            conn.close()

    def _next_code(self, conn: sqlite3.Connection, table: str, column: str, prefix: str, year: int) -> str:
        like_pat = f"{prefix}-{year}-%"
        if table == "core_incident":
            rows = conn.execute("SELECT incident_code FROM core_incident WHERE incident_code LIKE ?", (like_pat,)).fetchall()
        elif table == "a6_corrective_action":
            rows = conn.execute("SELECT mc_code FROM a6_corrective_action WHERE mc_code LIKE ?", (like_pat,)).fetchall()
        else:
            raise ValueError(f"Tabla no soportada en _next_code: {table}")
        max_seq = 0
        for r in rows:
            try:
                seq = int(str(r[0]).split("-")[-1])
                max_seq = max(max_seq, seq)
            except (ValueError, IndexError) as exc:
                logger.debug("Omitiendo código malformado al calcular secuencia (%s)", type(exc).__name__)
        return f"{prefix}-{year}-{max_seq + 1:03d}"

    def crear_incidente(self, payload: Dict[str, Any], actor_id: Optional[int] = None) -> Dict[str, Any]:
        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cfg = self._config_row(conn)
            det_date = payload.get("detection_date") or datetime.now().strftime("%Y-%m-%d")
            inc_date = payload.get("incident_date") or det_date
            year = int(det_date[:4]) if len(det_date) >= 4 and det_date[:4].isdigit() else datetime.now().year
            inc_code = payload.get("incident_code") or self._next_code(conn, "core_incident", "incident_code", "INC-UNSA", year)

            involves_pii = 1 if payload.get("involves_personal_data", True) else 0
            inc_type = (payload.get("incident_type") or ("BF" if involves_pii else "IT")).upper()
            status = (payload.get("status") or "I").upper()
            severity = (payload.get("severity") or "M").upper()
            impact = (payload.get("impact") or severity).upper()

            assigned_name = payload.get("assigned_to") or ""
            assigned_uid = payload.get("assigned_to_id")
            if assigned_uid and not assigned_name:
                u = conn.execute("SELECT first_name, last_name FROM auth_user WHERE id = ?", (int(assigned_uid),)).fetchone()
                if u:
                    assigned_name = f"{u['first_name']} {u['last_name']}".strip()

            asset_id = payload.get("asset_id")
            comp_sys = payload.get("compromised_system") or ""
            if asset_id and not comp_sys:
                a = conn.execute("SELECT code, name FROM core_asset WHERE id = ?", (int(asset_id),)).fetchone()
                if a:
                    comp_sys = f"{a['name']} ({a['code']}, id={asset_id})"

            actor_name = self._actor_label(conn, actor_id)
            reported_by = payload.get("reported_by") or actor_name
            ctrl_id = payload.get("iso27701_control_id") or "A.3.12"
            regla_cod = payload.get("regla_codigo")
            multa_uit = float(payload.get("multa_estimada_uit") or 0.0)
            precedente = payload.get("precedente_anpd") or ""
            if regla_cod and not str(regla_cod).startswith("IA-") and regla_cod != "AUD-NC":
                rinfo = resolver_regla_con_fallback(regla_cod)
                ctrl_id = payload.get("iso27701_control_id") or rinfo["control_iso27701"]
                if not multa_uit:
                    multa_uit = float(rinfo["multa_estimada_uit"])
                if not precedente:
                    precedente = rinfo["precedente_anpd"]

            rep_parts = (cfg.get("legal_rep_name") or "Hugo Rojas Flores").split()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO core_incident (
                    created_at, updated_at, incident_code, rep_first_name, rep_last_name_p,
                    entity_ruc, entity_name, involves_personal_data,
                    incident_date, incident_time, detection_date, detection_time,
                    incident_type, status, severity, impact, title, description,
                    reported_by, assigned_to, affected_treatment,
                    dpo_contact_name, dpo_contact_email,
                    affected_data_types, num_affected_subjects, compromised_system, affected_url,
                    affected_cid, created_by_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now, now, inc_code, rep_parts[0], " ".join(rep_parts[1:]),
                    cfg["org_ruc"], cfg["org_name"], involves_pii,
                    inc_date, payload.get("incident_time") or "09:00:00",
                    det_date, payload.get("detection_time") or "09:30:00",
                    inc_type, status, severity, impact,
                    payload.get("title", "Incidente de Seguridad"),
                    payload.get("description", ""),
                    reported_by, assigned_name or cfg["dpo_name"],
                    payload.get("affected_treatment") or comp_sys,
                    cfg["dpo_name"], cfg["dpo_email"],
                    json.dumps(payload.get("affected_data_types") or [], ensure_ascii=False),
                    int(payload.get("num_affected_subjects") or 0),
                    comp_sys, payload.get("affected_url") or "",
                    json.dumps({"confidentiality": inc_type in ("BF", "PI"), "integrity": inc_type in ("BI", "PI"), "availability": inc_type in ("BD", "IT")}),
                    actor_id or 601,
                ),
            )
            inc_id = cur.lastrowid

            cur.execute(
                """
                INSERT INTO a6_incident_ext (
                    incident_id, involves_personal_data, iso27701_control_id, regla_codigo, asset_id, source_finding_id,
                    consequences_summary, data_recovered_status, data_recovered_detail,
                    anpd_notified, anpd_notified_at, anpd_official_ref, anpd_delay_justification,
                    subjects_notified, subjects_notified_at, subjects_notice_channel,
                    multa_estimada_uit, precedente_anpd, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    inc_id, involves_pii, ctrl_id, regla_cod, asset_id, payload.get("source_finding_id"),
                    payload.get("consequences_summary") or "",
                    payload.get("data_recovered_status") or ("NO_RECUPERADO" if involves_pii else "NO_APLICA"),
                    payload.get("data_recovered_detail") or "",
                    1 if payload.get("anpd_notified") else 0,
                    payload.get("anpd_notified_at"),
                    payload.get("anpd_official_ref"),
                    payload.get("anpd_delay_justification"),
                    1 if payload.get("subjects_notified") else 0,
                    payload.get("subjects_notified_at"),
                    payload.get("subjects_notice_channel"),
                    multa_uit, precedente, now,
                ),
            )

            cur.execute(
                """
                INSERT INTO core_incidenthistory (event_type, changed_at, actor, description, recipients_snapshot, changed_by_id, incident_id)
                VALUES ('CREACION', ?, ?, ?, ?, ?, ?)
                """,
                (now, actor_name, f"Registro inicial de incidente {inc_code} (Control {ctrl_id}).", cfg["dpo_email"], actor_id or 601, inc_id),
            )

            if payload.get("initial_action_description"):
                cur.execute(
                    """
                    INSERT INTO core_incidentaction (action_type, responsible, action_date, description, evidence, position, incident_id)
                    VALUES (?, ?, ?, ?, ?, 1, ?)
                    """,
                    (
                        payload.get("initial_action_type") or "C",
                        assigned_name or actor_name,
                        det_date,
                        payload["initial_action_description"],
                        payload.get("initial_action_evidence") or "Registro inicial de contención",
                        inc_id,
                    ),
                )

            if payload.get("create_mc_draft", True):
                mc_code = self._next_code(conn, "a6_corrective_action", "mc_code", "MC-UNSA", year)
                cur.execute(
                    """
                    INSERT INTO a6_corrective_action (
                        incident_id, mc_code, nonconformity_desc, identified_on, identified_by_id,
                        identified_by_name, action_required, action_to_implement, notify_who,
                        approved_by_name, responsible_id, responsible_name, status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, 'ABIERTA', ?, ?)
                    """,
                    (
                        inc_id, mc_code,
                        f"[{ctrl_id}] {payload.get('title', '')}. {payload.get('description', '')}".strip(),
                        det_date, actor_id or 601, reported_by,
                        payload.get("initial_mc_action") or "Definir e implementar acción correctiva permanente conforme a Cláusula 10.2 ISO/IEC 27701:2025.",
                        f"DPO UNSA ({cfg['dpo_email']}), CISO OTI",
                        cfg["dpo_name"], assigned_uid, assigned_name or cfg["dpo_name"], now, now,
                    ),
                )

            conn.commit()
        finally:
            conn.close()
        return self.obtener_incidente_unsa(inc_id)

    def actualizar_incidente(self, incident_id: int, payload: Dict[str, Any], actor_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            existing = conn.execute("SELECT id FROM core_incident WHERE id = ? AND is_deleted = 0", (incident_id,)).fetchone()
            if not existing:
                return None

            core_cols = {
                "title", "description", "severity", "impact", "incident_type",
                "involves_personal_data", "num_affected_subjects", "compromised_system",
                "affected_url", "affected_treatment", "incident_date", "detection_date",
                "detection_time", "reported_by", "assigned_to",
            }
            sets_core, params_core = [], []
            for k in core_cols:
                if k in payload:
                    val = (1 if payload[k] else 0) if k == "involves_personal_data" else payload[k]
                    sets_core.append(f"{k} = ?")
                    params_core.append(val)
            if "affected_data_types" in payload:
                sets_core.append("affected_data_types = ?")
                params_core.append(json.dumps(payload["affected_data_types"] or [], ensure_ascii=False))
            if sets_core:
                sets_core.append("updated_at = ?")
                params_core.extend([now, incident_id])
                sql_core = f"UPDATE core_incident SET {', '.join(sets_core)} WHERE id = ?"  # nosec B608: columns strictly allowlisted
                conn.execute(sql_core, params_core)

            ext_cols = {
                "involves_personal_data", "iso27701_control_id", "regla_codigo", "asset_id",
                "consequences_summary", "data_recovered_status", "data_recovered_detail",
                "anpd_notified", "anpd_notified_at", "anpd_official_ref", "anpd_delay_justification",
                "subjects_notified", "subjects_notified_at", "subjects_notice_channel",
                "multa_estimada_uit", "precedente_anpd",
            }
            sets_ext, params_ext = [], []
            for k in ext_cols:
                if k in payload:
                    val = (1 if payload[k] else 0) if k in ("involves_personal_data", "anpd_notified", "subjects_notified") else payload[k]
                    sets_ext.append(f"{k} = ?")
                    params_ext.append(val)
            if sets_ext:
                sets_ext.append("updated_at = ?")
                params_ext.extend([now, incident_id])
                sql_ext = f"UPDATE a6_incident_ext SET {', '.join(sets_ext)} WHERE incident_id = ?"  # nosec B608: columns strictly allowlisted
                conn.execute(sql_ext, params_ext)

            actor_name = self._actor_label(conn, actor_id)
            conn.execute(
                """
                INSERT INTO core_incidenthistory (event_type, changed_at, actor, description, changed_by_id, incident_id)
                VALUES ('ACTUALIZACION', ?, ?, 'Actualización de ficha de triaje B.3.12 / recuperación / notificaciones.', ?, ?)
                """,
                (now, actor_name, actor_id or 601, incident_id),
            )
            conn.commit()
        finally:
            conn.close()
        return self.obtener_incidente_unsa(incident_id)

    def asignar_incidente(
        self, incident_id: int, assigned_to_id: Optional[int] = None, assigned_to_name: Optional[str] = None, actor_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if not conn.execute("SELECT id FROM core_incident WHERE id = ? AND is_deleted = 0", (incident_id,)).fetchone():
                return None
            resolved_name = (assigned_to_name or "").strip()
            if assigned_to_id:
                u = conn.execute("SELECT first_name, last_name FROM auth_user WHERE id = ?", (assigned_to_id,)).fetchone()
                if u:
                    resolved_name = f"{u['first_name']} {u['last_name']}".strip()
            if not resolved_name:
                raise ValueError("Debe especificar un responsable válido.")

            conn.execute("UPDATE core_incident SET assigned_to = ?, updated_at = ? WHERE id = ?", (resolved_name, now, incident_id))
            actor_name = self._actor_label(conn, actor_id)
            conn.execute(
                """
                INSERT INTO core_incidenthistory (event_type, changed_at, actor, description, changed_by_id, incident_id)
                VALUES ('ASIGNACION', ?, ?, ?, ?, ?)
                """,
                (now, actor_name, f"Responsable asignado: {resolved_name}", actor_id or 601, incident_id),
            )
            conn.commit()
        finally:
            conn.close()
        return self.obtener_incidente_unsa(incident_id)

    def cambiar_estado_incidente(
        self, incident_id: int, new_status: str, actor_id: Optional[int] = None, reason: str = "", force: bool = False
    ) -> Dict[str, Any]:
        new_status = new_status.strip().upper()
        if new_status not in ("I", "E", "C"):
            raise ValueError("Estado inválido. Valores permitidos: I, E, C.")

        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().strftime("%Y-%m-%d")
        try:
            row = conn.execute("SELECT status FROM core_incident WHERE id = ? AND is_deleted = 0", (incident_id,)).fetchone()
            if not row:
                raise KeyError("Incidente no encontrado.")
            old_status = row["status"]

            if new_status == "C" and old_status != "C":
                cnt = conn.execute("SELECT COUNT(*) FROM core_incidentaction WHERE incident_id = ?", (incident_id,)).fetchone()[0]
                if cnt == 0 and not force:
                    raise ValueError("No se puede cerrar sin registrar al menos una acción de contención, remediación o mitigación (ISO/IEC 27701 A.3.12).")
                conn.execute(
                    "UPDATE core_incident SET status = 'C', resolved_date = ?, measure_considered_resolved = 'S', updated_at = ? WHERE id = ?",
                    (today, now, incident_id),
                )
                ev_type = "CIERRE"
                desc = reason.strip() or "Cierre formal tras verificación de acciones A.3.12."
            elif old_status == "C" and new_status in ("I", "E"):
                if not reason.strip() and not force:
                    raise ValueError("Para reabrir un incidente cerrado debe proporcionar un motivo obligatorio.")
                conn.execute(
                    "UPDATE core_incident SET status = ?, resolved_date = NULL, measure_considered_resolved = 'N', updated_at = ? WHERE id = ?",
                    (new_status, now, incident_id),
                )
                ev_type = "REAPERTURA"
                desc = f"Reapertura a estado {new_status}: {reason.strip() or 'Revisión solicitada'}"
            else:
                conn.execute("UPDATE core_incident SET status = ?, updated_at = ? WHERE id = ?", (new_status, now, incident_id))
                ev_type = "CAMBIO_ESTADO"
                desc = f"Transición de estado {old_status} -> {new_status}." + (f" Nota: {reason.strip()}" if reason.strip() else "")

            actor_name = self._actor_label(conn, actor_id)
            conn.execute(
                """
                INSERT INTO core_incidenthistory (event_type, changed_at, actor, description, changed_by_id, incident_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (ev_type, now, actor_name, desc, actor_id or 601, incident_id),
            )
            conn.commit()
        finally:
            conn.close()
        return self.obtener_incidente_unsa(incident_id)

    def actualizar_estado_incidente(self, incident_id: int, nuevo_estado: str) -> bool:
        try:
            self.cambiar_estado_incidente(incident_id, nuevo_estado, force=True)
            return True
        except Exception:
            return False

    # =========================================================================
    # 2. ACCIONES A.3.12, HISTORIAL Y ADJUNTOS A.3.14
    # =========================================================================

    def listar_acciones_incidente(self, incident_id: int) -> List[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM core_incidentaction WHERE incident_id = ? ORDER BY position ASC, id ASC",
                (incident_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def agregar_accion_incidente(self, incident_id: int, payload: Dict[str, Any], actor_id: Optional[int] = None) -> Dict[str, Any]:
        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            if not conn.execute("SELECT id FROM core_incident WHERE id = ?", (incident_id,)).fetchone():
                raise KeyError("Incidente no encontrado.")
            max_pos = conn.execute("SELECT COALESCE(MAX(position), 0) FROM core_incidentaction WHERE incident_id = ?", (incident_id,)).fetchone()[0]
            atype = (payload.get("action_type") or "C").upper()
            if atype not in ("C", "R", "M"):
                atype = "C"
            actor_name = self._actor_label(conn, actor_id)
            resp = payload.get("responsible") or actor_name
            adate = payload.get("action_date") or datetime.now().strftime("%Y-%m-%d")
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO core_incidentaction (action_type, responsible, action_date, description, evidence, position, incident_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (atype, resp, adate, payload.get("description", ""), payload.get("evidence", ""), max_pos + 1, incident_id),
            )
            aid = cur.lastrowid
            conn.execute(
                """
                INSERT INTO core_incidenthistory (event_type, changed_at, actor, description, changed_by_id, incident_id)
                VALUES ('ACCION_REGISTRADA', ?, ?, ?, ?, ?)
                """,
                (now, actor_name, f"Nueva acción [{atype}] asignada a {resp}: {payload.get('description', '')[:120]}", actor_id or 601, incident_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM core_incidentaction WHERE id = ?", (aid,)).fetchone()
            return dict(row)
        finally:
            conn.close()

    def eliminar_accion_incidente(self, incident_id: int, action_id: int, actor_id: Optional[int] = None) -> bool:
        conn = self._pims_conn()
        try:
            cur = conn.execute("DELETE FROM core_incidentaction WHERE id = ? AND incident_id = ?", (action_id, incident_id))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def listar_historial_incidente(self, incident_id: int) -> List[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM core_incidenthistory WHERE incident_id = ? ORDER BY changed_at ASC, id ASC",
                (incident_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def listar_adjuntos_incidente(self, incident_id: int) -> List[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM core_incidentattachment WHERE incident_id = ? ORDER BY uploaded_at DESC, id DESC",
                (incident_id,),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def agregar_adjunto_incidente(
        self, incident_id: int, rel_path: str, file_name: str, actor_id: Optional[int] = None
    ) -> Dict[str, Any]:
        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO core_incidentattachment (file, file_name, uploaded_at, incident_id, uploaded_by_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rel_path, file_name, now, incident_id, actor_id or 601),
            )
            att_id = cur.lastrowid
            actor_name = self._actor_label(conn, actor_id)
            conn.execute(
                """
                INSERT INTO core_incidenthistory (event_type, changed_at, actor, description, changed_by_id, incident_id)
                VALUES ('EVIDENCIA_ADJUNTA', ?, ?, ?, ?, ?)
                """,
                (now, actor_name, f"Evidencia adjuntada: {file_name}", actor_id or 601, incident_id),
            )
            conn.commit()
            return dict(conn.execute("SELECT * FROM core_incidentattachment WHERE id = ?", (att_id,)).fetchone())
        finally:
            conn.close()

    def obtener_adjunto(self, att_id: int) -> Optional[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            row = conn.execute("SELECT * FROM core_incidentattachment WHERE id = ?", (att_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # =========================================================================
    # 3. MEDIDAS CORRECTIVAS D34 (CLÁUSULA 10.2 / a6_corrective_action)
    # =========================================================================

    def obtener_medida_correctiva(self, incident_id: int) -> Optional[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            row = conn.execute("SELECT * FROM a6_corrective_action WHERE incident_id = ?", (incident_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def guardar_medida_correctiva(self, incident_id: int, payload: Dict[str, Any], actor_id: Optional[int] = None) -> Dict[str, Any]:
        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            inc = conn.execute("SELECT * FROM core_incident WHERE id = ? AND is_deleted = 0", (incident_id,)).fetchone()
            if not inc:
                raise KeyError("Incidente no encontrado.")
            existing = conn.execute("SELECT * FROM a6_corrective_action WHERE incident_id = ?", (incident_id,)).fetchone()
            cfg = self._config_row(conn)

            resp_name = payload.get("responsible_name")
            resp_id = payload.get("responsible_id")
            if resp_id and not resp_name:
                u = conn.execute("SELECT first_name, last_name FROM auth_user WHERE id = ?", (int(resp_id),)).fetchone()
                if u:
                    resp_name = f"{u['first_name']} {u['last_name']}".strip()

            fields = [
                "nonconformity_desc", "identified_on", "identified_by_id", "identified_by_name",
                "identified_signature", "root_cause", "similar_mc_ref", "action_required",
                "action_to_implement", "notify_who", "approved_by_name", "due_date",
                "responsible_id", "responsible_name", "implemented_on", "implemented_signature",
                "effectiveness_reviewed_on", "effectiveness_signature", "doc_changes_required",
                "doc_changes_signature", "status", "source_type", "iso27701_control_id",
            ]

            if existing:
                sets, params = [], []
                for f in fields:
                    if f in payload:
                        val = (1 if payload[f] else 0) if f == "action_required" else payload[f]
                        sets.append(f"{f} = ?")
                        params.append(val)
                if sets:
                    sets.append("updated_at = ?")
                    params.extend([now, incident_id])
                    sql_mc = f"UPDATE a6_corrective_action SET {', '.join(sets)} WHERE incident_id = ?"  # nosec B608: columns strictly allowlisted
                    conn.execute(sql_mc, params)
            else:
                year = int((inc["detection_date"] or "2026")[:4])
                mc_code = payload.get("mc_code") or self._next_code(conn, "a6_corrective_action", "mc_code", "MC-UNSA", year)
                conn.execute(
                    """
                    INSERT INTO a6_corrective_action (
                        incident_id, mc_code, nonconformity_desc, identified_on, identified_by_id,
                        identified_by_name, identified_signature, root_cause, similar_mc_ref, action_required,
                        action_to_implement, notify_who, approved_by_name, due_date, responsible_id,
                        responsible_name, implemented_on, implemented_signature, effectiveness_reviewed_on,
                        effectiveness_signature, doc_changes_required, doc_changes_signature, status,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id, mc_code,
                        payload.get("nonconformity_desc") or inc["title"],
                        payload.get("identified_on") or inc["detection_date"],
                        payload.get("identified_by_id") or actor_id or 601,
                        payload.get("identified_by_name") or inc["reported_by"],
                        payload.get("identified_signature") or "",
                        payload.get("root_cause") or "",
                        payload.get("similar_mc_ref") or "",
                        1 if payload.get("action_required", 1) else 0,
                        payload.get("action_to_implement") or "",
                        payload.get("notify_who") or cfg["dpo_name"],
                        payload.get("approved_by_name") or cfg["dpo_name"],
                        payload.get("due_date") or "",
                        resp_id, resp_name or inc["assigned_to"],
                        payload.get("implemented_on") or "",
                        payload.get("implemented_signature") or "",
                        payload.get("effectiveness_reviewed_on") or "",
                        payload.get("effectiveness_signature") or "",
                        payload.get("doc_changes_required") or "",
                        payload.get("doc_changes_signature") or "",
                        payload.get("status") or "ABIERTA",
                        now, now,
                    ),
                )

            actor_name = self._actor_label(conn, actor_id)
            conn.execute(
                """
                INSERT INTO core_incidenthistory (event_type, changed_at, actor, description, changed_by_id, incident_id)
                VALUES ('MC_ACTUALIZADA', ?, ?, ?, ?, ?)
                """,
                (now, actor_name, f"Formulario D34 actualizado (Estado: {payload.get('status', 'ABIERTA')}).", actor_id or 601, incident_id),
            )
            conn.commit()
            return dict(conn.execute("SELECT * FROM a6_corrective_action WHERE incident_id = ?", (incident_id,)).fetchone())
        finally:
            conn.close()

    def obtener_medida_correctiva_por_id(self, mc_id: int) -> Optional[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            row = conn.execute(
                """
                SELECT mc.*, ci.incident_code, ci.title AS incident_title, ci.severity AS incident_severity,
                       ci.status AS incident_status,
                       COALESCE(ext.iso27701_control_id, mc.iso27701_control_id, 'A.3.12') AS iso27701_control_id
                FROM a6_corrective_action mc
                LEFT JOIN core_incident ci ON ci.id = mc.incident_id
                LEFT JOIN a6_incident_ext ext ON ext.incident_id = ci.id
                WHERE mc.id = ? AND (ci.id IS NULL OR ci.is_deleted = 0)
                """,
                (mc_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def guardar_medida_correctiva_por_id(
        self, payload: Dict[str, Any], mc_id: Optional[int] = None, actor_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Crea o actualiza una Medida Correctiva D34 (con o sin incidente vinculado, Cláusula 10.2)."""
        inc_id = payload.get("incident_id")
        if inc_id is not None and str(inc_id).strip() != "":
            inc_id_int = int(inc_id)
            if mc_id is None:
                return self.guardar_medida_correctiva(inc_id_int, payload, actor_id=actor_id)
        else:
            inc_id_int = None

        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cfg = self._config_row(conn)
            resp_name = payload.get("responsible_name")
            resp_id = payload.get("responsible_id")
            if resp_id and not resp_name:
                u = conn.execute("SELECT first_name, last_name FROM auth_user WHERE id = ?", (int(resp_id),)).fetchone()
                if u:
                    resp_name = f"{u['first_name']} {u['last_name']}".strip()
            actor_name = self._actor_label(conn, actor_id)

            fields = [
                "incident_id", "nonconformity_desc", "identified_on", "identified_by_id", "identified_by_name",
                "identified_signature", "root_cause", "similar_mc_ref", "action_required",
                "action_to_implement", "notify_who", "approved_by_name", "due_date",
                "responsible_id", "responsible_name", "implemented_on", "implemented_signature",
                "effectiveness_reviewed_on", "effectiveness_signature", "doc_changes_required",
                "doc_changes_signature", "status", "source_type", "iso27701_control_id",
            ]

            if mc_id is not None:
                existing = conn.execute("SELECT * FROM a6_corrective_action WHERE id = ?", (mc_id,)).fetchone()
                if not existing:
                    raise KeyError("Medida correctiva no encontrada.")
                sets, params = [], []
                for f in fields:
                    if f in payload:
                        val = (1 if payload[f] else 0) if f == "action_required" else (inc_id_int if f == "incident_id" else payload[f])
                        sets.append(f"{f} = ?")
                        params.append(val)
                if sets:
                    sets.append("updated_at = ?")
                    params.extend([now, mc_id])
                    sql_mc = f"UPDATE a6_corrective_action SET {', '.join(sets)} WHERE id = ?"  # nosec B608: columns strictly allowlisted
                    conn.execute(sql_mc, params)
                new_id = mc_id
            else:
                ident_on = payload.get("identified_on") or datetime.now().strftime("%Y-%m-%d")
                year = int(ident_on[:4]) if len(ident_on) >= 4 and ident_on[:4].isdigit() else datetime.now().year
                mc_code = payload.get("mc_code") or self._next_code(conn, "a6_corrective_action", "mc_code", "MC-UNSA", year)
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO a6_corrective_action (
                        incident_id, mc_code, nonconformity_desc, identified_on, identified_by_id,
                        identified_by_name, identified_signature, root_cause, similar_mc_ref, action_required,
                        action_to_implement, notify_who, approved_by_name, due_date, responsible_id,
                        responsible_name, implemented_on, implemented_signature, effectiveness_reviewed_on,
                        effectiveness_signature, doc_changes_required, doc_changes_signature, status,
                        source_type, iso27701_control_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        inc_id_int, mc_code,
                        payload.get("nonconformity_desc") or "No conformidad registrada conforme a Cláusula 10.2.",
                        ident_on,
                        payload.get("identified_by_id") or actor_id or 601,
                        payload.get("identified_by_name") or actor_name,
                        payload.get("identified_signature") or "",
                        payload.get("root_cause") or "",
                        payload.get("similar_mc_ref") or "",
                        1 if payload.get("action_required", 1) else 0,
                        payload.get("action_to_implement") or "",
                        payload.get("notify_who") or cfg["dpo_name"],
                        payload.get("approved_by_name") or cfg["dpo_name"],
                        payload.get("due_date") or "",
                        resp_id, resp_name or actor_name,
                        payload.get("implemented_on") or "",
                        payload.get("implemented_signature") or "",
                        payload.get("effectiveness_reviewed_on") or "",
                        payload.get("effectiveness_signature") or "",
                        payload.get("doc_changes_required") or "",
                        payload.get("doc_changes_signature") or "",
                        payload.get("status") or "ABIERTA",
                        payload.get("source_type") or ("INCIDENTE" if inc_id_int else "MANUAL"),
                        payload.get("iso27701_control_id") or "A.3.12",
                        now, now,
                    ),
                )
                new_id = cur.lastrowid

            conn.commit()
        finally:
            conn.close()
        return self.obtener_medida_correctiva_por_id(new_id)  # type: ignore[return-value]

    def listar_medidas_correctivas(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            rows = conn.execute(
                """
                SELECT mc.*, ci.incident_code, ci.title AS incident_title, ci.severity AS incident_severity,
                       ci.status AS incident_status,
                       COALESCE(ext.iso27701_control_id, mc.iso27701_control_id, 'A.3.12') AS iso27701_control_id
                FROM a6_corrective_action mc
                LEFT JOIN core_incident ci ON ci.id = mc.incident_id
                LEFT JOIN a6_incident_ext ext ON ext.incident_id = ci.id
                WHERE (ci.id IS NULL OR ci.is_deleted = 0)
                ORDER BY mc.id DESC
                """
            ).fetchall()
            items = [dict(r) for r in rows]
            if status_filter and status_filter != "ALL":
                items = [m for m in items if m.get("status") == status_filter]
            return items
        finally:
            conn.close()

    # =========================================================================
    # 4. PROMOCIÓN DE HALLAZGO DSPM -> INCIDENTE REAL EN BD
    # =========================================================================

    def obtener_incidente_por_hallazgo(self, hallazgo_id: int) -> Optional[Dict[str, Any]]:
        """Retorna el incidente activo ya vinculado a un hallazgo DSPM, o None."""
        conn = self._pims_conn()
        try:
            row = conn.execute(
                """
                SELECT ci.id
                FROM a6_incident_ext ext
                JOIN core_incident ci ON ci.id = ext.incident_id
                WHERE ext.source_finding_id = ? AND ci.is_deleted = 0
                ORDER BY ci.id DESC
                LIMIT 1
                """,
                (hallazgo_id,),
            ).fetchone()
            inc_id = row["id"] if row else None
        finally:
            conn.close()
        return self.obtener_incidente_unsa(inc_id) if inc_id else None

    def promover_hallazgo_a_incidente(self, hallazgo_id: int, actor_id: Optional[int] = None) -> Dict[str, Any]:
        existing = self.obtener_incidente_por_hallazgo(hallazgo_id)
        if existing:
            return {"already_exists": True, "incident": existing}

        conn = self._pims_conn()
        try:
            h = conn.execute("SELECT * FROM hallazgos_dspm WHERE id = ?", (hallazgo_id,)).fetchone()
            if not h:
                raise KeyError("Hallazgo DSPM no encontrado.")
            hd = dict(h)
        finally:
            conn.close()

        regla = resolver_regla_con_fallback(hd.get("codigo_regla", "R-001"))
        sev = MAPA_SEVERIDAD_HALLAZGO.get(str(hd.get("nivel_riesgo", "MEDIO")).upper(), "M")
        inc_type = "PI" if regla.get("tipo_hallazgo") == "DOCUMENTAL" else "BF"
        inc = self.crear_incidente(
            {
                "title": f"{hd.get('titulo')} ({hd.get('elemento_afectado')})",
                "description": hd.get("descripcion"),
                "severity": sev,
                "impact": sev,
                "incident_type": inc_type,
                "involves_personal_data": True,
                "iso27701_control_id": regla["control_iso27701"] if regla else hd.get("control_iso27701", "A.3.12"),
                "regla_codigo": hd.get("codigo_regla"),
                "source_finding_id": hallazgo_id,
                "compromised_system": f"{hd.get('origen_archivo')} -> {hd.get('elemento_afectado')}",
                "multa_estimada_uit": hd.get("multa_estimada_uit", 5.0),
                "precedente_anpd": hd.get("precedente_anpd", ""),
                "reported_by": "Inspector SQL/PDF (DSPM UNSA)",
                "create_mc_draft": True,
                "initial_mc_action": regla.get("remediacion_sugerida", ""),
            },
            actor_id=actor_id,
        )
        return {"already_exists": False, "incident": inc}

    # =========================================================================
    # 5. DIRECTORIOS INSTITUCIONALES, LOGS Y REVISIÓN POR LA DIRECCIÓN D35
    # =========================================================================

    def listar_usuarios(self) -> List[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            rows = conn.execute(
                """
                SELECT u.id, u.username, u.first_name, u.last_name,
                       TRIM(u.first_name || ' ' || u.last_name) AS full_name,
                       u.email, u.is_active, u.is_superuser,
                       p.area, p.position, p.is_platform_admin
                FROM auth_user u
                LEFT JOIN core_userprofile p ON p.user_id = u.id
                WHERE u.is_active = 1
                ORDER BY u.id ASC
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def obtener_configuracion(self) -> Dict[str, Any]:
        conn = self._pims_conn()
        try:
            return self._config_row(conn)
        finally:
            conn.close()

    def actualizar_configuracion(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            allowed = {"org_name", "org_ruc", "legal_rep_name", "dpo_user_id", "dpo_name", "dpo_email", "ciso_user_id", "uit_value_pen"}
            sets, params = [], []
            for k in allowed:
                if k in payload:
                    sets.append(f"{k} = ?")
                    params.append(payload[k])
            if sets:
                sets.append("updated_at = ?")
                params.append(now)
                sql_cfg = f"UPDATE a6_system_config SET {', '.join(sets)} WHERE id = 1"  # nosec B608: columns strictly allowlisted
                conn.execute(sql_cfg, params)
                conn.commit()
            return self._config_row(conn)
        finally:
            conn.close()

    # =========================================================================
    # 5.1 SNAPSHOTS Y RESTAURACIÓN DE DEMOSTRACIÓN (1 SOLA BD SQLITE)
    # =========================================================================

    def _snapshot_path(self) -> str:
        from ..db import DB_PATH
        db_path = os.path.abspath(os.getenv("DATABASE_PATH", DB_PATH))
        return f"{db_path}.checkpoint.bak"

    def obtener_info_bd(self) -> Dict[str, Any]:
        from ..db import DB_PATH
        db_path = os.path.abspath(os.getenv("DATABASE_PATH", DB_PATH))
        snap_path = self._snapshot_path()
        conn = self._pims_conn()
        try:
            inc_count = conn.execute("SELECT COUNT(*) FROM core_incident WHERE is_deleted = 0").fetchone()[0]
            mc_count = conn.execute("SELECT COUNT(*) FROM a6_corrective_action").fetchone()[0]
            act_count = conn.execute("SELECT COUNT(*) FROM core_incidentaction").fetchone()[0]
        finally:
            conn.close()

        has_snap = os.path.exists(snap_path)
        snap_mtime = (
            datetime.fromtimestamp(os.path.getmtime(snap_path)).strftime("%Y-%m-%d %H:%M:%S")
            if has_snap else None
        )
        return {
            "db_path": db_path,
            "db_size_kb": round(os.path.getsize(db_path) / 1024, 1) if os.path.exists(db_path) else 0,
            "incidents_count": inc_count,
            "corrective_actions_count": mc_count,
            "actions_count": act_count,
            "has_checkpoint": has_snap,
            "checkpoint_updated_at": snap_mtime,
        }

    def crear_checkpoint_bd(self) -> Dict[str, Any]:
        """Guarda un punto de control binario usando sqlite3.Connection.backup() stdlib."""
        # ponytail: stdlib sqlite3 backup API works online without file locks on Windows
        snap_path = self._snapshot_path()
        src_conn = self._pims_conn()
        dst_conn = sqlite3.connect(snap_path)
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()
        return self.obtener_info_bd()

    def restaurar_checkpoint_bd(self) -> Dict[str, Any]:
        """Restaura la base de datos activa desde el último punto de control guardado."""
        snap_path = self._snapshot_path()
        if not os.path.exists(snap_path):
            raise FileNotFoundError("No existe un punto de control guardado para restaurar.")
        src_conn = sqlite3.connect(snap_path)
        dst_conn = self._pims_conn()
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
            src_conn.close()
        return self.obtener_info_bd()

    def restaurar_semilla_demo(self) -> Dict[str, Any]:
        """Restablece la base de datos al estado inicial canónico de demostración (15 incidentes 2023-2026)."""
        from .pims_schema import seed_pims_data
        conn = self._pims_conn()
        try:
            conn.executescript("""
                DELETE FROM core_incidentaction;
                DELETE FROM core_incidenthistory;
                DELETE FROM core_incidentattachment;
                DELETE FROM a6_corrective_action;
                DELETE FROM a6_incident_ext;
                DELETE FROM core_incident;
                DELETE FROM core_securitylog;
                DELETE FROM core_incidentrecipient;
                DELETE FROM core_asset;
                DELETE FROM core_userprofile;
                DELETE FROM auth_user;
                DELETE FROM a6_system_config;
            """)
            conn.commit()
            seed_pims_data(conn)
        finally:
            conn.close()
        return self.obtener_info_bd()

    def listar_destinatarios_notificacion(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            if include_inactive:
                rows = conn.execute("SELECT * FROM core_incidentrecipient ORDER BY id ASC").fetchall()
            else:
                rows = conn.execute("SELECT * FROM core_incidentrecipient WHERE is_active = 1 ORDER BY id ASC").fetchall()
            items = [dict(r) for r in rows]
            for it in items:
                it["is_active"] = bool(it.get("is_active", 1))
            return items
        finally:
            conn.close()

    def crear_destinatario(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        conn = self._pims_conn()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO core_incidentrecipient (email, label, is_active, created_at) VALUES (?, ?, ?, ?)",
                (payload["email"], payload.get("label", ""), 1 if payload.get("is_active", True) else 0, now),
            )
            rid = cur.lastrowid
            conn.commit()
            row = dict(conn.execute("SELECT * FROM core_incidentrecipient WHERE id = ?", (rid,)).fetchone())
            row["is_active"] = bool(row["is_active"])
            return row
        finally:
            conn.close()

    def actualizar_destinatario(self, rec_id: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            sets, params = [], []
            for k in ("email", "label", "is_active"):
                if k in payload:
                    val = (1 if payload[k] else 0) if k == "is_active" else payload[k]
                    sets.append(f"{k} = ?")
                    params.append(val)
            if sets:
                params.append(rec_id)
                sql_rec = f"UPDATE core_incidentrecipient SET {', '.join(sets)} WHERE id = ?"  # nosec B608: columns strictly allowlisted
                conn.execute(sql_rec, params)
                conn.commit()
            row = conn.execute("SELECT * FROM core_incidentrecipient WHERE id = ?", (rec_id,)).fetchone()
            if not row:
                return None
            res = dict(row)
            res["is_active"] = bool(res["is_active"])
            return res
        finally:
            conn.close()

    def listar_trazas_seguridad(self, incident_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retorna logs de seguridad filtrando por object_id = asset_id del incidente cuando aplica."""
        conn = self._pims_conn()
        try:
            if incident_id is not None:
                ext = conn.execute("SELECT asset_id FROM a6_incident_ext WHERE incident_id = ?", (incident_id,)).fetchone()
                if not ext or ext["asset_id"] is None:
                    return []
                rows = conn.execute(
                    "SELECT * FROM core_securitylog WHERE object_id = ? ORDER BY created_at DESC, id DESC LIMIT 50",
                    (ext["asset_id"],),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM core_securitylog ORDER BY id DESC LIMIT 50").fetchall()
            res = []
            for r in rows:
                d = dict(r)
                d["detail"] = _safe_json_loads(d.get("detail"), d.get("detail"))
                res.append(d)
            return res
        finally:
            conn.close()

    def listar_activos_unsa(self) -> List[Dict[str, Any]]:
        conn = self._pims_conn()
        try:
            rows = conn.execute("SELECT * FROM core_asset WHERE is_deleted = 0 ORDER BY id ASC").fetchall()
            res = []
            for r in rows:
                d = dict(r)
                d["pii_controls"] = _safe_json_loads(d.get("pii_controls"), [])
                d["data_categories"] = _safe_json_loads(d.get("data_categories"), [])
                res.append(d)
            return res
        finally:
            conn.close()

    def contar_incidentes_por_control(self) -> Dict[str, int]:
        conn = self._pims_conn()
        try:
            rows = conn.execute(
                """
                SELECT ext.iso27701_control_id, COUNT(*) AS cnt
                FROM a6_incident_ext ext
                JOIN core_incident ci ON ci.id = ext.incident_id
                WHERE ci.is_deleted = 0
                GROUP BY ext.iso27701_control_id
                """
            ).fetchall()
            return {r["iso27701_control_id"]: r["cnt"] for r in rows if r["iso27701_control_id"]}
        finally:
            conn.close()

    def obtener_resumen_revision_direccion_d35(self) -> Dict[str, Any]:
        """Agrega métricas reales 2023-2026 para el informe D35 (Cláusula 9.3)."""
        items = self.listar_incidentes_unsa()
        mc_list = self.listar_medidas_correctivas()
        cfg = self.obtener_configuracion()

        years_map: Dict[int, Dict[str, int]] = {}
        crit_by_resp: Dict[str, Dict[str, Any]] = {}
        ctrl_counts: Dict[str, int] = {}

        for i in items:
            y = i["year"]
            ym = years_map.setdefault(y, {"year": y, "total": 0, "open": 0, "closed": 0, "critical": 0, "pii": 0, "tech": 0})
            ym["total"] += 1
            if i["status"] == "C":
                ym["closed"] += 1
            else:
                ym["open"] += 1
            if i["severity"] == "C":
                ym["critical"] += 1
            if i["involves_personal_data"]:
                ym["pii"] += 1
            else:
                ym["tech"] += 1

            ctrl = i.get("iso27701_control_id") or "A.3.12"
            ctrl_counts[ctrl] = ctrl_counts.get(ctrl, 0) + 1

            if i["status"] != "C" and i["severity"] == "C":
                resp = i.get("assigned_to") or "Sin asignar"
                entry = crit_by_resp.setdefault(resp, {"responsible": resp, "count": 0, "codes": []})
                entry["count"] += 1
                entry["codes"].append(i["incident_code"])

        open_list = [i for i in items if i["status"] != "C"]
        disruptive = [i for i in items if i.get("severity") in ("C", "A")][:6]
        users = self.listar_usuarios()
        sin_mc = [i for i in items if not i.get("mc_id")]
        mc_pend = [m for m in mc_list if m["status"] in ("ABIERTA", "EN_PROGRESO")]
        return {
            "config": cfg,
            "users": users,
            "total_incidents": len(items),
            "open_incidents": len(open_list),
            "closed_incidents": len(items) - len(open_list),
            "open_critical": len([i for i in open_list if i["severity"] == "C"]),
            "pii_incidents": len([i for i in items if i["involves_personal_data"]]),
            "tech_non_pii": len([i for i in items if not i["involves_personal_data"]]),
            "by_year": [years_map[y] for y in sorted(years_map.keys())],
            "open_critical_by_responsible": sorted(crit_by_resp.values(), key=lambda x: -x["count"]),
            "disruptive_incidents": disruptive,
            "mc_items": mc_list,
            "top_controls": [
                {"control_id": k, "count": v}
                for k, v in sorted(ctrl_counts.items(), key=lambda kv: -kv[1])[:8]
            ],
            "corrective_actions": {
                "total": len(mc_list),
                "abiertas": len([m for m in mc_list if m["status"] == "ABIERTA"]),
                "en_progreso": len([m for m in mc_list if m["status"] == "EN_PROGRESO"]),
                "implementadas": len([m for m in mc_list if m["status"] == "IMPLEMENTADA"]),
                "verificadas": len([m for m in mc_list if m["status"] == "VERIFICADA"]),
                "pendientes": len(mc_pend),
            },
            "procedure_kpis": {
                "mc_iniciadas": len(mc_list),
                "mc_incompletas": len(mc_pend),
                "incidentes_sin_formulario_d34": len(sin_mc),
            },
        }

    # =========================================================================
    # 6. OPERACIONES HEREDADAS DSPM (Inspector SQL / PDF)
    # =========================================================================

    def resetear_base_de_datos(self) -> None:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM interacciones_coach")
        cur.execute("DELETE FROM hallazgos_dspm")
        cur.execute("DELETE FROM clausulas_documentales")
        cur.execute("DELETE FROM inventario_activos_datos")
        cur.execute("DELETE FROM archivos_cargados")
        conn.commit()
        conn.close()

    def obtener_estadisticas_globales(self) -> Dict[str, int]:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM archivos_cargados")
        num_archivos = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) as cnt FROM inventario_activos_datos")
        num_activos = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) as cnt FROM hallazgos_dspm")
        num_hallazgos = cur.fetchone()["cnt"]
        conn.close()
        return {"num_archivos": num_archivos, "num_activos": num_activos, "num_hallazgos": num_hallazgos}

    def registrar_archivo(self, nombre: str, tipo: str, tamano: int, resumen: Optional[str] = None) -> int:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO archivos_cargados (nombre_archivo, tipo_archivo, fecha_carga, tamano_bytes, resumen_analisis)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nombre, tipo, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tamano, resumen or ""),
        )
        conn.commit()
        file_id = cur.lastrowid
        conn.close()
        return file_id

    def registrar_activo_columna(self, activo: Dict[str, Any]) -> int:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO inventario_activos_datos (
                archivo_id, nombre_tabla, nombre_columna, tipo_sql,
                es_clave_primaria, es_clave_foranea, categoria_sensible,
                es_dato_sensible, nivel_confianza, candado_deteccion, recomendacion_seguridad
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                activo.get("archivo_id"), activo["nombre_tabla"], activo["nombre_columna"],
                activo["tipo_sql"], 1 if activo.get("es_clave_primaria") else 0,
                1 if activo.get("es_clave_foranea") else 0, activo.get("categoria_sensible", "NO_SENSIBLE"),
                1 if activo.get("es_dato_sensible") else 0, activo.get("nivel_confianza", 1.0),
                activo.get("candado_deteccion"), activo.get("recomendacion_seguridad"),
            ),
        )
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return last_id

    def registrar_clausula(self, clausula: Dict[str, Any]) -> int:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO clausulas_documentales (
                archivo_id, documento, numero_clausula, titulo_clausula,
                texto_clausula, tipo_clausula, estado_cumplimiento, alerta_legal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clausula.get("archivo_id"), clausula["documento"], clausula.get("numero_clausula"),
                clausula.get("titulo_clausula"), clausula["texto_clausula"], clausula.get("tipo_clausula"),
                clausula.get("estado_cumplimiento", "OBSERVADO"), clausula.get("alerta_legal"),
            ),
        )
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return last_id

    def limpiar_hallazgos(self) -> None:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM hallazgos_dspm")
        conn.commit()
        conn.close()

    def insertar_hallazgo(self, hallazgo: Dict[str, Any]) -> int:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO hallazgos_dspm (
                codigo_regla, titulo, descripcion, nivel_riesgo, elemento_afectado, origen_archivo,
                control_iso27701, principio_iso29100, articulo_ley29733, directiva_seguridad,
                multa_estimada_uit, multa_estimada_pen, precedente_anpd, fecha_deteccion, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hallazgo["codigo_regla"], hallazgo["titulo"], hallazgo["descripcion"],
                hallazgo["nivel_riesgo"], hallazgo["elemento_afectado"], hallazgo["origen_archivo"],
                hallazgo["control_iso27701"], hallazgo["principio_iso29100"], hallazgo["articulo_ley29733"],
                hallazgo["directiva_seguridad"], hallazgo["multa_estimada_uit"], hallazgo["multa_estimada_pen"],
                hallazgo["precedente_anpd"], hallazgo.get("fecha_deteccion", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                hallazgo.get("estado", "PENDIENTE"),
            ),
        )
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return last_id

    def obtener_todos_los_hallazgos(self) -> List[Dict[str, Any]]:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM hallazgos_dspm ORDER BY multa_estimada_uit DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def obtener_hallazgo_por_id(self, hallazgo_id: int) -> Optional[Dict[str, Any]]:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM hallazgos_dspm WHERE id = ?", (hallazgo_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def obtener_vista_completa_base_datos(self) -> Dict[str, List[Dict[str, Any]]]:
        conn = self._pims_conn()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM archivos_cargados ORDER BY id DESC")
            archivos = [dict(r) for r in cur.fetchall()]
            cur.execute("SELECT * FROM inventario_activos_datos ORDER BY id ASC")
            inventario = [dict(r) for r in cur.fetchall()]
            cur.execute("SELECT * FROM clausulas_documentales ORDER BY id ASC")
            clausulas = [dict(r) for r in cur.fetchall()]
            cur.execute("""
                SELECT h.*,
                       (SELECT ci.id FROM a6_incident_ext ext
                        JOIN core_incident ci ON ci.id = ext.incident_id
                        WHERE ext.source_finding_id = h.id AND ci.is_deleted = 0
                        ORDER BY ci.id DESC LIMIT 1) AS promoted_incident_id,
                       (SELECT ci.incident_code FROM a6_incident_ext ext
                        JOIN core_incident ci ON ci.id = ext.incident_id
                        WHERE ext.source_finding_id = h.id AND ci.is_deleted = 0
                        ORDER BY ci.id DESC LIMIT 1) AS promoted_incident_code
                FROM hallazgos_dspm h
                ORDER BY h.multa_estimada_uit DESC
            """)
            hallazgos = [dict(r) for r in cur.fetchall()]
            return {"archivos": archivos, "inventario": inventario, "clausulas": clausulas, "hallazgos": hallazgos}
        finally:
            conn.close()

    def guardar_interaccion_coach(
        self, hallazgo_id: int, rol: str, mensaje: str, reasoning: Optional[str] = None, parche: Optional[str] = None
    ) -> int:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO interacciones_coach (hallazgo_id, timestamp, rol, mensaje, pensamiento_reasoning, parche_sql)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (hallazgo_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rol, mensaje, reasoning or "", parche or ""),
        )
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return last_id

    def obtener_interacciones_por_hallazgo(self, hallazgo_id: int) -> List[Dict[str, Any]]:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM interacciones_coach WHERE hallazgo_id = ? ORDER BY id ASC", (hallazgo_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def actualizar_estado_hallazgo(self, hallazgo_id: int, nuevo_estado: str) -> bool:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("UPDATE hallazgos_dspm SET estado = ? WHERE id = ?", (nuevo_estado, hallazgo_id))
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return affected > 0


repository = AuditRepository()
__all__ = ["repository", "AuditRepository"]
