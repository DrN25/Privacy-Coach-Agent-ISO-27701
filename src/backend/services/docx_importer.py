"""
Importadores deterministas y asistidos por IA para archivos Word (.docx):
1. D34 (Formulario de Medidas Correctivas - Cláusula 10.2)
2. Reporte / Expediente de Incidente o Brecha PII (B.3.12)
3. Apéndice 2 (Informe de Auditoría Interna y No Conformidades)
"""

import io
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import docx

from ..infrastructure.llm_client import default_luna_client
from ..knowledge_bridge import knowledge_bridge

logger = logging.getLogger(__name__)


def _unique_row_cells(row) -> List[str]:
    """Retorna textos de celdas únicas de una fila evitando duplicados por celdas combinadas."""
    texts: List[str] = []
    seen_tcs = set()
    for cell in row.cells:
        if id(cell._tc) in seen_tcs:
            continue
        seen_tcs.add(id(cell._tc))
        texts.append(cell.text.strip())
    return texts


def _strip_label(raw: str, labels: Tuple[str, ...]) -> str:
    """Extrae el valor de una celda quitando su etiqueta descriptiva inicial."""
    lines = [ln.strip() for ln in (raw or "").splitlines() if ln.strip()]
    cleaned_lines: List[str] = []
    for ln in lines:
        low = ln.lower()
        matched_prefix = next((lbl for lbl in labels if low.startswith(lbl.lower())), None)
        if matched_prefix:
            rest = ln[len(matched_prefix):].lstrip(" :.-—|")
            if rest:
                cleaned_lines.append(rest)
        else:
            cleaned_lines.append(ln)
    val = " ".join(cleaned_lines).strip()
    return "" if val in ("—", "-", "Pendiente", "Por firmar") else val


def extract_docx_text(raw_bytes: bytes) -> str:
    """Extrae texto plano ordenado de párrafos y tablas únicas de un .docx."""
    doc = docx.Document(io.BytesIO(raw_bytes))
    chunks: List[str] = []
    for p in doc.paragraphs:
        if p.text.strip():
            chunks.append(p.text.strip())
    for tbl in doc.tables:
        for row in tbl.rows:
            vals = [v.replace("\n", " ") for v in _unique_row_cells(row) if v]
            if vals:
                chunks.append(" | ".join(vals))
    return "\n".join(chunks)


def extract_audit_nonconformities_from_docx(raw_bytes_or_path) -> List[Dict[str, Any]]:
    """Detecta tablas de Apéndice 2 (No-conformidades identificadas) y extrae cada hallazgo."""
    if isinstance(raw_bytes_or_path, (bytes, bytearray)):
        doc = docx.Document(io.BytesIO(raw_bytes_or_path))
    else:
        doc = docx.Document(raw_bytes_or_path)

    findings: List[Dict[str, Any]] = []
    for tbl in doc.tables:
        header_idx: Optional[int] = None
        for r_i, row in enumerate(tbl.rows):
            joined = " ".join(_unique_row_cells(row)).lower()
            if "no-conformidades identificadas" in joined or "no conformidades identificadas" in joined:
                header_idx = r_i
                break
        if header_idx is None:
            continue

        for row in tbl.rows[header_idx + 1:]:
            cells = _unique_row_cells(row)
            nc_text = (cells[0] if len(cells) > 0 else "").strip()
            mc_ref = (cells[1] if len(cells) > 1 else "").strip()
            if not nc_text or nc_text in ("—", "-"):
                continue

            ctrl_match = re.search(r"\b([AB]\.[123](?:\.[0-9]+){1,2})\b", nc_text, re.IGNORECASE)
            ctrl_id = ctrl_match.group(1).upper() if ctrl_match else "A.3.15"
            if ctrl_id not in knowledge_bridge.engine.controls_map:
                ctrl_id = "A.3.15"

            findings.append({
                "nc_text": nc_text,
                "mc_ref": mc_ref,
                "control_iso27701": ctrl_id,
            })
    return findings


