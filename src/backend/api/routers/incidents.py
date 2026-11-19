"""
Router de Gestión de Incidentes de Seguridad, Brechas de PII y Medidas Correctivas (Agente 6).
Marco normativo principal: ISO/IEC 27701:2025 (Cl. 8.1, A.3.11, A.3.12, Cl. 10.2).
"""

import json
import logging
import os
import re
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Header, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from ...core.rules_catalog import resolver_regla_con_fallback
from ...db import DEFAULT_DB_PATH
from ...infrastructure.llm_client import default_luna_client
from ...infrastructure.repository import MAPA_SEVERIDAD_HALLAZGO, repository
from ...knowledge_bridge import knowledge_bridge
from ...services.docx_exporter import (
    PIMS_TEMPLATES_CATALOG,
    export_audit_nonconformities_docx,
    export_blank_template_docx,
    export_corrective_action_docx,
    export_corrective_procedure_docx,
    export_incident_dossier_docx,
    export_management_review_d35_docx,
    export_management_review_d35_markdown,
)
from ...services.docx_importer import parse_d34_docx, parse_incident_report_docx

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Incidents"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
MEDIA_DIR = os.path.join(BASE_DIR, "media")


def _get_writable_evidences_dir() -> str:
    """Retorna directorio escribible junto a la BD activa (compatible con read_only: true en Docker/VPS)."""
    db_path = os.path.abspath(os.getenv("DATABASE_PATH", DEFAULT_DB_PATH))
    return os.path.join(os.path.dirname(db_path), "evidencias_uploads")


MAPA_EVIDENCIA_DOCUMENTAL = {
    "R-001": {
        "documento_fuente_pdf": "Manual_Procedimientos_Hospital_Docente_Zamacola_UNSA.pdf",
        "descripcion_documento": "Manual de Procedimientos y Custodia de Historias Clínicas (Hospital Docente Zamácola)",
        "esquema_fuente_sql": "schema_unsa_servicios_centrales.sql",
        "tabla_afectada": "pacientes_hospital_zamacola",
        "columnas_afectadas": ["diagnostico_cie10", "tratamiento_medico", "historia_clinica_numero"],
        "evidencia_texto": "Tabla pacientes_hospital_zamacola: diagnósticos y tratamientos en texto plano sin cifrado AES-256 en reposo (A.3.26).",
        "url_pdf_raw": "/api/documents/raw?filename=Manual_Procedimientos_Hospital_Docente_Zamacola_UNSA.pdf",
        "url_sql_raw": "/api/documents/raw?filename=schema_unsa_servicios_centrales.sql",
    },
    "R-002": {
        "documento_fuente_pdf": "RCU_0085_2026_Reglamento_Admision_Pregrado_UNSA_v5.pdf",
        "descripcion_documento": "Reglamento Oficial Proceso de Admisión Pregrado v5 vigente",
        "esquema_fuente_sql": "schema_unsa_servicios_centrales.sql",
        "tabla_afectada": "usuarios_admision_sisunsa",
        "columnas_afectadas": ["password_hash", "dni_postulante"],
        "evidencia_texto": "Tabla usuarios_admision_sisunsa: contraseñas almacenadas con MD5 sin salt (A.3.23).",
        "url_pdf_raw": "/api/documents/raw?filename=RCU_0085_2026_Reglamento_Admision_Pregrado_UNSA_v5.pdf",
        "url_sql_raw": "/api/documents/raw?filename=schema_unsa_servicios_centrales.sql",
    },
    "R-003": {
        "documento_fuente_pdf": "Convenio_Pasarela_Pagos_Tesoreria_BancoNacion_UNSA.pdf",
        "descripcion_documento": "Convenio de Recaudación Electrónica Págalo.pe (R.R. 0178-2025)",
        "esquema_fuente_sql": "schema_unsa_servicios_centrales.sql",
        "tabla_afectada": "transacciones_pagos_tesoreria",
        "columnas_afectadas": ["numero_tarjeta_pan", "codigo_seguridad_cvv", "titular_tarjeta"],
        "evidencia_texto": "Tabla transacciones_pagos_tesoreria: retención indebida de CVV y PAN tras autorización de pago (A.1.4.5).",
        "url_pdf_raw": "/api/documents/raw?filename=Convenio_Pasarela_Pagos_Tesoreria_BancoNacion_UNSA.pdf",
        "url_sql_raw": "/api/documents/raw?filename=schema_unsa_servicios_centrales.sql",
    },
    "R-004": {
        "documento_fuente_pdf": "Reglamento_Comedor_Universitario_SISCOM_UNSA.pdf",
        "descripcion_documento": "Reglamento de Bienestar Estudiantil y Comedores SISCOM",
        "esquema_fuente_sql": None,
        "tabla_afectada": "fichas_socioeconomicas_comedor",
        "columnas_afectadas": ["autorizacion_cesion_publicitaria"],
        "evidencia_texto": "Ficha SISCOM: casilla pre-marcada obligatoria para cesión comercial (A.1.2.4).",
        "url_pdf_raw": "/api/documents/raw?filename=Reglamento_Comedor_Universitario_SISCOM_UNSA.pdf",
        "url_sql_raw": None,
    },
    "R-005": {
        "documento_fuente_pdf": "Reglamento_Admision_Pregrado_UNSA_2026.pdf",
        "descripcion_documento": "Reglamento General de Admisión Pregrado (Biometría, Huella)",
        "esquema_fuente_sql": "schema_unsa_servicios_centrales.sql",
        "tabla_afectada": "postulantes_biometria_historico",
        "columnas_afectadas": ["minucia_huella_dactilar", "patron_facial_biometrico"],
        "evidencia_texto": "Conservación indefinida de huellas y biometría facial sin política de supresión (A.1.4.8).",
        "url_pdf_raw": "/api/documents/raw?filename=Reglamento_Admision_Pregrado_UNSA_2026.pdf",
        "url_sql_raw": "/api/documents/raw?filename=schema_unsa_servicios_centrales.sql",
    },
    "R-006": {
        "documento_fuente_pdf": "Contrato_DPA_Google_Workspace_Education_UNSA_2026.pdf",
        "descripcion_documento": "Acuerdo de Tratamiento de Datos (DPA) Google Workspace for Education",
        "esquema_fuente_sql": None,
        "tabla_afectada": "backups_s3_cloud_eu_west",
        "columnas_afectadas": ["expedientes_academicos_tar"],
        "evidencia_texto": "Transferencia transfronteriza de respaldos a región eu-west-1 sin DPA/SCC ni registro (A.1.5.2).",
        "url_pdf_raw": "/api/documents/raw?filename=Contrato_DPA_Google_Workspace_Education_UNSA_2026.pdf",
        "url_sql_raw": None,
    },
    "R-007": {
        "documento_fuente_pdf": "TUPA_UNSA_Procedimientos_Administrativos_2026.pdf",
        "descripcion_documento": "TUPA Institucional UNSA (Procedimientos ARCO)",
        "esquema_fuente_sql": None,
        "tabla_afectada": "solicitudes_arco_tramited",
        "columnas_afectadas": ["comprobante_pago_tupa"],
        "evidencia_texto": "Procedimiento N° 14 TUPA: cobro de tasa y exigencia notarial para derechos ARCO (A.1.3.7).",
        "url_pdf_raw": "/api/documents/raw?filename=TUPA_UNSA_Procedimientos_Administrativos_2026.pdf",
        "url_sql_raw": None,
    },
}


