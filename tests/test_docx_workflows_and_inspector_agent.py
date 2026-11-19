import io
from pathlib import Path

import docx
from fastapi.testclient import TestClient

from backend.agents import doc_inspector_agent
from backend.api.routers import files as files_router
from backend.app import app
from backend.infrastructure.llm_client import LLMResponse
from backend.infrastructure.repository import repository

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _delete_mc_by_id(mc_id: int) -> None:
    conn = repository._pims_conn()
    try:
        conn.execute("DELETE FROM a6_corrective_action WHERE id = ?", (mc_id,))
        conn.commit()
    finally:
        conn.close()


def _delete_incident_tree(inc_id: int) -> None:
    conn = repository._pims_conn()
    try:
        conn.execute("DELETE FROM a6_corrective_action WHERE incident_id = ?", (inc_id,))
        conn.execute("DELETE FROM core_incidentaction WHERE incident_id = ?", (inc_id,))
        conn.execute("DELETE FROM core_incidenthistory WHERE incident_id = ?", (inc_id,))
        conn.execute("DELETE FROM core_incidentattachment WHERE incident_id = ?", (inc_id,))
        conn.execute("DELETE FROM a6_incident_ext WHERE incident_id = ?", (inc_id,))
        conn.execute("DELETE FROM core_incident WHERE id = ?", (inc_id,))
        conn.commit()
    finally:
        conn.close()


def test_export_all_five_official_docx_and_blank_templates():
    with TestClient(app) as client:
        # 1. Expediente completo de Incidente (.docx)
        r_inc = client.get("/api/incidents/601/export-docx")
        assert r_inc.status_code == 200
        d_inc = docx.Document(io.BytesIO(r_inc.content))
        txt_inc = "\n".join(p.text for p in d_inc.paragraphs)
        assert "INC-UNSA-2026-001" in txt_inc
        assert len(d_inc.tables) >= 2

        # 2. D35 Minutas de Revisión por la Dirección (sobre plantilla oficial adaptada a PIMS)
        r_d35 = client.get("/api/reports/management-review-d35?format=docx")
        assert r_d35.status_code == 200
        d_d35 = docx.Document(io.BytesIO(r_d35.content))
        txt_d35 = "\n".join(p.text for p in d_d35.paragraphs)
        assert "MINUTAS DE REVISIÓN POR LA DIRECCIÓN" in txt_d35
        assert "ISO/IEC 27701:2025" in txt_d35
        assert "Cl. 10.2" in txt_d35

        # 3. Procedimiento de Medidas Correctivas (con KPIs en vivo desde SQLite)
        r_proc = client.get("/api/reports/corrective-procedure-docx")
        assert r_proc.status_code == 200
        d_proc = docx.Document(io.BytesIO(r_proc.content))
        txt_proc = "\n".join(p.text for p in d_proc.paragraphs)
        assert "ISO/IEC 27701:2025" in txt_proc
        assert "medidas correctivas iniciadas (BD PIMS):" in txt_proc

        # 4. Informe de Auditoría y No Conformidades (Apéndice 2 adaptado)
        r_aud = client.get("/api/reports/audit-nonconformities-docx")
        assert r_aud.status_code == 200
        d_aud = docx.Document(io.BytesIO(r_aud.content))
        assert len(d_aud.tables) >= 1
        tbl_aud_txt = "\n".join(c.text for row in d_aud.tables[0].rows for c in row.cells)
        assert "MC-UNSA-" in tbl_aud_txt

        # 5. Catálogo y descarga en blanco de las 5 plantillas PIMS
        cat = client.get("/api/templates/pims")
        assert cat.status_code == 200
        tpls = cat.json()["templates"]
        assert len(tpls) == 5
        for tpl in tpls:
            dl = client.get(f"/api/templates/pims/{tpl['id']}/blank")
            assert dl.status_code == 200
            parsed = docx.Document(io.BytesIO(dl.content))
            assert len(parsed.paragraphs) > 0