def _infer_date(text: str) -> str:
    m = re.search(r"\b(20[2-3][0-9]-[01][0-9]-[0-3][0-9])\b", text or "")
    return m.group(1) if m else ""


def parse_d34_docx(raw_bytes: bytes) -> Dict[str, Any]:
    """Parsea las 12 filas de un Formulario D34 .docx hacia campos de a6_corrective_action."""
    doc = docx.Document(io.BytesIO(raw_bytes))
    if not doc.tables or len(doc.tables[0].rows) < 12:
        raise ValueError("El archivo .docx no coincide con la estructura de 12 filas del Formulario D34.")

    t = doc.tables[0]
    rows_cells = [_unique_row_cells(r) for r in t.rows[:12]]

    r0 = rows_cells[0][0] if rows_cells[0] else ""
    mc_match = re.search(r"\b(MC-[A-Z0-9-]+)\b", r0, re.IGNORECASE)
    inc_match = re.search(r"\b(INC-[A-Z0-9-]+)\b", r0, re.IGNORECASE)
    ctrl_match = re.search(r"\b([AB]\.[123](?:\.[0-9]+){1,2})\b", f"{r0} {' '.join(rows_cells[1])}", re.IGNORECASE)

    r1 = _strip_label(rows_cells[1][0] if rows_cells[1] else "", ("Descripción de la no-conformidad",))
    r1 = re.sub(r"^\[[^\]]*\]\s*", "", r1).strip()

    r2_c0 = _strip_label(rows_cells[2][0] if len(rows_cells[2]) > 0 else "", ("No-conformidad identificada en",))
    r2_c1 = _strip_label(rows_cells[2][1] if len(rows_cells[2]) > 1 else "", ("Nombre de la persona que identificó la no-conformidad",))
    r2_c2 = _strip_label(rows_cells[2][2] if len(rows_cells[2]) > 2 else "", ("Firma",))

    root_cause = _strip_label(rows_cells[3][0] if rows_cells[3] else "", ("Causa de la no-conformidad",))
    similar_ref = _strip_label(
        rows_cells[4][0] if rows_cells[4] else "",
        ("Si ya existe una no conformidad similar, indique aquí su Medida correctiva Nro.",),
    )

    r5_raw = rows_cells[5][0] if rows_cells[5] else ""
    r5_clean = _strip_label(r5_raw, ("¿Es necesario tomar medidas correctivas?",)).upper()
    action_required = not (
        "[NO]" in r5_raw.upper()
        or "MARCADO: NO" in r5_raw.upper()
        or r5_clean in ("NO", "NO.", "SÍ - NO: NO")
    )

    action_impl = _strip_label(rows_cells[6][0] if rows_cells[6] else "", ("Medida correctiva a implementar",))
    notify_who = _strip_label(rows_cells[7][0] if rows_cells[7] else "", ("¿Quién debe estar informado sobre la medida implementada?",))

    approved_by = _strip_label(rows_cells[8][0] if len(rows_cells[8]) > 0 else "", ("Aprobado por",))
    due_raw = _strip_label(rows_cells[8][1] if len(rows_cells[8]) > 1 else "", ("Fecha límite para la implementación",))
    due_date = _infer_date(due_raw) or ("" if due_raw == "Sin definir" else due_raw)
    responsible_name = _strip_label(rows_cells[8][2] if len(rows_cells[8]) > 2 else "", ("Persona responsable de la implementación",))

    impl_raw = _strip_label(rows_cells[9][0] if len(rows_cells[9]) > 0 else "", ("Medida correctiva implementada el",))
    implemented_on = _infer_date(impl_raw)
    implemented_sig = _strip_label(rows_cells[9][-1] if len(rows_cells[9]) > 1 else "", ("Firma",))

    eff_raw = _strip_label(rows_cells[10][0] if len(rows_cells[10]) > 0 else "", ("Efectividad de la medida implementada revisada el",))
    effectiveness_on = _infer_date(eff_raw)
    effectiveness_sig = _strip_label(rows_cells[10][-1] if len(rows_cells[10]) > 1 else "", ("Firma",))

    doc_changes = _strip_label(
        rows_cells[11][0] if len(rows_cells[11]) > 0 else "",
        ("Si es necesario realizar cambios al documento, especifíquelos aquí",),
    )
    doc_sig = _strip_label(rows_cells[11][-1] if len(rows_cells[11]) > 1 else "", ("Firma",))

    status = "VERIFICADA" if effectiveness_on else ("IMPLEMENTADA" if implemented_on else "ABIERTA")
    ctrl_id = ctrl_match.group(1).upper() if ctrl_match and ctrl_match.group(1).upper() in knowledge_bridge.engine.controls_map else "A.3.12"

    return {
        "mc_code": mc_match.group(1).upper() if mc_match else "",
        "incident_code_ref": inc_match.group(1).upper() if inc_match else "",
        "iso27701_control_id": ctrl_id,
        "nonconformity_desc": r1,
        "identified_on": _infer_date(r2_c0) or datetime.now().strftime("%Y-%m-%d"),
        "identified_by_name": r2_c1,
        "identified_signature": r2_c2,
        "root_cause": root_cause,
        "similar_mc_ref": "" if similar_ref.startswith("Ninguna registrada") else similar_ref,
        "action_required": action_required,
        "action_to_implement": action_impl,
        "notify_who": notify_who,
        "approved_by_name": approved_by,
        "due_date": due_date,
        "responsible_name": responsible_name,
        "implemented_on": implemented_on,
        "implemented_signature": implemented_sig,
        "effectiveness_reviewed_on": effectiveness_on,
        "effectiveness_signature": effectiveness_sig,
        "doc_changes_required": doc_changes,
        "doc_changes_signature": doc_sig,
        "status": status,
        "source_type": "IMPORTACION_D34",
    }