class IncidentCreate(BaseModel):
    title: str
    description: str = ""
    incident_date: Optional[str] = None
    incident_time: Optional[str] = None
    detection_date: Optional[str] = None
    detection_time: Optional[str] = None
    involves_personal_data: bool = True
    incident_type: Optional[str] = None
    severity: str = "M"
    impact: Optional[str] = None
    iso27701_control_id: str = "A.3.12"
    regla_codigo: Optional[str] = None
    asset_id: Optional[int] = None
    compromised_system: Optional[str] = None
    affected_url: Optional[str] = None
    affected_data_types: List[str] = Field(default_factory=list)
    num_affected_subjects: int = 0
    assigned_to_id: Optional[int] = None
    assigned_to: Optional[str] = None
    reported_by: Optional[str] = None
    consequences_summary: Optional[str] = None
    data_recovered_status: Optional[str] = None
    data_recovered_detail: Optional[str] = None
    anpd_notified: bool = False
    anpd_notified_at: Optional[str] = None
    anpd_official_ref: Optional[str] = None
    anpd_delay_justification: Optional[str] = None
    subjects_notified: bool = False
    subjects_notified_at: Optional[str] = None
    subjects_notice_channel: Optional[str] = None
    initial_action_type: Optional[str] = "C"
    initial_action_description: Optional[str] = None
    initial_action_evidence: Optional[str] = None
    initial_mc_action: Optional[str] = None
    source_finding_id: Optional[int] = None
    multa_estimada_uit: Optional[float] = 0.0
    precedente_anpd: Optional[str] = None
    create_mc_draft: bool = True


class IncidentAssign(BaseModel):
    assigned_to_id: Optional[int] = None
    assigned_to: Optional[str] = None


class IncidentStatusChange(BaseModel):
    status: str
    reason: str = ""
    force: bool = False


class ActionCreate(BaseModel):
    action_type: str = "C"
    responsible: Optional[str] = None
    action_date: Optional[str] = None
    description: str
    evidence: str = ""


class RecipientCreate(BaseModel):
    email: str
    label: str = ""
    is_active: bool = True


def _actor(x_actor_id: Optional[int]) -> Optional[int]:
    return x_actor_id


@router.get("/api/incidents")
def list_incidents(
    year: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    classification: Optional[str] = None,
    control_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    has_mc: Optional[str] = None,
    q: Optional[str] = None,
):
    """Retorna incidentes filtrados y KPIs operativos en tiempo real."""
    filters = {
        "year": year,
        "status": status,
        "severity": severity,
        "classification": classification,
        "control_id": control_id,
        "assigned_to": assigned_to,
        "has_mc": has_mc,
        "q": q,
    }
    incidentes = repository.listar_incidentes_unsa(filters)
    enriquecidos = []
    for inc in incidentes:
        item = dict(inc)
        regla_cod = inc.get("regla_codigo")
        evidencia = MAPA_EVIDENCIA_DOCUMENTAL.get(regla_cod, {}) if regla_cod else {}
        item.update({
            "documento_fuente_pdf": evidencia.get("documento_fuente_pdf"),
            "esquema_fuente_sql": evidencia.get("esquema_fuente_sql"),
            "tabla_afectada": evidencia.get("tabla_afectada"),
            "url_pdf_raw": evidencia.get("url_pdf_raw"),
            "url_sql_raw": evidencia.get("url_sql_raw"),
        })
        enriquecidos.append(item)

    return {
        "incidents": enriquecidos,
        "incidentes": enriquecidos,
        "total": len(enriquecidos),
        "kpis": repository.obtener_kpis_incidentes(),
    }


