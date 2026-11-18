"""
Exportador oficial de Formularios de Medidas Correctivas (D34 - Cláusula 10.2)
e Informes de Revisión por la Dirección (D35 - Cláusula 9.3) bajo ISO/IEC 27701:2025.
"""

import io
import os
from datetime import datetime
from typing import Any, Dict

import docx

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BUNDLED_D34_TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates",
    "Apendice_Formulario_para_medidas_correctivas_ES.docx",
)
FALLBACK_D34_TEMPLATE = os.path.join(BASE_DIR, "temp", "Apendice_Formulario_para_medidas_correctivas_ES.docx")
D34_TEMPLATE_PATH = BUNDLED_D34_TEMPLATE if os.path.exists(BUNDLED_D34_TEMPLATE) else FALLBACK_D34_TEMPLATE


def _set_cell_value(cell, value: str, replace_placeholder: str = "", inline: bool = False) -> None:
    """Rellena una celda del formulario .docx preservando la etiqueta de la fila."""
    clean_val = (value or "—").strip()
    p0 = cell.paragraphs[0]
    if replace_placeholder and replace_placeholder in p0.text:
        new_text = p0.text.replace(replace_placeholder, f" {clean_val}")
        for r in p0.runs:
            r.text = ""
        if p0.runs:
            p0.runs[0].text = new_text
        else:
            p0.add_run(new_text)
        return

    if inline:
        run = p0.add_run(f" {clean_val}")
        run.bold = False
        return

    # Reutilizar párrafo 1 si existe (plantilla trae saltos vacíos) y limpiar vacíos sobrantes
    while len(cell.paragraphs) > 2:
        last_p = cell.paragraphs[-1]
        if not last_p.text.strip():
            last_p._element.getparent().remove(last_p._element)
        else:
            break

    target_p = cell.paragraphs[1] if len(cell.paragraphs) > 1 else cell.add_paragraph()
    target_p.text = clean_val