def _match_kv_draft(kv_map: Dict[str, str], filename: str) -> Dict[str, Any]:
    today = datetime.now().strftime("%Y-%m-%d")

    def _get(*keys: str) -> str:
        for k_sub in keys:
            for k, v in kv_map.items():
                if k_sub in k:
                    return v.strip()
        return ""

    pii_raw = _get("involucra datos", "datos personales", "pii").upper()
    involves_pii = not (pii_raw.startswith("NO") or pii_raw == "0")

    type_raw = _get("clasificación", "clasificacion", "tipo").upper()
    inc_type = next((code for code in ("BF", "BI", "BD", "PI", "IT") if code in type_raw), "BF" if involves_pii else "IT")
    if inc_type == "IT":
        involves_pii = False

    sev_raw = _get("severidad", "criticidad").upper()
    severity = "A"
    if sev_raw.startswith("C") or "CRÍTIC" in sev_raw or "CRITIC" in sev_raw:
        severity = "C"
    elif sev_raw.startswith("A") or "ALT" in sev_raw:
        severity = "A"
    elif sev_raw.startswith("M") or "MEDI" in sev_raw:
        severity = "M"
    elif sev_raw.startswith("B") or "BAJ" in sev_raw:
        severity = "B"

    ctrl_raw = _get("control iso", "27701")
    ctrl_match = re.search(r"\b([AB]\.[123](?:\.[0-9]+){1,2})\b", ctrl_raw, re.IGNORECASE)
    ctrl_id = ctrl_match.group(1).upper() if ctrl_match and ctrl_match.group(1).upper() in knowledge_bridge.engine.controls_map else "A.3.12"

    subj_digits = "".join(ch for ch in _get("titulares", "afectados") if ch.isdigit())
    num_subj = int(subj_digits) if subj_digits else 0

    return {
        "title": _get("título", "titulo") or f"Incidente importado desde {filename}",
        "description": _get("descripción", "descripcion", "hechos"),
        "incident_date": _infer_date(_get("fecha del incidente")) or today,
        "detection_date": _infer_date(_get("fecha de detección", "fecha de deteccion")) or today,
        "compromised_system": _get("sistema", "activo"),
        "affected_url": _get("url", "endpoint"),
        "involves_personal_data": involves_pii,
        "incident_type": inc_type,
        "severity": severity,
        "impact": severity,
        "iso27701_control_id": ctrl_id,
        "num_affected_subjects": num_subj,
        "consequences_summary": _get("consecuencias"),
        "initial_action_type": "C" if inc_type != "PI" else "M",
        "initial_action_description": _get("acción inicial", "accion inicial", "contención", "contencion"),
        "reported_by": f"Importado Word ({filename})",
        "create_mc_draft": True,
    }