def test_standalone_corrective_action_and_import_d34_docx():
    created_mc_ids = []
    try:
        with TestClient(app) as client:
            # Importar demo_d34_medida_correctiva.docx
            raw_d34 = (PROJECT_ROOT / "media" / "demos" / "demo_d34_medida_correctiva.docx").read_bytes()
            imp = client.post(
                "/api/corrective-actions/import-docx",
                files={"file": ("demo_d34_medida_correctiva.docx", raw_d34, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
            assert imp.status_code == 200
            draft = imp.json()["draft"]
            assert draft["iso27701_control_id"] == "A.3.31"
            assert "anonimización" in draft["nonconformity_desc"]
            assert "enmascaramiento" in draft["root_cause"]
            assert draft["action_required"] is True

            # Crear MC independiente SIN incidente previo (Cláusula 10.2 por Auditoría Interna)
            draft.pop("mc_code", None)
            draft["incident_id"] = None
            draft["source_type"] = "AUDITORIA_INTERNA"
            created = client.post("/api/corrective-actions", headers={"X-Actor-Id": "601"}, json=draft)
            assert created.status_code == 201
            mc = created.json()["corrective_action"]
            created_mc_ids.append(mc["id"])
            assert mc["incident_id"] is None
            assert mc["source_type"] == "AUDITORIA_INTERNA"
            assert mc["iso27701_control_id"] == "A.3.31"

            # Listar en consolidado, actualizar y exportar por mc_id sin incidente
            lst = client.get("/api/corrective-actions").json()["corrective_actions"]
            assert any(item["id"] == mc["id"] for item in lst)

            upd = client.put(
                f"/api/corrective-actions/{mc['id']}",
                headers={"X-Actor-Id": "601"},
                json={"status": "IMPLEMENTADA", "implemented_on": "2026-11-18"},
            )
            assert upd.status_code == 200
            assert upd.json()["corrective_action"]["status"] == "IMPLEMENTADA"

            exp = client.get(f"/api/corrective-actions/{mc['id']}/export-docx")
            assert exp.status_code == 200
            exp_doc = docx.Document(io.BytesIO(exp.content))
            assert mc["mc_code"] in " ".join(c.text for c in exp_doc.tables[0].rows[0].cells)
    finally:
        for mid in created_mc_ids:
            _delete_mc_by_id(mid)


def test_import_incident_report_docx_to_draft_and_create():
    created_inc_id = None
    try:
        with TestClient(app) as client:
            raw_inc = (PROJECT_ROOT / "media" / "demos" / "demo_reporte_incidente_qa.docx").read_bytes()
            imp = client.post(
                "/api/incidents/import-docx",
                files={"file": ("demo_reporte_incidente_qa.docx", raw_inc, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
            assert imp.status_code == 200
            draft = imp.json()["draft"]
            assert "laboratorio" in draft["title"].lower()
            assert draft["iso27701_control_id"] == "A.3.31"
            assert draft["severity"] == "C"
            assert draft["num_affected_subjects"] == 620
            assert draft["involves_personal_data"] is True

            # Confirmar creación desde borrador importado
            create = client.post("/api/incidents", headers={"X-Actor-Id": "601"}, json=draft)
            assert create.status_code == 201
            created_inc_id = create.json()["incident"]["id"]
    finally:
        if created_inc_id is not None:
            _delete_incident_tree(created_inc_id)


def test_upload_audit_docx_and_ai_document_inspector_subagent(monkeypatch):
    uploaded_name = "demo_informe_auditoria_interna.docx"
    promoted_inc_id = None

    # Respuesta controlada del LLM simulando 1 hallazgo válido (A.3.18) y 1 código inventado (A.9.9.9) que debe descartarse
    monkeypatch.setattr(
        doc_inspector_agent.default_luna_client,
        "generate",
        lambda **kwargs: LLMResponse(
            content=(
                '{"tipo_documento": "Informe de Auditoría Interna PIMS (.docx)",'
                ' "resumen_ejecutivo": "Se identificaron brechas de anonimización en QA y falta de NDA en personal temporal.",'
                ' "hallazgos": ['
                '   {"control_iso27701": "A.3.18", "titulo": "Personal temporal sin acuerdo de confidencialidad firmado",'
                '    "descripcion": "Digitalización de expedientes con DNI sin NDA ni compromiso PIMS vigente.",'
                '    "elemento_afectado": "Mesa de Partes / Digitalización", "origen_archivo": "demo_informe_auditoria_interna.docx",'
                '    "nivel_riesgo": "ALTO", "recomendacion": "Suscribir acuerdos de confidencialidad A.3.18 previos al acceso."},'
                '   {"control_iso27701": "A.9.9.9", "titulo": "Control inventado que debe filtrarse",'
                '    "descripcion": "No existe en ISO/IEC 27701:2025.", "nivel_riesgo": "BAJO"}'
                ' ]}'
            ),
            mode="openrouter",
        ),
    )

    try:
        with TestClient(app) as client:
            assert client.post("/api/reset").status_code == 200
            raw_aud = (PROJECT_ROOT / "media" / "demos" / uploaded_name).read_bytes()
            up = client.post(
                "/api/upload",
                files={"file": (uploaded_name, raw_aud, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
            assert up.status_code == 200
            assert client.post("/api/reanalyze").status_code == 200

            view1 = client.get("/api/database-view").json()
            aud_findings = [h for h in view1["hallazgos"] if h["codigo_regla"] == "AUD-NC"]
            assert len(aud_findings) == 2
            assert any(h["control_iso27701"] == "A.3.31" for h in aud_findings)

            # Invocar Subagente IA Documental
            ai_res = client.post("/api/inspector/ai-analyze")
            assert ai_res.status_code == 200
            ai_data = ai_res.json()
            assert ai_data["ai_executed"] is True
            assert ai_data["hallazgos_nuevos"] == 1  # A.9.9.9 descartado

            view2 = client.get("/api/database-view").json()
            ia_finding = next(h for h in view2["hallazgos"] if h["codigo_regla"] == "IA-A.3.18")
            assert ia_finding["control_iso27701"] == "A.3.18"

            # Verificar que draft-from-finding respeta el control A.3.18 del subagente IA
            draft_res = client.post(f"/api/incidents/draft-from-finding/{ia_finding['id']}")
            assert draft_res.status_code == 200
            draft = draft_res.json()["draft"]
            assert draft["iso27701_control_id"] == "A.3.18"

            created = client.post("/api/incidents", headers={"X-Actor-Id": "601"}, json=draft)
            assert created.status_code == 201
            promoted_inc_id = created.json()["incident"]["id"]
    finally:
        if promoted_inc_id is not None:
            _delete_incident_tree(promoted_inc_id)
        for base_up in (Path(files_router._get_writable_uploads_dir()), PROJECT_ROOT / "media" / "uploads"):
            p = base_up / uploaded_name
            if p.exists():
                p.unlink()
        repository.resetear_base_de_datos()