@router.post("/api/incidents", status_code=201)
def create_incident(payload: IncidentCreate, x_actor_id: Optional[int] = Header(default=None)):
    """Crea un nuevo incidente o brecha PII (3 pasos) + borrador opcional de MC 10.2."""
    inc = repository.crear_incidente(payload.model_dump(), actor_id=_actor(x_actor_id))
    return {"incident": inc, "mensaje": f"Incidente {inc['incident_code']} registrado con éxito."}


_FINDING_ASSET_USER_MAP = {
    "R-001": (102, 605),
    "R-002": (103, 602),
    "R-003": (108, 608),
    "R-004": (110, 601),
    "R-005": (103, 602),
    "R-006": (101, 609),
    "R-007": (107, 607),
}


def _build_draft_from_finding(hd: Dict[str, Any]) -> tuple[Dict[str, Any], bool]:
    """Construye un borrador completo de 3 pasos desde un hallazgo DSPM/IA/Auditoría y lo enriquece con IA."""
    rule_code = str(hd.get("codigo_regla") or "R-001").upper()
    is_custom_rule = rule_code.startswith("IA-") or rule_code == "AUD-NC"
    regla = None if is_custom_rule else resolver_regla_con_fallback(rule_code)
    ctrl_id = ((regla.get("control_iso27701") if regla else None) or hd.get("control_iso27701") or "A.3.12").upper()
    ctrl = knowledge_bridge.engine.get_control(ctrl_id) or {}

    sev = MAPA_SEVERIDAD_HALLAZGO.get(str(hd.get("nivel_riesgo", "MEDIO")).upper(), "M")
    if regla:
        inc_type = "PI" if regla.get("tipo_hallazgo") == "DOCUMENTAL" else "BF"
    else:
        inc_type = "PI" if (ctrl_id.startswith("A.1") or ctrl_id.startswith("A.2") or rule_code == "AUD-NC") else "BF"
    asset_id, user_id = _FINDING_ASSET_USER_MAP.get(rule_code, (101, 601))
    today = datetime.now().strftime("%Y-%m-%d")

    elemento = hd.get("elemento_afectado") or ""
    origen = hd.get("origen_archivo") or "Inspector DSPM"
    remed = (regla.get("remediacion_sugerida") if regla else None) or ctrl.get("annex_b_guidance") or ""

    draft: Dict[str, Any] = {
        "title": f"{hd.get('titulo')} ({elemento})".strip(),
        "description": (hd.get("descripcion") or "").strip(),
        "incident_date": today,
        "detection_date": today,
        "asset_id": asset_id,
        "compromised_system": f"{origen} -> {elemento}".strip(),
        "affected_url": "",
        "involves_personal_data": True,
        "incident_type": inc_type,
        "severity": sev,
        "impact": sev,
        "iso27701_control_id": ctrl_id,
        "num_affected_subjects": 0,
        "consequences_summary": (
            f"Exposición normativa/técnica detectada en {origen} ({elemento}). "
            f"Referencia sancionadora estimada: {hd.get('multa_estimada_uit', 5.0)} UIT."
        ),
        "assigned_to_id": user_id,
        "initial_action_type": "C" if inc_type != "PI" else "M",
        "initial_action_description": remed,
        "initial_mc_action": remed,
        "source_finding_id": hd["id"],
        "regla_codigo": rule_code,
        "multa_estimada_uit": float(hd.get("multa_estimada_uit") or 0.0),
        "precedente_anpd": hd.get("precedente_anpd") or "",
        "reported_by": "Inspector SQL/PDF (DSPM UNSA)",
        "create_mc_draft": True,
    }

    ai_enriched = False
    prompt = (
        "Completa un borrador JSON estricto (claves exactas: title, description, consequences_summary, initial_action_description) "
        "en español técnico-jurídico conciso para registrar un incidente/brecha PII en ISO/IEC 27701:2025.\n"
        f"Regla DSPM: {rule_code} - {hd.get('titulo')}\n"
        f"Archivo fuente: {origen} | Elemento afectado: {elemento}\n"
        f"Descripción técnica base: {hd.get('descripcion')}\n"
        f"Control ISO/IEC 27701:2025: {ctrl_id} ({ctrl.get('title', '')})\n"
        f"Guía Anexo B: {ctrl.get('annex_b_guidance', '')}\n"
        f"Precedente ANPD: {hd.get('precedente_anpd', '')}\n"
        "Responde ÚNICAMENTE con un objeto JSON válido sin markdown."
    )
    try:
        resp = default_luna_client.generate(
            messages=[
                {"role": "system", "content": "Eres auditor PIMS ISO/IEC 27701:2025. Responde SOLO JSON válido."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        m = re.search(r"\{.*\}", resp.content or "", re.DOTALL)
        if resp.mode != "error" and m:
            parsed = json.loads(m.group(0))
            updated_any = False
            for k in ("title", "description", "consequences_summary", "initial_action_description"):
                val = parsed.get(k)
                if isinstance(val, str) and val.strip():
                    draft[k] = val.strip()
                    updated_any = True
            if updated_any:
                draft["initial_mc_action"] = draft["initial_action_description"]
                ai_enriched = True
    except Exception as exc:
        logger.warning("Enriquecimiento IA para borrador DSPM omitido: %s", type(exc).__name__)

    return draft, ai_enriched


@router.post("/api/incidents/draft-from-finding/{hallazgo_id}")
def draft_incident_from_finding(hallazgo_id: int):
    """Genera un borrador autocompletado (DSPM + IA) para revisar en el modal de 3 pasos sin guardar aún."""
    existing = repository.obtener_incidente_por_hallazgo(hallazgo_id)
    if existing:
        return {
            "already_exists": True,
            "ai_enriched": False,
            "incident": existing,
            "draft": None,
            "mensaje": f"El hallazgo ya fue registrado como {existing['incident_code']}.",
        }

    hd = repository.obtener_hallazgo_por_id(hallazgo_id)
    if not hd:
        raise HTTPException(status_code=404, detail="Hallazgo DSPM no encontrado.")

    draft, ai_enriched = _build_draft_from_finding(hd)
    return {
        "already_exists": False,
        "ai_enriched": ai_enriched,
        "incident": None,
        "draft": draft,
        "hallazgo": hd,
    }


@router.post("/api/incidents/import-docx")
async def import_incident_from_docx(file: UploadFile = File(...)):
    """Importa una ficha o reporte Word (.docx) hacia borrador de 3 pasos sin guardar todavía."""
    fname = os.path.basename(file.filename or "")
    if not fname.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Debe subir un archivo Word con extensión .docx.")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="El archivo .docx está vacío.")
    try:
        draft, ai_enriched = parse_incident_report_docx(raw, fname)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo interpretar el archivo .docx: {exc}") from exc
    return {
        "draft": draft,
        "ai_enriched": ai_enriched,
        "filename": fname,
        "mensaje": f"Archivo '{fname}' importado como borrador de 3 pasos. Revise y confirme.",
    }


@router.post("/api/incidents/from-finding/{hallazgo_id}")
def promote_finding_to_incident(hallazgo_id: int, x_actor_id: Optional[int] = Header(default=None)):
    """Promueve un hallazgo detectado por Inspector SQL/PDF a un incidente persistente en BD."""
    try:
        res = repository.promover_hallazgo_a_incidente(hallazgo_id, actor_id=_actor(x_actor_id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Hallazgo DSPM no encontrado.")
    msg = (
        f"El hallazgo ya estaba vinculado al incidente {res['incident']['incident_code']}."
        if res["already_exists"]
        else f"Hallazgo promovido a incidente {res['incident']['incident_code']}."
    )
    return {**res, "mensaje": msg}


@router.get("/api/incidents/{incident_id}")
def get_incident(incident_id: int):
    """Retorna expediente completo del incidente (evaluación B.3.12, acciones, MC 10.2, adjuntos y bitácora)."""
    inc = repository.obtener_incidente_unsa(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    regla_codigo = inc.get("regla_codigo")
    regla_info = resolver_regla_con_fallback(regla_codigo) if regla_codigo else None
    evidencia = MAPA_EVIDENCIA_DOCUMENTAL.get(regla_codigo, {}) if regla_codigo else {}
    ctrl_info = knowledge_bridge.engine.get_control(inc.get("iso27701_control_id", "A.3.12")) or {}

    acciones = repository.listar_acciones_incidente(incident_id)
    historial = repository.listar_historial_incidente(incident_id)
    adjuntos = repository.listar_adjuntos_incidente(incident_id)
    mc = repository.obtener_medida_correctiva(incident_id)
    sec_logs = repository.listar_trazas_seguridad(incident_id)

    res = dict(inc)
    res.update({
        "control_iso": ctrl_info,
        "regla": regla_info,
        "documento_fuente_pdf": evidencia.get("documento_fuente_pdf"),
        "descripcion_documento": evidencia.get("descripcion_documento"),
        "esquema_fuente_sql": evidencia.get("esquema_fuente_sql"),
        "tabla_afectada": evidencia.get("tabla_afectada"),
        "columnas_afectadas": evidencia.get("columnas_afectadas", []),
        "evidencia_texto": evidencia.get("evidencia_texto"),
        "url_pdf_raw": evidencia.get("url_pdf_raw"),
        "url_sql_raw": evidencia.get("url_sql_raw"),
        "actions": acciones,
        "acciones": acciones,
        "historial": historial,
        "attachments": adjuntos,
        "corrective_action": mc,
        "security_logs": sec_logs,
        "incidente": inc,
    })
    return res


@router.patch("/api/incidents/{incident_id}")
def update_incident(incident_id: int, payload: Dict[str, Any], x_actor_id: Optional[int] = Header(default=None)):
    """Actualiza triaje B.3.12, recuperación de datos y registro documental de notificaciones."""
    updated = repository.actualizar_incidente(incident_id, payload, actor_id=_actor(x_actor_id))
    if not updated:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    return {"incident": updated, "mensaje": f"Expediente {updated['incident_code']} actualizado."}


@router.patch("/api/incidents/{incident_id}/assign")
def assign_incident(incident_id: int, payload: IncidentAssign, x_actor_id: Optional[int] = Header(default=None)):
    try:
        updated = repository.asignar_incidente(
            incident_id,
            assigned_to_id=payload.assigned_to_id,
            assigned_to_name=payload.assigned_to,
            actor_id=_actor(x_actor_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not updated:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    return {"incident": updated, "mensaje": f"Responsable asignado: {updated['assigned_to']}"}


@router.patch("/api/incidents/{incident_id}/status")
def change_incident_status(incident_id: int, payload: IncidentStatusChange, x_actor_id: Optional[int] = Header(default=None)):
    try:
        updated = repository.cambiar_estado_incidente(
            incident_id,
            new_status=payload.status,
            actor_id=_actor(x_actor_id),
            reason=payload.reason,
            force=payload.force,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"incident": updated, "status": updated["status"], "mensaje": f"Estado actualizado a {updated['status']}."}


@router.post("/api/incidents/{incident_id}/close")
def close_incident(incident_id: int, x_actor_id: Optional[int] = Header(default=None)):
    try:
        updated = repository.cambiar_estado_incidente(incident_id, "C", actor_id=_actor(x_actor_id))
        return {"success": True, "nuevo_estado": "C", "incident": updated, "mensaje": f"Incidente {incident_id} cerrado formalmente."}
    except KeyError:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/incidents/{incident_id}/actions")
def get_incident_actions(incident_id: int):
    acciones = repository.listar_acciones_incidente(incident_id)
    return {"actions": acciones, "acciones": acciones}


@router.post("/api/incidents/{incident_id}/actions", status_code=201)
def add_incident_action(incident_id: int, payload: ActionCreate, x_actor_id: Optional[int] = Header(default=None)):
    try:
        action = repository.agregar_accion_incidente(incident_id, payload.model_dump(), actor_id=_actor(x_actor_id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    return {"action": action, "mensaje": "Acción registrada en la bitácora A.3.12."}


@router.delete("/api/incidents/{incident_id}/actions/{action_id}")
def delete_incident_action(incident_id: int, action_id: int, x_actor_id: Optional[int] = Header(default=None)):
    ok = repository.eliminar_accion_incidente(incident_id, action_id, actor_id=_actor(x_actor_id))
    if not ok:
        raise HTTPException(status_code=404, detail="Acción no encontrada.")
    return {"deleted": True}


@router.get("/api/incidents/{incident_id}/history")
def get_incident_history(incident_id: int):
    historial = repository.listar_historial_incidente(incident_id)
    return {"history": historial, "historial": historial}


# =========================================================================
# MEDIDAS CORRECTIVAS D34 (CLÁUSULA 10.2)
# =========================================================================

@router.get("/api/corrective-actions")
def list_corrective_actions(status: Optional[str] = None):
    items = repository.listar_medidas_correctivas(status)
    return {"corrective_actions": items, "total": len(items)}


@router.post("/api/corrective-actions", status_code=201)
def create_corrective_action_standalone(payload: Dict[str, Any], x_actor_id: Optional[int] = Header(default=None)):
    """Crea una Medida Correctiva Cláusula 10.2 (independiente o asociada a un incidente)."""
    mc = repository.guardar_medida_correctiva_por_id(payload, mc_id=None, actor_id=_actor(x_actor_id))
    return {"corrective_action": mc, "mensaje": f"Medida correctiva {mc['mc_code']} registrada (Cláusula 10.2)."}


@router.post("/api/corrective-actions/import-docx")
async def import_corrective_action_docx_route(file: UploadFile = File(...)):
    """Lee un Formulario D34 (.docx) de 12 filas y devuelve los campos parseados y el incidente coincidente si existe."""
    fname = os.path.basename(file.filename or "")
    if not fname.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Debe subir un archivo Word D34 (.docx).")
    raw = await file.read()
    try:
        parsed = parse_d34_docx(raw)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error interpretando Formulario D34 .docx: {exc}") from exc

    matched_incident = None
    ref_code = parsed.get("incident_code_ref")
    if ref_code:
        for inc in repository.listar_incidentes_unsa():
            if (inc.get("incident_code") or "").upper() == ref_code:
                matched_incident = inc
                break
    return {
        "draft": parsed,
        "matched_incident": matched_incident,
        "filename": fname,
        "mensaje": f"Formulario D34 leído desde '{fname}'. Revise y guarde.",
    }


@router.put("/api/corrective-actions/{mc_id}")
def update_corrective_action_by_id(
    mc_id: int, payload: Dict[str, Any], x_actor_id: Optional[int] = Header(default=None)
):
    try:
        mc = repository.guardar_medida_correctiva_por_id(payload, mc_id=mc_id, actor_id=_actor(x_actor_id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Medida correctiva no encontrada.")
    return {"corrective_action": mc, "mensaje": f"Medida correctiva {mc['mc_code']} actualizada."}


@router.get("/api/corrective-actions/{mc_id}/export-docx")
def export_corrective_action_by_id_docx(mc_id: int):
    mc = repository.obtener_medida_correctiva_por_id(mc_id)
    if not mc:
        raise HTTPException(status_code=404, detail="Medida correctiva no encontrada.")
    inc = repository.obtener_incidente_unsa(mc["incident_id"]) if mc.get("incident_id") else None
    cfg = repository.obtener_configuracion()
    content = export_corrective_action_docx(mc, inc, cfg)
    filename = f"D34_{mc['mc_code'].replace(' ', '_')}.docx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/incidents/{incident_id}/corrective-action")
def get_incident_corrective_action(incident_id: int):
    inc = repository.obtener_incidente_unsa(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    mc = repository.obtener_medida_correctiva(incident_id)
    return {"corrective_action": mc, "incident": inc}


@router.put("/api/incidents/{incident_id}/corrective-action")
def save_incident_corrective_action(
    incident_id: int, payload: Dict[str, Any], x_actor_id: Optional[int] = Header(default=None)
):
    try:
        mc = repository.guardar_medida_correctiva(incident_id, payload, actor_id=_actor(x_actor_id))
    except KeyError:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    return {"corrective_action": mc, "mensaje": f"Medida correctiva {mc['mc_code']} guardada."}


@router.post("/api/incidents/{incident_id}/corrective-action/ai-draft")
def generate_ai_draft_corrective_action(incident_id: int):
    """Genera borrador técnico-normativo asistido por IA para los campos de la MC 10.2 (D34)."""
    inc = repository.obtener_incidente_unsa(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    ctrl_id = inc.get("iso27701_control_id") or "A.3.12"
    ctrl = knowledge_bridge.engine.get_control(ctrl_id) or {}
    cfg = repository.obtener_configuracion()

    fallback_draft = {
        "nonconformity_desc": f"Incidente {inc['incident_code']} ({ctrl_id} - {ctrl.get('title', 'PIMS')}): {inc.get('title')}. {inc.get('description', '')}".strip(),
        "root_cause": (
            f"Falla de control preventivo u organizativo vinculado a {ctrl_id} "
            f"en el activo '{inc.get('compromised_system') or 'sistema institucional'}', que permitió: {inc.get('consequences_summary') or inc.get('title')}."
        ),
        "action_to_implement": (
            ctrl.get("annex_b_guidance")
            or f"Implementar remediación técnica definitiva sobre {inc.get('compromised_system') or 'el activo'}, actualizar procedimientos y verificar eficacia conforme a ISO/IEC 27701:2025 Cláusula 10.2."
        ),
        "notify_who": f"{cfg['dpo_name']}, CISO OTI, Responsable de Activo ({inc.get('assigned_to') or 'OTI'})",
        "doc_changes_required": f"Actualizar directiva operativa del activo y matriz de riesgos vinculada al control {ctrl_id}.",
    }

    prompt = (
        "Redacta un borrador JSON estricto (claves: nonconformity_desc, root_cause, action_to_implement, "
        "notify_who, doc_changes_required) en español formal para un Formulario de Medida Correctiva ISO/IEC 27701:2025 Cláusula 10.2.\n"
        f"Incidente: {inc['incident_code']} - {inc['title']}\n"
        f"Descripción: {inc.get('description')}\n"
        f"Control ISO/IEC 27701:2025: {ctrl_id} ({ctrl.get('title', '')})\n"
        f"Guía Anexo B: {ctrl.get('annex_b_guidance', '')}\n"
        f"Activo: {inc.get('compromised_system')}\n"
        "Responde SOLO con JSON válido."
    )
    try:
        resp = default_luna_client.generate(
            messages=[
                {"role": "system", "content": "Eres auditor ISO/IEC 27701:2025. Responde únicamente un objeto JSON válido."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=700,
        )
        m = re.search(r"\{.*\}", resp.content or "", re.DOTALL)
        if resp.mode != "error" and m:
            parsed = json.loads(m.group(0))
            for k in fallback_draft:
                if isinstance(parsed.get(k), str) and parsed[k].strip():
                    fallback_draft[k] = parsed[k].strip()
    except Exception as exc:
        logger.debug("Omitiendo borrador LLM de MC 10.2 (%s); usando borrador determinista.", type(exc).__name__)

    return {"draft": fallback_draft}


@router.get("/api/incidents/{incident_id}/corrective-action/export-docx")
def export_corrective_action_word(incident_id: int):
    inc = repository.obtener_incidente_unsa(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    mc = repository.obtener_medida_correctiva(incident_id)
    if not mc:
        mc = repository.guardar_medida_correctiva(incident_id, {"nonconformity_desc": inc["title"]})
    cfg = repository.obtener_configuracion()
    content = export_corrective_action_docx(mc, inc, cfg)
    filename = f"D34_{mc['mc_code'].replace(' ', '_')}.docx"
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# =========================================================================
# EVIDENCIAS ADJUNTAS A.3.14
# =========================================================================

@router.get("/api/incidents/{incident_id}/attachments")
def list_incident_attachments(incident_id: int):
    return {"attachments": repository.listar_adjuntos_incidente(incident_id)}


@router.post("/api/incidents/{incident_id}/attachments", status_code=201)
async def upload_incident_attachment(
    incident_id: int, file: UploadFile = File(...), x_actor_id: Optional[int] = Header(default=None)
):
    if not repository.obtener_incidente_unsa(incident_id):
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    safe_name = os.path.basename(file.filename or "")
    if not safe_name:
        raise HTTPException(status_code=400, detail="Archivo inválido.")

    evid_dir = _get_writable_evidences_dir()
    os.makedirs(evid_dir, exist_ok=True)
    disk_name = f"inc_{incident_id}_{int(datetime.now().timestamp())}_{safe_name}"
    dest_path = os.path.join(evid_dir, disk_name)
    with open(dest_path, "wb") as out:
        shutil.copyfileobj(file.file, out)

    att = repository.agregar_adjunto_incidente(incident_id, f"uploads_evidencias/{disk_name}", safe_name, actor_id=_actor(x_actor_id))
    return {"attachment": att, "mensaje": f"Evidencia '{safe_name}' adjuntada."}


@router.get("/api/attachments/{att_id}/download")
def download_attachment(att_id: int):
    att = repository.obtener_adjunto(att_id)
    if not att:
        raise HTTPException(status_code=404, detail="Adjunto no encontrado.")
    rel = att["file"].lstrip("/\\").replace("\\", "/")
    if rel.startswith("uploads_evidencias/"):
        base_dir = os.path.abspath(_get_writable_evidences_dir())
        rel_sub = rel[len("uploads_evidencias/"):]
        full_path = os.path.abspath(os.path.join(base_dir, rel_sub))
    else:
        base_dir = os.path.abspath(MEDIA_DIR)
        full_path = os.path.abspath(os.path.join(base_dir, rel))
    if not full_path.startswith(base_dir) or not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Archivo físico de evidencia no disponible en disco.")
    return FileResponse(full_path, filename=att["file_name"])


# =========================================================================
# DIRECTORIOS, CONFIGURACIÓN Y REPORTE D35 (CLÁUSULA 9.3)
# =========================================================================

@router.get("/api/users")
def list_users():
    users = repository.listar_usuarios()
    return {"users": users, "total": len(users)}


@router.get("/api/config")
def get_config():
    return {"config": repository.obtener_configuracion()}


@router.put("/api/config")
def update_config(payload: Dict[str, Any]):
    return {"config": repository.actualizar_configuracion(payload)}


@router.get("/api/db/info")
def get_db_info():
    """Retorna estado de la base de datos única y del punto de control (checkpoint) de demostración."""
    return repository.obtener_info_bd()


@router.post("/api/db/checkpoint")
def create_db_checkpoint():
    """Guarda un snapshot instantáneo de la base de datos SQLite actual."""
    info = repository.crear_checkpoint_bd()
    return {"info": info, "mensaje": f"Punto de control guardado ({info['checkpoint_updated_at']})."}


@router.post("/api/db/restore-checkpoint")
def restore_db_checkpoint():
    """Restaura la base de datos al último punto de control guardado por el usuario."""
    try:
        info = repository.restaurar_checkpoint_bd()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"info": info, "mensaje": "Base de datos restaurada al punto de control guardado."}


@router.post("/api/db/reset-demo-seed")
def reset_db_demo_seed():
    """Restaura los 15 incidentes canónicos (2023-2026), 10 MC D34, 18 usuarios y 10 activos."""
    info = repository.restaurar_semilla_demo()
    return {"info": info, "mensaje": "Base de datos restablecida al estado inicial de demostración (15 incidentes 2023–2026)."}


@router.get("/api/security-logs")
def list_security_logs(incident_id: Optional[int] = None):
    logs = repository.listar_trazas_seguridad(incident_id=incident_id)
    return {"logs": logs, "total": len(logs)}


@router.get("/api/recipients")
def list_recipients(include_inactive: bool = False):
    dest = repository.listar_destinatarios_notificacion(include_inactive=include_inactive)
    return {"recipients": dest, "destinatarios": dest}


@router.post("/api/recipients", status_code=201)
def create_recipient(payload: RecipientCreate):
    rec = repository.crear_destinatario(payload.model_dump())
    return {"recipient": rec}


@router.patch("/api/recipients/{rec_id}")
def update_recipient(rec_id: int, payload: Dict[str, Any]):
    rec = repository.actualizar_destinatario(rec_id, payload)
    if not rec:
        raise HTTPException(status_code=404, detail="Destinatario no encontrado.")
    return {"recipient": rec}


@router.get("/api/unsa-assets")
def list_unsa_assets():
    activos = repository.listar_activos_unsa()
    return {"assets": activos, "activos": activos, "total": len(activos)}


@router.get("/api/reports/management-review-d35")
def get_management_review_d35(format: str = Query(default="json")):
    summary = repository.obtener_resumen_revision_direccion_d35()
    fmt = format.lower()
    if fmt == "markdown":
        md = export_management_review_d35_markdown(summary)
        return Response(
            content=md,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="D35_Revision_Direccion_PIMS.md"'},
        )
    if fmt == "docx":
        raw = export_management_review_d35_docx(summary)
        return Response(
            content=raw,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="D35_Revision_Direccion_PIMS.docx"'},
        )
    return {"summary": summary, "markdown": export_management_review_d35_markdown(summary)}


@router.get("/api/reports/corrective-procedure-docx")
def get_corrective_procedure_docx():
    """Exporta Procedimiento de Medidas Correctivas adaptado a UNSA ISO/IEC 27701:2025 con KPIs vivos."""
    summary = repository.obtener_resumen_revision_direccion_d35()
    raw = export_corrective_procedure_docx(summary, include_live_kpis=True)
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="Procedimiento_Medidas_Correctivas_PIMS_UNSA.docx"'},
    )


@router.get("/api/reports/audit-nonconformities-docx")
def get_audit_nonconformities_docx():
    """Exporta Apéndice 2 de Auditoría y No Conformidades con referencias cruzadas MC-UNSA."""
    summary = repository.obtener_resumen_revision_direccion_d35()
    raw = export_audit_nonconformities_docx(summary)
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="Informe_Auditoria_NoConformidades_PIMS_UNSA.docx"'},
    )


@router.get("/api/templates/pims")
def list_pims_templates():
    """Retorna catálogo oficial de plantillas .docx PIMS ISO/IEC 27701:2025."""
    return {"templates": PIMS_TEMPLATES_CATALOG, "total": len(PIMS_TEMPLATES_CATALOG)}


@router.get("/api/templates/pims/{template_id}/blank")
def download_blank_pims_template(template_id: str):
    """Descarga una plantilla oficial .docx en blanco lista para completar fuera del sistema."""
    entry = next((t for t in PIMS_TEMPLATES_CATALOG if t["id"] == template_id), None)
    if not entry:
        raise HTTPException(status_code=404, detail="Plantilla PIMS no encontrada.")
    cfg = repository.obtener_configuracion()
    raw = export_blank_template_docx(template_id, cfg)
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{entry["blank_filename"]}"'},
    )


@router.get("/api/incidents/{incident_id}/export-docx")
def export_incident_dossier_word(incident_id: int):
    """Exporta el Expediente completo de Incidente / Brecha PII (B.3.12 + A.3.14) en Word (.docx)."""
    inc = repository.obtener_incidente_unsa(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    ctrl_id = inc.get("iso27701_control_id") or "A.3.12"
    ctrl = knowledge_bridge.engine.get_control(ctrl_id) or {}
    acciones = repository.listar_acciones_incidente(incident_id)
    mc = repository.obtener_medida_correctiva(incident_id)
    adjuntos = repository.listar_adjuntos_incidente(incident_id)
    historial = repository.listar_historial_incidente(incident_id)
    cfg = repository.obtener_configuracion()
    raw = export_incident_dossier_docx(inc, ctrl, acciones, mc, adjuntos, historial, cfg)
    fname = f"Expediente_{inc['incident_code'].replace(' ', '_')}.docx"
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/api/incidents/{incident_id}/export-dictamen", response_class=PlainTextResponse)
def export_incident_dictamen(incident_id: int):
    """Genera informe pericial del incidente bajo ISO/IEC 27701:2025 (A.3.11, A.3.12 y Cl. 10.2)."""
    inc = repository.obtener_incidente_unsa(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    ctrl_id = inc.get("iso27701_control_id") or "A.3.12"
    ctrl = knowledge_bridge.engine.get_control(ctrl_id) or {}
    acciones = repository.listar_acciones_incidente(incident_id)
    mc = repository.obtener_medida_correctiva(incident_id)

    lineas = [
        "================================================================================",
        "EXPEDIENTE TÉCNICO DE INCIDENTE / BRECHA PII — ISO/IEC 27701:2025",
        "Universidad Nacional de San Agustín de Arequipa (UNSA) - PIMS / CSIRT",
        "Referencias: Cláusula 8.1, Controles A.3.11 / A.3.12 (B.3.12) y Cláusula 10.2",
        "================================================================================\n",
        f"1. Código: {inc['incident_code']} (ID: {inc['id']}) | Año: {inc['year']}",
        f"2. Título: {inc['title']}",
        f"3. Estado: {inc['status']} | Severidad: {inc.get('severity')} | Impacto: {inc.get('impact')}",
        f"4. Control ISO/IEC 27701:2025: {ctrl_id} — {ctrl.get('title', '')}",
        f"5. Clasificación B.3.12: {'Afecta PII (' + inc.get('incident_type', '') + ')' if inc.get('involves_personal_data') else 'Incidente técnico sin afectación PII (IT)'}",
        f"6. Responsable Asignado: {inc.get('assigned_to', 'Sin asignar')}",
        f"7. Sistema / Activo: {inc.get('compromised_system', 'N/A')}",
        f"8. Fecha Detección: {inc.get('detection_date', '')} {inc.get('detection_time', '')} | Cierre: {inc.get('resolved_date') or 'Pendiente'}",
        f"9. Consecuencias (B.3.12): {inc.get('consequences_summary') or 'En evaluación'}",
        f"10. Recuperación de Datos (B.3.12): {inc.get('data_recovered_status')} — {inc.get('data_recovered_detail') or ''}",
        f"11. Registro Documental Autoridad: {'Sí (' + (inc.get('anpd_official_ref') or 'Ref. pendiente') + ' - ' + (inc.get('anpd_notified_at') or '') + ')' if inc.get('anpd_notified') else 'No registrada'}",
        "\nACCIONES REGISTRADAS (A.3.12):",
    ]
    for idx, a in enumerate(acciones, 1):
        lineas.append(f"  {idx}. [{a['action_type']}] {a['action_date']} ({a['responsible']}): {a['description']}")
    if mc:
        lineas.extend([
            "\nMEDIDA CORRECTIVA CLÁUSULA 10.2 (D34):",
            f"  - Código: {mc['mc_code']} | Estado: {mc['status']} | Límite: {mc.get('due_date') or 'N/A'}",
            f"  - Causa raíz: {mc.get('root_cause') or 'Pendiente'}",
            f"  - Medida a implementar: {mc.get('action_to_implement') or 'Pendiente'}",
        ])
    return "\n".join(lineas)