def parse_incident_report_docx(raw_bytes: bytes, filename: str) -> Tuple[Dict[str, Any], bool]:
    """Lee un reporte .docx de incidente/brecha; usa tabla Campo|Valor y enriquece con IA si falta detalle."""
    doc = docx.Document(io.BytesIO(raw_bytes))
    kv_map: Dict[str, str] = {}
    for tbl in doc.tables:
        for row in tbl.rows:
            cells = _unique_row_cells(row)
            if len(cells) >= 2 and cells[0]:
                kv_map[cells[0].lower()] = cells[1]

    has_structured_title = any("título" in k or "titulo" in k for k in kv_map)
    draft = _match_kv_draft(kv_map, filename) if has_structured_title else _match_kv_draft({}, filename)
    raw_text = extract_docx_text(raw_bytes)

    if has_structured_title and draft.get("description"):
        return draft, False

    ai_enriched = False
    prompt = (
        "Extrae un borrador JSON estricto (claves exactas: title, description, involves_personal_data, "
        "incident_type [BF|BI|BD|PI|IT], severity [C|A|M|B], iso27701_control_id, num_affected_subjects, "
        "compromised_system, consequences_summary, initial_action_description) de este documento Word.\n"
        f"Archivo: {filename}\nContenido:\n{raw_text[:4500]}\n"
        "Responde SOLO JSON válido sin markdown."
    )
    try:
        resp = default_luna_client.generate(
            messages=[
                {"role": "system", "content": "Eres auditor PIMS ISO/IEC 27701:2025. Devuelve únicamente JSON válido."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=550,
        )
        m = re.search(r"\{.*\}", resp.content or "", re.DOTALL)
        if resp.mode != "error" and m:
            parsed = json.loads(m.group(0))
            for k in ("title", "description", "compromised_system", "consequences_summary", "initial_action_description"):
                val = parsed.get(k)
                if isinstance(val, str) and val.strip():
                    draft[k] = val.strip()
            if isinstance(parsed.get("involves_personal_data"), bool):
                draft["involves_personal_data"] = parsed["involves_personal_data"]
            if parsed.get("incident_type") in ("BF", "BI", "BD", "PI", "IT"):
                draft["incident_type"] = parsed["incident_type"]
            if parsed.get("severity") in ("C", "A", "M", "B"):
                draft["severity"] = parsed["severity"]
                draft["impact"] = parsed["severity"]
            ctrl = str(parsed.get("iso27701_control_id") or "").upper()
            if ctrl in knowledge_bridge.engine.controls_map:
                draft["iso27701_control_id"] = ctrl
            if isinstance(parsed.get("num_affected_subjects"), int):
                draft["num_affected_subjects"] = max(0, parsed["num_affected_subjects"])
            ai_enriched = True
    except Exception as exc:
        logger.warning("Fallback determinista al importar incidente .docx: %s", type(exc).__name__)

    if not draft.get("description") and raw_text:
        draft["description"] = raw_text[:800]
    return draft, ai_enriched