def export_corrective_action_docx(mc: Dict[str, Any], incident: Dict[str, Any], config: Dict[str, Any]) -> bytes:
    """
    Carga la plantilla institucional D34 y completa las 12 filas de la tabla principal
    con los datos de la medida correctiva (Cláusula 10.2 ISO/IEC 27701:2025).
    """
    if not os.path.exists(D34_TEMPLATE_PATH):
        raise FileNotFoundError(f"Plantilla D34 no encontrada en {D34_TEMPLATE_PATH}")

    doc = docx.Document(D34_TEMPLATE_PATH)
    if not doc.tables:
        raise ValueError("La plantilla D34 no contiene la tabla esperada.")

    t = doc.tables[0]
    mc_code = mc.get("mc_code") or f"MC-{incident.get('incident_code', 'UNSA')}"
    inc_code = incident.get("incident_code", "")
    iso_ctrl = incident.get("iso27701_control_id") or "A.3.12"
    org_name = config.get("org_name") or "Universidad Nacional de San Agustín de Arequipa"

    # Fila 0: Nro. de medida correctiva
    _set_cell_value(t.rows[0].cells[0], f"{mc_code}  |  Incidente: {inc_code} ({iso_ctrl})", replace_placeholder="____")

    # Fila 1: Descripción de la no-conformidad
    desc_text = mc.get("nonconformity_desc") or incident.get("description") or incident.get("title") or ""
    _set_cell_value(t.rows[1].cells[0], f"[{org_name} • Control {iso_ctrl}] {desc_text}")

    # Fila 2: Identificada en / Nombre / Firma
    identified_in = mc.get("identified_on") or incident.get("detection_date") or ""
    if incident.get("compromised_system"):
        identified_in = f"{identified_in} — {incident['compromised_system']}"
    _set_cell_value(t.rows[2].cells[0], identified_in)
    _set_cell_value(t.rows[2].cells[1], mc.get("identified_by_name") or incident.get("reported_by") or "")
    _set_cell_value(t.rows[2].cells[2], mc.get("identified_signature") or "Por firmar")

    # Fila 3: Causa raíz
    _set_cell_value(t.rows[3].cells[0], mc.get("root_cause") or "Pendiente de análisis de causa raíz.")

    # Fila 4: Medida correctiva similar previa
    _set_cell_value(t.rows[4].cells[0], mc.get("similar_mc_ref") or "Ninguna registrada previamente", inline=True)

    # Fila 5: ¿Es necesario tomar medidas correctivas? SÍ / NO
    req = bool(mc.get("action_required", 1))
    marcador = "[SÍ] - NO (Marcado: SÍ)" if req else "SÍ - [NO] (Marcado: NO)"
    p5 = t.rows[5].cells[0].paragraphs[0]
    p5.text = f"¿Es necesario tomar medidas correctivas? {marcador}"

    # Fila 6: Medida correctiva a implementar
    _set_cell_value(t.rows[6].cells[0], mc.get("action_to_implement") or "")

    # Fila 7: ¿Quién debe estar informado?
    _set_cell_value(t.rows[7].cells[0], mc.get("notify_who") or config.get("dpo_name") or "DPO / CISO / Propietario del Activo")

    # Fila 8: Aprobado por / Fecha límite / Responsable
    _set_cell_value(t.rows[8].cells[0], mc.get("approved_by_name") or config.get("dpo_name") or "")
    _set_cell_value(t.rows[8].cells[1], mc.get("due_date") or "Sin definir")
    _set_cell_value(t.rows[8].cells[2], mc.get("responsible_name") or incident.get("assigned_to") or "")

    # Fila 9: Implementada el / Firma
    _set_cell_value(t.rows[9].cells[0], mc.get("implemented_on") or "Pendiente", inline=True)
    _set_cell_value(t.rows[9].cells[2], mc.get("implemented_signature") or "Pendiente")

    # Fila 10: Efectividad revisada el / Firma
    _set_cell_value(t.rows[10].cells[0], mc.get("effectiveness_reviewed_on") or "Pendiente", inline=True)
    _set_cell_value(t.rows[10].cells[2], mc.get("effectiveness_signature") or "Pendiente")

    # Fila 11: Cambios al documento / Firma
    _set_cell_value(t.rows[11].cells[0], mc.get("doc_changes_required") or "Sin cambios requeridos por el momento.")
    _set_cell_value(t.rows[11].cells[2], mc.get("doc_changes_signature") or "Pendiente")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def export_management_review_d35_markdown(summary: Dict[str, Any]) -> str:
    """Genera informe ejecutivo de Revisión por la Dirección (Cláusula 9.3 / D35)."""
    cfg = summary.get("config", {})
    by_year = summary.get("by_year", [])
    top_ctrls = summary.get("top_controls", [])
    open_crit = summary.get("open_critical_by_responsible", [])
    mc_stats = summary.get("corrective_actions", {})

    lines = [
        "# INFORME PARA REVISIÓN POR LA DIRECCIÓN — PIMS ISO/IEC 27701:2025 (D35 / Cláusula 9.3)",
        f"**Organización:** {cfg.get('org_name', 'UNSA')} (RUC: {cfg.get('org_ruc', '20140798781')})",
        f"**Oficial de Protección de Datos (DPO):** {cfg.get('dpo_name', 'DPO UNSA')}",
        f"**Fecha de Emisión:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 1. Resumen Ejecutivo (Tendencia de Incidentes, Brechas PII y No Conformidades)",
        f"- **Total registros históricos:** {summary.get('total_incidents', 0)}",
        f"- **Abiertos (En Investigación / Mitigación):** {summary.get('open_incidents', 0)} (Críticos abiertos: {summary.get('open_critical', 0)})",
        f"- **Cerrados:** {summary.get('closed_incidents', 0)}",
        f"- **Brechas / No Conformidades PII:** {summary.get('pii_incidents', 0)} | **Incidentes Técnicos sin PII (B.3.12 Note 1):** {summary.get('tech_non_pii', 0)}",
        f"- **Medidas Correctivas 10.2 (D34):** Total={mc_stats.get('total', 0)} | Verificadas={mc_stats.get('verificadas', 0)} | Pendientes={mc_stats.get('pendientes', 0)}",
        "",
        "## 2. Distribución Anual (2023–2026)",
        "| Año | Total | Abiertos | Cerrados | Críticos | Brechas PII | Técnicos sin PII |",
        "|---|---|---|---|---|---|---|",
    ]
    for y in by_year:
        lines.append(
            f"| {y['year']} | {y['total']} | {y['open']} | {y['closed']} | {y['critical']} | {y['pii']} | {y['tech']} |"
        )

    lines.extend([
        "",
        "## 3. Incidentes Críticos Sin Cerrar por Responsable",
        "| Responsable | Críticos Abiertos | Códigos |",
        "|---|---|---|",
    ])
    for r in open_crit:
        lines.append(f"| {r['responsible']} | {r['count']} | {', '.join(r['codes'])} |")

    lines.extend([
        "",
        "## 4. Controles ISO/IEC 27701:2025 Más Afectados",
        "| Control | Cantidad de Incidentes |",
        "|---|---|",
    ])
    for c in top_ctrls:
        lines.append(f"| {c['control_id']} | {c['count']} |")

    return "\n".join(lines)


def export_management_review_d35_docx(summary: Dict[str, Any]) -> bytes:
    """Exporta el resumen ejecutivo D35 en formato Word (.docx)."""
    md = export_management_review_d35_markdown(summary)
    doc = docx.Document()
    for line in md.splitlines():
        if line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.strip():
            doc.add_paragraph(line)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
