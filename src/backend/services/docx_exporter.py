"""
Exportador oficial de documentos PIMS en formato Word (.docx) y Markdown (.md):
1. D34: Formulario de Medidas Correctivas (Cláusula 10.2)
2. D35: Minutas de Revisión por la Dirección (Cláusula 9.3)
3. Procedimiento para Medidas Correctivas (Cláusula 10.2 + KPIs vivos)
4. Informe de Auditoría / No Conformidades (Cláusula 9.2 -> 10.2)
5. Expediente de Incidente / Brecha PII (A.3.11 / A.3.12 / B.3.12 / A.3.14)
6. Plantillas en blanco listas para descarga e importación.
"""

import io
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import docx

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BUNDLED_TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
FALLBACK_TEMPLATES_DIR = os.path.join(BASE_DIR, "temp")


def _resolve_template(filename: str) -> str:
    """Resuelve la ruta de una plantilla .docx empaquetada en src/backend/templates/ o temp/."""
    bundled = os.path.join(BUNDLED_TEMPLATES_DIR, filename)
    if os.path.exists(bundled):
        return bundled
    return os.path.join(FALLBACK_TEMPLATES_DIR, filename)


def _set_cell_value(cell, value: str, replace_placeholder: str = "", inline: bool = False) -> None:
    """Rellena una celda de formulario .docx preservando su etiqueta."""
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

    while len(cell.paragraphs) > 2:
        last_p = cell.paragraphs[-1]
        if not last_p.text.strip():
            last_p._element.getparent().remove(last_p._element)
        else:
            break

    target_p = cell.paragraphs[1] if len(cell.paragraphs) > 1 else cell.add_paragraph()
    target_p.text = clean_val


def _replace_paragraph_text(paragraph, new_text: str) -> None:
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for r in paragraph.runs[1:]:
            r.text = ""
    else:
        paragraph.text = new_text


def _adapt_sgsi_to_pims(text: str, org_name: str, cargo_default: str = "Oficial de Datos Personales (DPO)") -> str:
    """Adapta textos de plantillas ISO 27001/22301 hacia PIMS ISO/IEC 27701:2025."""
    out = (
        text.replace("Sistema de Gestión de Seguridad de la Información (SGSI) Sistema de Gestión de Continuidad del Negocio (SGCN)]", "Sistema de Gestión de Información de Privacidad (PIMS - ISO/IEC 27701:2025)")
        .replace("Sistema de Gestión de Seguridad de la Información (SGSI)", "Sistema de Gestión de Información de Privacidad (PIMS)")
        .replace("(SGSI)", "(PIMS - ISO/IEC 27701:2025)")
        .replace("SGSI", "PIMS (ISO/IEC 27701:2025)")
        .replace("[nombre de la organización]", org_name)
        .replace("[nombre del organismo]", org_name)
        .replace("[cargo]", cargo_default)
    )
    return out


# ==============================================================================
# 1. FORMULARIO D34 — MEDIDA CORRECTIVA (CLÁUSULA 10.2)
# ==============================================================================

def export_corrective_action_docx(
    mc: Dict[str, Any],
    incident: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Completa las 12 filas de D34 con los datos de una MC (vinculada a incidente o independiente)."""
    tpl_path = _resolve_template("Apendice_Formulario_para_medidas_correctivas_ES.docx")
    if not os.path.exists(tpl_path):
        raise FileNotFoundError(f"Plantilla D34 no encontrada en {tpl_path}")

    doc = docx.Document(tpl_path)
    if not doc.tables:
        raise ValueError("La plantilla D34 no contiene la tabla esperada.")

    cfg = config or {}
    inc = incident or {}
    t = doc.tables[0]

    mc_code = mc.get("mc_code") or f"MC-{inc.get('incident_code', 'UNSA')}"
    inc_code = inc.get("incident_code") or mc.get("incident_code") or ""
    iso_ctrl = inc.get("iso27701_control_id") or mc.get("iso27701_control_id") or "A.3.12"
    org_name = cfg.get("org_name") or "Universidad Nacional de San Agustín de Arequipa"

    # Fila 0: Nro. de medida correctiva
    origen_txt = f"Incidente: {inc_code}" if inc_code else f"Origen: {mc.get('source_type') or 'INDEPENDIENTE'}"
    _set_cell_value(t.rows[0].cells[0], f"{mc_code}  |  {origen_txt} ({iso_ctrl})", replace_placeholder="____")

    # Fila 1: Descripción de la no-conformidad
    desc_text = mc.get("nonconformity_desc") or inc.get("description") or inc.get("title") or ""
    _set_cell_value(t.rows[1].cells[0], f"[{org_name} • Control {iso_ctrl}] {desc_text}")

    # Fila 2: Identificada en / Nombre / Firma
    identified_in = mc.get("identified_on") or inc.get("detection_date") or datetime.now().strftime("%Y-%m-%d")
    if inc.get("compromised_system"):
        identified_in = f"{identified_in} — {inc['compromised_system']}"
    _set_cell_value(t.rows[2].cells[0], identified_in)
    _set_cell_value(t.rows[2].cells[1], mc.get("identified_by_name") or inc.get("reported_by") or "")
    _set_cell_value(t.rows[2].cells[2], mc.get("identified_signature") or "Por firmar")

    # Fila 3: Causa raíz
    _set_cell_value(t.rows[3].cells[0], mc.get("root_cause") or "Pendiente de análisis de causa raíz.")

    # Fila 4: Medida correctiva similar previa
    _set_cell_value(t.rows[4].cells[0], mc.get("similar_mc_ref") or "Ninguna registrada previamente", inline=True)

    # Fila 5: ¿Es necesario tomar medidas correctivas? SÍ / NO
    req = bool(mc.get("action_required", 1))
    marcador = "[SÍ] - NO (Marcado: SÍ)" if req else "SÍ - [NO] (Marcado: NO)"
    t.rows[5].cells[0].paragraphs[0].text = f"¿Es necesario tomar medidas correctivas? {marcador}"

    # Fila 6: Medida correctiva a implementar
    _set_cell_value(t.rows[6].cells[0], mc.get("action_to_implement") or "")

    # Fila 7: ¿Quién debe estar informado?
    _set_cell_value(t.rows[7].cells[0], mc.get("notify_who") or cfg.get("dpo_name") or "DPO / CISO / Propietario del Activo")

    # Fila 8: Aprobado por / Fecha límite / Responsable
    _set_cell_value(t.rows[8].cells[0], mc.get("approved_by_name") or cfg.get("dpo_name") or "")
    _set_cell_value(t.rows[8].cells[1], mc.get("due_date") or "Sin definir")
    _set_cell_value(t.rows[8].cells[2], mc.get("responsible_name") or inc.get("assigned_to") or "")

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


# ==============================================================================
# 2. REPORTE D35 — MINUTAS DE REVISIÓN POR LA DIRECCIÓN (CLÁUSULA 9.3)
# ==============================================================================

def export_management_review_d35_markdown(summary: Dict[str, Any]) -> str:
    """Genera informe ejecutivo en Markdown de Revisión por la Dirección (Cláusula 9.3 / D35)."""
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
    """Exporta las Minutas D35 usando la plantilla oficial adaptada a PIMS ISO/IEC 27701:2025 (Cl. 9.3)."""
    tpl_path = _resolve_template("Minutas_de_Revision_por_parte_de_la_direccion_ES.docx")
    cfg = summary.get("config", {})
    org_name = cfg.get("org_name") or "Universidad Nacional de San Agustín de Arequipa"
    dpo_name = cfg.get("dpo_name") or "Abog. Carlos Mendoza Valdivia (DPO UNSA)"
    rep_name = cfg.get("legal_rep_name") or "Dr. Hugo Rojas Flores"
    mc_stats = summary.get("corrective_actions", {})
    proc_kpis = summary.get("procedure_kpis", {})
    today = datetime.now().strftime("%Y-%m-%d")

    if not os.path.exists(tpl_path):
        md = export_management_review_d35_markdown(summary)
        doc = docx.Document()
        for line in md.splitlines():
            if line.strip():
                doc.add_paragraph(line)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    doc = docx.Document(tpl_path)
    disruptive = summary.get("disruptive_incidents", [])
    disruptive_txt = "; ".join(f"{d['incident_code']} ({d['severity']}, {d['status']})" for d in disruptive[:4]) or "Sin incidentes disruptivos abiertos"
    top_ctrls = ", ".join(f"{c['control_id']} ({c['count']})" for c in summary.get("top_controls", [])[:5]) or "A.3.12"

    replacements = {
        0: "MINUTAS DE REVISIÓN POR LA DIRECCIÓN — PIMS ISO/IEC 27701:2025 (Cláusula 9.3 / D35)",
        1: f"La reunión de Alta Dirección de {org_name} (RUC: {cfg.get('org_ruc', '20140798781')}) fue realizada el {today} con la asistencia de:",
        2: f"{rep_name} (Rector / Representante Legal), {dpo_name} (DPO UNSA), Oficial de Seguridad (CISO / OTI) y Jefe de CSIRT UNSA.",
        3: "El objetivo de la reunión fue revisar la conveniencia, adecuación y eficacia del Sistema de Gestión de Información de Privacidad (PIMS - ISO/IEC 27701:2025).",
        5: f"Informe Consolidado de Incidentes y Brechas PII (2023–2026) — emitido el {today} sobre base unificada PIMS.",
        6: "Retroalimentación de titulares de datos personales, solicitudes ARCO y quejas documentadas en TRAMITED.",
        7: f"Adopción de ISO/IEC 27701:2025 (78 controles Anexo A), inspección AST con SQLGlot y Subagente IA documental.",
        8: f"Controles con mayor exposición detectada: {top_ctrls}. Total brechas PII: {summary.get('pii_incidents', 0)} | Técnicos IT: {summary.get('tech_non_pii', 0)}.",
        9: (
            f"Estado de No Conformidades y Medidas Correctivas (Cl. 10.2 / D34): Total={mc_stats.get('total', 0)}, "
            f"Verificadas={mc_stats.get('verificadas', 0)}, Implementadas={mc_stats.get('implementadas', 0)}, "
            f"Pendientes={mc_stats.get('pendientes', 0)} (Incidentes sin D34: {proc_kpis.get('incidentes_sin_formulario_d34', 0)})."
        ),
        10: f"Tasa de cierre de incidentes: {summary.get('closed_incidents', 0)} cerrados de {summary.get('total_incidents', 0)} totales ({summary.get('open_critical', 0)} críticos abiertos).",
        11: f"Seguimiento de acciones abiertas de revisión anterior: {summary.get('open_incidents', 0)} expedientes activos en investigación o mitigación.",
        12: "Cambios normativos y organizacionales: alineación completa a ISO/IEC 27701:2025 (Edición 2, Oct-2025) y directivas CSIRT/DPO UNSA.",
        13: "Recomendaciones: completar las Medidas Correctivas 10.2 pendientes y reforzar cifrado pgcrypto, Argon2id y MFA institucional.",
        14: f"Resultados de monitoreo de registros y trazas DSPM/CSIRT ejecutados al {today}.",
        15: f"Revisión tras incidentes críticos/altos recientes: {disruptive_txt}.",
        17: "Alcance PIMS confirmado sobre los 10 activos institucionales UNSA (SISUNSA, Hospital Zamácola, SISADMISION, TRAMITED, Tesorería, etc.).",
        18: "Priorizar el cierre de expedientes críticos abiertos y verificar la eficacia de las medidas D34 vencidas.",
        19: "Actualizar inventario RAT, matriz de riesgos B.3.12 y planes de contingencia tras el cierre de cada medida correctiva.",
        20: "Actualizar políticas de retención de admisión, gratuidad ARCO en TUPA y contratos DPA para flujos cloud.",
        21: "Asignación de horas de ingeniería OTI, CSIRT UNSA y validación jurídica DPO para ejecución de medidas 10.2.",
        22: "Presupuesto operativo OTI cubierto para cifrado, tokenización de pasarela y respaldo inmutable 3-2-1.",
        23: "Incorporar revisión trimestral de KPIs de eficacia del Procedimiento de Medidas Correctivas y bitácora A.3.14.",
        24: f"Comunicar acuerdos a: Rectorado UNSA, {dpo_name}, CISO OTI, Secretaría General y Jefaturas de Unidad Orgánica.",
        29: "Oficial de Protección de Datos Personales (DPO) / Representante Alta Dirección",
        30: f"{dpo_name} / {rep_name}",
    }

    for idx, p in enumerate(doc.paragraphs):
        if idx in replacements:
            _replace_paragraph_text(p, replacements[idx])
        elif "SGSI" in p.text or "[" in p.text:
            _replace_paragraph_text(p, _adapt_sgsi_to_pims(p.text, org_name, dpo_name))

    # Añadir tablas resumen al final para lectura ejecutiva de Alta Dirección
    doc.add_heading("Anexo Cuantitativo 1: Distribución Anual de Incidentes y Brechas PII", level=2)
    by_year = summary.get("by_year", [])
    tbl_y = doc.add_table(rows=1 + len(by_year), cols=6)
    tbl_y.style = "Table Grid"
    headers_y = ["Año", "Total", "Abiertos", "Cerrados", "Críticos", "Brechas PII"]
    for c_i, h in enumerate(headers_y):
        tbl_y.rows[0].cells[c_i].text = h
    for r_i, y in enumerate(by_year, 1):
        vals = [y["year"], y["total"], y["open"], y["closed"], y["critical"], y["pii"]]
        for c_i, v in enumerate(vals):
            tbl_y.rows[r_i].cells[c_i].text = str(v)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ==============================================================================
# 3. PROCEDIMIENTO PARA MEDIDAS CORRECTIVAS (CLÁUSULA 10.2 + KPIS VIVOS)
# ==============================================================================

def export_corrective_procedure_docx(summary: Dict[str, Any], include_live_kpis: bool = True) -> bytes:
    """Adapta Procedimiento_para_medidas_correctivas_ES.docx a UNSA PIMS ISO/IEC 27701:2025."""
    tpl_path = _resolve_template("Procedimiento_para_medidas_correctivas_ES.docx")
    if not os.path.exists(tpl_path):
        raise FileNotFoundError(f"Plantilla de Procedimiento MC no encontrada en {tpl_path}")

    doc = docx.Document(tpl_path)
    cfg = summary.get("config", {})
    org_name = cfg.get("org_name") or "Universidad Nacional de San Agustín de Arequipa"
    dpo_name = cfg.get("dpo_name") or "Abog. Carlos Mendoza Valdivia (DPO UNSA)"
    rep_name = cfg.get("legal_rep_name") or "Dr. Hugo Rojas Flores"
    today = datetime.now().strftime("%Y-%m-%d")
    kpis = summary.get("procedure_kpis", {})

    specific_p = {
        6: "UNSA — SISTEMA DE GESTIÓN DE INFORMACIÓN DE PRIVACIDAD (PIMS)",
        7: f"{org_name} (RUC: {cfg.get('org_ruc', '20140798781')})",
        10: "PROCEDIMIENTO PARA MEDIDAS CORRECTIVAS (ISO/IEC 27701:2025 CLÁUSULA 10.2)",
        38: "Norma ISO/IEC 27701:2025, Cláusula 10.2 (No conformidad y medida correctiva)",
        39: "Norma ISO/IEC 27701:2025, Cláusula 8.1 y Controles A.3.11 / A.3.12 / A.3.14",
        40: "Ley Peruana N° 29733 y Directiva de Seguridad de la Información",
        60: f"Este documento es válido hasta el {datetime.now().year + 1}-12-31.",
        61: f"El propietario de este documento es el {dpo_name}, quien debe revisarlo y actualizarlo anualmente.",
        71: "Oficial de Protección de Datos Personales (DPO) / Aprobado por Rectorado",
        72: f"{dpo_name} | {rep_name}",
    }
    if include_live_kpis:
        specific_p[63] = f"• Cantidad de medidas correctivas iniciadas (BD PIMS): {kpis.get('mc_iniciadas', 0)}"
        specific_p[64] = f"• Cantidad de medidas correctivas incompletas (Abiertas / En progreso): {kpis.get('mc_incompletas', 0)}"
        specific_p[65] = f"• Cantidad de incidentes sin Formulario D34 registrado: {kpis.get('incidentes_sin_formulario_d34', 0)}"

    for idx, p in enumerate(doc.paragraphs):
        if idx in specific_p:
            _replace_paragraph_text(p, specific_p[idx])
        elif p.text.strip():
            adapted = _adapt_sgsi_to_pims(p.text, org_name, dpo_name)
            if adapted != p.text:
                _replace_paragraph_text(p, adapted)

    # Tabla 0: Metadatos de control documental
    if len(doc.tables) > 0 and len(doc.tables[0].rows) >= 6:
        t0 = doc.tables[0]
        meta_vals = ["PIMS-PRO-10.2", "2.0 (ISO/IEC 27701:2025)", today, dpo_name, rep_name, "Uso Interno Institucional UNSA"]
        for r_i, val in enumerate(meta_vals):
            if len(t0.rows[r_i].cells) > 1:
                t0.rows[r_i].cells[1].text = val

    # Tabla 1: Historial de modificaciones
    if len(doc.tables) > 1 and len(doc.tables[1].rows) > 2:
        r2 = doc.tables[1].rows[2]
        vals = [today, "2.0", dpo_name, "Adaptación oficial PIMS UNSA a ISO/IEC 27701:2025 Cl. 10.2 e integración KPIs"]
        for c_i, val in enumerate(vals[:len(r2.cells)]):
            r2.cells[c_i].text = val

    # Tabla 2: Pasos y responsables
    if len(doc.tables) > 2:
        for r in doc.tables[2].rows:
            for c in r.cells:
                if "SGSI" in c.text or "[cargo]" in c.text:
                    c.text = _adapt_sgsi_to_pims(c.text, org_name, "DPO / CISO UNSA")

    # Tabla 3: Gestión de registros
    if len(doc.tables) > 3 and len(doc.tables[3].rows) > 1:
        r1 = doc.tables[3].rows[1]
        reg_vals = [
            "Formulario D34 (a6_corrective_action)",
            "BD Única PIMS (empresa_conocimiento.db) — Módulo Medidas Correctivas",
            dpo_name,
            "Bitácora inmutable A.3.14, respaldo SHA-256 y control de acceso por rol",
            "Mínimo 3 años (o 5 años si involucra brechas PII)",
        ]
        for c_i, val in enumerate(reg_vals[:len(r1.cells)]):
            r1.cells[c_i].text = val

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ==============================================================================
# 4. INFORME DE NO CONFORMIDADES Y AUDITORÍA INTERNA (CL. 9.2 -> 10.2)
# ==============================================================================

def export_audit_nonconformities_docx(
    summary: Dict[str, Any],
    items_override: Optional[List[Dict[str, str]]] = None,
    blank: bool = False,
) -> bytes:
    """Genera Apéndice 2 adaptado a PIMS ISO/IEC 27701:2025 con no conformidades y referencias MC."""
    tpl_path = _resolve_template("Apendice_2_Informe_de_auditoria_interna_ES.docx")
    if not os.path.exists(tpl_path):
        raise FileNotFoundError(f"Plantilla de Informe de Auditoría no encontrada en {tpl_path}")

    doc = docx.Document(tpl_path)
    cfg = summary.get("config", {})
    org_name = cfg.get("org_name") or "Universidad Nacional de San Agustín de Arequipa"
    dpo_name = cfg.get("dpo_name") or "Abog. Carlos Mendoza Valdivia (DPO UNSA)"
    today = datetime.now().strftime("%Y-%m-%d")

    for p in doc.paragraphs:
        if "Apéndice 2" in p.text:
            _replace_paragraph_text(p, f"Informe de Auditoría PIMS y No Conformidades — {org_name} (ISO/IEC 27701:2025 Cl. 9.2 / 10.2)")
        elif "[cargo]" in p.text:
            _replace_paragraph_text(p, "Oficial de Protección de Datos Personales (DPO UNSA)")
        elif "[nombre]" in p.text:
            _replace_paragraph_text(p, "" if blank else dpo_name)
        elif "[firma]" in p.text:
            _replace_paragraph_text(p, "[Firma Digital / Institucional]")

    if doc.tables:
        t = doc.tables[0]
        if not blank:
            if items_override is not None:
                nc_list = items_override
            else:
                mc_items = summary.get("mc_items", [])
                nc_list = [
                    {
                        "nc": f"[{m.get('iso27701_control_id') or 'A.3.12'}] {(m.get('nonconformity_desc') or m.get('incident_title') or '')[:180]}",
                        "ref": f"{m.get('mc_code', 'N/A')} ({m.get('status', 'ABIERTA')})" + (f" / {m['incident_code']}" if m.get("incident_code") else ""),
                    }
                    for m in mc_items
                ]

            if len(t.rows) >= 8:
                t.rows[0].cells[1].text = today
                t.rows[1].cells[1].text = "2023-01-01 al " + today
                t.rows[2].cells[1].text = f"{dpo_name} / Equipo Auditoría PIMS UNSA"
                t.rows[3].cells[1].text = "ISO/IEC 27701:2025 (Cl. 8.1, Cl. 9.2, Cl. 10.2 y 78 Controles Anexo A)"
                t.rows[4].cells[1].text = "Activos de Información, Sistemas Académicos, Clínicos y Documentación PIMS UNSA"
                t.rows[5].cells[0].text = f"Seguimiento de la auditoría:\n{summary.get('open_incidents', 0)} incidentes abiertos; {summary.get('corrective_actions', {}).get('pendientes', 0)} medidas correctivas pendientes."
                t.rows[6].cells[0].text = "Recomendaciones de mejora:\nEjecutar verificación de eficacia D34 y mantener inspecciones periódicas con DSPM + SQLGlot."
                t.rows[7].cells[2].text = str(len(nc_list))

            start_row = 9
            while len(t.rows) < start_row + len(nc_list):
                nr = t.add_row()
                nr.cells[0].merge(nr.cells[1])
            for idx, item in enumerate(nc_list):
                r = t.rows[start_row + idx]
                r.cells[0].text = item["nc"]
                r.cells[2].text = item["ref"]

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ==============================================================================
# 5. EXPEDIENTE DE INCIDENTE / BRECHA PII (.DOCX PROPIO B.3.12 + A.3.14)
# ==============================================================================

def _add_kv_table(doc: docx.Document, pairs: List[tuple]) -> None:
    tbl = doc.add_table(rows=len(pairs), cols=2)
    tbl.style = "Table Grid"
    for idx, (k, v) in enumerate(pairs):
        c0 = tbl.rows[idx].cells[0]
        c1 = tbl.rows[idx].cells[1]
        c0.text = str(k)
        if c0.paragraphs and c0.paragraphs[0].runs:
            c0.paragraphs[0].runs[0].bold = True
        c1.text = str(v if v is not None and str(v).strip() != "" else "—")


def export_incident_dossier_docx(
    incident: Dict[str, Any],
    ctrl_info: Dict[str, Any],
    actions: List[Dict[str, Any]],
    mc: Optional[Dict[str, Any]],
    attachments: List[Dict[str, Any]],
    history: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> bytes:
    """Genera Expediente Pericial completo de Incidente / Brecha PII bajo ISO/IEC 27701:2025."""
    doc = docx.Document()
    org_name = config.get("org_name") or "Universidad Nacional de San Agustín de Arequipa"
    code = incident.get("incident_code", "INC-UNSA")
    ctrl_id = incident.get("iso27701_control_id") or "A.3.12"

    doc.add_heading(f"EXPEDIENTE DE INCIDENTE / BRECHA PII — {code}", level=1)
    doc.add_paragraph(
        f"{org_name} • ISO/IEC 27701:2025 Cláusula 8.1, Controles A.3.11 / A.3.12 (B.3.12) y Bitácora A.3.14"
    )

    doc.add_heading("1. Identificación y Evaluación / Triaje B.3.12", level=2)
    pii_txt = "SÍ — Brecha de Datos Personales (PII)" if incident.get("involves_personal_data") else "NO — Incidente Técnico sin PII (IT)"
    _add_kv_table(doc, [
        ("Código de Expediente", code),
        ("Título", incident.get("title")),
        ("Descripción de los Hechos", incident.get("description")),
        ("Estado Actual", incident.get("status")),
        ("Involucra PII (B.3.12 Note 1)", pii_txt),
        ("Clasificación", incident.get("incident_type")),
        ("Severidad / Impacto", f"{incident.get('severity')} / {incident.get('impact')}"),
        ("Titulares Afectados", str(incident.get("num_affected_subjects", 0))),
        ("Fecha del Incidente / Detección", f"{incident.get('incident_date', '')} / {incident.get('detection_date', '')}"),
        ("Fecha de Cierre", incident.get("resolved_date") or "Abierto / Pendiente"),
        ("Activo / Sistema Comprometido", incident.get("compromised_system") or "N/A"),
        ("URL / Endpoint", incident.get("affected_url") or "N/A"),
        ("Reportado por", incident.get("reported_by") or "N/A"),
        ("Responsable Asignado", incident.get("assigned_to") or "Sin asignar"),
        ("Control ISO/IEC 27701:2025", f"{ctrl_id} — {ctrl_info.get('title', '')}"),
        ("Consecuencias Observadas (B.3.12)", incident.get("consequences_summary") or "En evaluación"),
        ("Recuperación de Datos (B.3.24)", f"{incident.get('data_recovered_status', 'NO_APLICA')} — {incident.get('data_recovered_detail') or ''}"),
        ("Notificación Autoridad (ANPD)", f"{'Sí (' + (incident.get('anpd_official_ref') or '') + ' - ' + (incident.get('anpd_notified_at') or '') + ')' if incident.get('anpd_notified') else 'No registrada'}"),
        ("Notificación a Titulares", f"{'Sí (' + (incident.get('subjects_notice_channel') or '') + ' - ' + (incident.get('subjects_notified_at') or '') + ')' if incident.get('subjects_notified') else 'No registrada'}"),
    ])

    if ctrl_info.get("annex_b_guidance"):
        doc.add_heading(f"2. Guía Oficial ISO/IEC 27701:2025 ({ctrl_id})", level=2)
        doc.add_paragraph(ctrl_info["annex_b_guidance"])

    doc.add_heading(f"3. Acciones de Contención, Remediación y Mitigación A.3.12 ({len(actions)})", level=2)
    if actions:
        tbl_a = doc.add_table(rows=1 + len(actions), cols=4)
        tbl_a.style = "Table Grid"
        for i, h in enumerate(["Tipo", "Fecha", "Responsable", "Descripción y Evidencia"]):
            tbl_a.rows[0].cells[i].text = h
        for r_i, a in enumerate(actions, 1):
            tbl_a.rows[r_i].cells[0].text = str(a.get("action_type", ""))
            tbl_a.rows[r_i].cells[1].text = str(a.get("action_date", ""))
            tbl_a.rows[r_i].cells[2].text = str(a.get("responsible", ""))
            ev = f" [Evidencia: {a['evidence']}]" if a.get("evidence") else ""
            tbl_a.rows[r_i].cells[3].text = f"{a.get('description', '')}{ev}"
    else:
        doc.add_paragraph("Sin acciones registradas hasta la fecha.")

    doc.add_heading("4. Medida Correctiva Cláusula 10.2 (Formulario D34)", level=2)
    if mc:
        _add_kv_table(doc, [
            ("Código MC", mc.get("mc_code")),
            ("Estado MC", mc.get("status")),
            ("Causa Raíz", mc.get("root_cause") or "Pendiente"),
            ("Medida a Implementar", mc.get("action_to_implement") or "Pendiente"),
            ("Fecha Límite / Responsable", f"{mc.get('due_date') or '—'} / {mc.get('responsible_name') or '—'}"),
        ])
    else:
        doc.add_paragraph("Sin Formulario D34 registrado para este incidente.")

    doc.add_heading(f"5. Evidencias ({len(attachments)}) y Bitácora Inmutable A.3.14 ({len(history)})", level=2)
    for att in attachments:
        doc.add_paragraph(f"• Archivo adjunto: {att.get('file_name')} (Subido: {att.get('uploaded_at')})")
    for h in history:
        doc.add_paragraph(f"• [{h.get('changed_at')}] {h.get('event_type')} — {h.get('actor')}: {h.get('description')}")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ==============================================================================
# 6. CENTRO DE PLANTILLAS EN BLANCO (5 PLANTILLAS OFICIALES .DOCX)
# ==============================================================================

PIMS_TEMPLATES_CATALOG = [
    {
        "id": "expediente_incidente",
        "title": "Reporte / Expediente de Incidente o Brecha PII",
        "clause": "A.3.11 / A.3.12 (B.3.12) / A.3.14",
        "origin": "Plantilla Propia ISO/IEC 27701:2025",
        "supports_import": True,
        "supports_export_live": False,
        "description": "Ficha estructurada para notificar e importar un incidente desde cualquier facultad/oficina directamente al modal de 3 pasos.",
        "blank_filename": "Plantilla_Reporte_Incidente_Brecha_ISO27701.docx",
    },
    {
        "id": "d34_medida_correctiva",
        "title": "Formulario D34 — Medida Correctiva (12 filas)",
        "clause": "Cláusula 10.2 ISO/IEC 27701:2025",
        "origin": "Adaptada de Apéndice D34",
        "supports_import": True,
        "supports_export_live": False,
        "description": "Formato oficial para documentar causa raíz, plan correctivo y revisión de eficacia; compatible con importación directa en Módulo 2 y Pestaña 3.",
        "blank_filename": "Plantilla_D34_Medidas_Correctivas_ISO27701.docx",
    },
    {
        "id": "d35_minutas_direccion",
        "title": "Minutas D35 de Revisión por la Dirección",
        "clause": "Cláusula 9.3 ISO/IEC 27701:2025",
        "origin": "Adaptada de Minutas de Dirección",
        "supports_import": False,
        "supports_export_live": True,
        "live_url": "/api/reports/management-review-d35?format=docx",
        "description": "Acta ejecutiva con asistentes, estado de no conformidades, incidentes disruptivos, métricas 2023–2026 y decisiones.",
        "blank_filename": "Plantilla_D35_Minutas_Revision_Direccion_PIMS.docx",
    },
    {
        "id": "procedimiento_mc",
        "title": "Procedimiento Oficial de Medidas Correctivas",
        "clause": "Cláusula 10.2 & A.3.14",
        "origin": "Adaptada de Procedimiento MC",
        "supports_import": False,
        "supports_export_live": True,
        "live_url": "/api/reports/corrective-procedure-docx",
        "description": "Documento normativo de los 9 pasos de medida correctiva adaptado a roles UNSA, incluyendo KPIs de eficacia calculados en vivo.",
        "blank_filename": "Procedimiento_Medidas_Correctivas_PIMS_UNSA.docx",
    },
    {
        "id": "informe_auditoria_nc",
        "title": "Informe de Auditoría Interna y No Conformidades",
        "clause": "Cláusula 9.2 → Cláusula 10.2",
        "origin": "Adaptada de Apéndice 2 Auditoría",
        "supports_import": True,
        "supports_export_live": True,
        "live_url": "/api/reports/audit-nonconformities-docx",
        "description": "Tabla consolidada de no conformidades y referencias cruzadas MC; se puede exportar desde BD o subir al Inspector DSPM.",
        "blank_filename": "Plantilla_Informe_Auditoria_NoConformidades_PIMS.docx",
    },
]


def export_blank_template_docx(template_id: str, config: Optional[Dict[str, Any]] = None) -> bytes:
    """Genera una plantilla Word (.docx) en blanco adaptada a PIMS UNSA lista para llenar."""
    cfg = config or {}
    org_name = cfg.get("org_name") or "Universidad Nacional de San Agustín de Arequipa"

    if template_id == "expediente_incidente":
        doc = docx.Document()
        doc.add_heading("REPORTE DE INCIDENTE DE SEGURIDAD / BRECHA PII (ISO/IEC 27701:2025)", level=1)
        doc.add_paragraph(f"{org_name} • Complete la columna derecha y suba este archivo en el Módulo 1 ('Importar Reporte .docx').")
        _add_kv_table(doc, [
            ("Título del Incidente", ""),
            ("Descripción técnica de los hechos", ""),
            ("Fecha del Incidente (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d")),
            ("Fecha de Detección (YYYY-MM-DD)", datetime.now().strftime("%Y-%m-%d")),
            ("Sistema / Activo Afectado", ""),
            ("URL / Endpoint Afectado", ""),
            ("¿Involucra Datos Personales (PII)? (SÍ / NO)", "SÍ"),
            ("Clasificación (BF / BI / BD / PI / IT)", "BF"),
            ("Severidad (C / A / M / B)", "A"),
            ("Titulares Afectados (Cantidad)", "0"),
            ("Control ISO/IEC 27701:2025", "A.3.12"),
            ("Consecuencias Observadas", ""),
            ("Responsable Sugerido", ""),
            ("Acción Inicial de Contención A.3.12", ""),
        ])
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    if template_id == "d34_medida_correctiva":
        tpl_path = _resolve_template("Apendice_Formulario_para_medidas_correctivas_ES.docx")
        with open(tpl_path, "rb") as f:
            return f.read()

    if template_id == "d35_minutas_direccion":
        tpl_path = _resolve_template("Minutas_de_Revision_por_parte_de_la_direccion_ES.docx")
        doc = docx.Document(tpl_path)
        for p in doc.paragraphs:
            if "SGSI" in p.text or "[nombre del organismo]" in p.text:
                _replace_paragraph_text(p, _adapt_sgsi_to_pims(p.text, org_name))
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    if template_id == "procedimiento_mc":
        return export_corrective_procedure_docx({"config": cfg}, include_live_kpis=False)

    if template_id == "informe_auditoria_nc":
        return export_audit_nonconformities_docx({"config": cfg}, blank=True)

    raise KeyError(f"Plantilla desconocida: {template_id}")
