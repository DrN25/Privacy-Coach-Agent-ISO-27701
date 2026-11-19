import io
from pathlib import Path

import docx
import pytest
from fastapi.testclient import TestClient

from backend.api.routers import incidents as incidents_router
from backend.app import app
from backend.infrastructure.repository import repository


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _cleanup_created_incident(inc_id: int) -> None:
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


def test_seeded_baseline_and_kpis():
    with TestClient(app) as client:
        resp = client.get("/api/incidents")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 15
    assert {inc["year"] for inc in data["incidents"]} == {2023, 2024, 2025, 2026}

    kpis = data["kpis"]
    assert kpis["abiertos"] == 9
    assert kpis["cerrados"] == 6
    assert kpis["criticos_abiertos"] == 4
    assert kpis["brechas_pii"] == 13
    assert kpis["incidentes_tecnicos"] == 2


def test_incidents_filters():
    with TestClient(app) as client:
        r_year = client.get("/api/incidents?year=2024")
        r_open = client.get("/api/incidents?status=OPEN")
        r_sev = client.get("/api/incidents?severity=C")
        r_tech = client.get("/api/incidents?classification=TECH")

    assert r_year.status_code == 200
    year_items = r_year.json()["incidents"]
    assert len(year_items) == 3
    assert all(inc["year"] == 2024 for inc in year_items)

    assert r_open.status_code == 200
    open_items = r_open.json()["incidents"]
    assert len(open_items) == 9
    assert all(inc["status"] in ("I", "E") for inc in open_items)

    assert r_sev.status_code == 200
    sev_items = r_sev.json()["incidents"]
    assert len(sev_items) >= 4
    assert all(inc["severity"] == "C" for inc in sev_items)

    assert r_tech.status_code == 200
    tech_ids = {inc["id"] for inc in r_tech.json()["incidents"]}
    assert tech_ids == {612, 615}


def test_catalogs_users_assets_and_iso27701_controls():
    with TestClient(app) as client:
        r_users = client.get("/api/users")
        r_assets = client.get("/api/unsa-assets")
        r_ctrl = client.get("/api/controls/iso27701")

    assert r_users.status_code == 200
    assert r_users.json()["total"] == 18
    assert len(r_users.json()["users"]) == 18

    assert r_assets.status_code == 200
    assert r_assets.json()["total"] == 10
    assert len(r_assets.json()["assets"]) == 10

    assert r_ctrl.status_code == 200
    ctrl_data = r_ctrl.json()
    assert ctrl_data["total"] == 78
    assert len(ctrl_data["controls"]) == 78

    by_id = {c["id"]: c["title"] for c in ctrl_data["controls"]}
    assert by_id["A.3.11"] == "Information security incident management planning and preparation"
    assert by_id["A.3.12"] == "Response to information security incidents"
    assert by_id["A.3.23"] == "Secure authentication"
    assert by_id["A.3.24"] == "Information backup"
    assert by_id["A.3.26"] == "Use of cryptography"
    assert by_id["A.3.31"] == "Test information"


def test_d34_corrective_action_save_and_export_docx():
    saved_root_cause = "Falta de política de transferencia internacional y validación previa del DPO en scripts cron."
    saved_action = "Suspender sincronización S3 externa, firmar Addendum SCC y migrar respaldos a repositorio nacional."

    with TestClient(app) as client:
        put_resp = client.put(
            "/api/incidents/604/corrective-action",
            headers={"X-Actor-Id": "601"},
            json={
                "root_cause": saved_root_cause,
                "action_to_implement": saved_action,
                "status": "EN_PROGRESO",
                "action_required": False,
            },
        )
        assert put_resp.status_code == 200
        mc = put_resp.json()["corrective_action"]
        assert mc["status"] == "EN_PROGRESO"
        assert bool(mc["action_required"]) is False

        docx_resp = client.get("/api/incidents/604/corrective-action/export-docx")

    assert docx_resp.status_code == 200
    assert (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        in docx_resp.headers.get("content-type", "")
    )

    doc = docx.Document(io.BytesIO(docx_resp.content))
    table = doc.tables[0]
    row0_text = " ".join(c.text for c in table.rows[0].cells)
    row3_text = " ".join(c.text for c in table.rows[3].cells)
    row5_text = " ".join(c.text for c in table.rows[5].cells)
    row6_text = " ".join(c.text for c in table.rows[6].cells)

    assert "MC-UNSA-2026-004" in row0_text
    assert "INC-UNSA-2026-004" in row0_text
    assert saved_root_cause in row3_text
    assert "[NO]" in row5_text
    assert saved_action in row6_text


def test_security_logs_for_incident_601():
    with TestClient(app) as client:
        resp = client.get("/api/security-logs?incident_id=601")

    assert resp.status_code == 200
    logs = resp.json()["logs"]
    assert len(logs) >= 1
    assert all(log["object_id"] == 102 for log in logs)


def test_management_review_d35():
    with TestClient(app) as client:
        r_json = client.get("/api/reports/management-review-d35")
        r_md = client.get("/api/reports/management-review-d35?format=markdown")
        r_docx = client.get("/api/reports/management-review-d35?format=docx")

    assert r_json.status_code == 200
    summary = r_json.json()["summary"]
    assert summary["total_incidents"] >= 15
    assert summary["open_incidents"] + summary["closed_incidents"] == summary["total_incidents"]

    assert r_md.status_code == 200
    assert "REVISIÓN POR LA DIRECCIÓN" in r_md.text

    assert r_docx.status_code == 200
    assert (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        in r_docx.headers.get("content-type", "")
    )
    doc = docx.Document(io.BytesIO(r_docx.content))
    assert len(doc.paragraphs) > 0


def test_seeded_attachment_download():
    with TestClient(app) as client:
        resp = client.get("/api/attachments/601/download")

    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


def test_upload_and_download_incident_attachment():
    sample_pdf = b"%PDF-1.4\n1 0 obj << /Type /Catalog >> endobj\n%%EOF\n"
    uploaded_rel = None

    try:
        with TestClient(app) as client:
            up_resp = client.post(
                "/api/incidents/601/attachments",
                headers={"X-Actor-Id": "601"},
                files={"file": ("evidencia_prueba_601.pdf", sample_pdf, "application/pdf")},
            )
            assert up_resp.status_code == 201
            att = up_resp.json()["attachment"]
            uploaded_rel = att["file"]

            list_resp = client.get("/api/incidents/601/attachments")
            assert list_resp.status_code == 200
            att_ids = [a["id"] for a in list_resp.json()["attachments"]]
            assert att["id"] in att_ids

            dl_resp = client.get(f"/api/attachments/{att['id']}/download")
            assert dl_resp.status_code == 200
            assert dl_resp.content == sample_pdf
    finally:
        if uploaded_rel:
            rel_sub = uploaded_rel[len("uploads_evidencias/"):] if uploaded_rel.startswith("uploads_evidencias/") else uploaded_rel
            for base_media in (
                Path(incidents_router._get_writable_evidences_dir()),
                Path(incidents_router.MEDIA_DIR),
                PROJECT_ROOT / "media",
            ):
                candidate = base_media / rel_sub.lstrip("/\\")
                if candidate.exists():
                    candidate.unlink()
        src_media = PROJECT_ROOT / "src" / "media"
        src_evid = src_media / "evidencias"
        if src_evid.exists() and not any(src_evid.iterdir()):
            src_evid.rmdir()
        if src_media.exists() and not any(src_media.iterdir()):
            src_media.rmdir()


def test_incident_full_crud_lifecycle():
    headers = {"X-Actor-Id": "601"}
    inc_id = None

    try:
        with TestClient(app) as client:
            create_resp = client.post(
                "/api/incidents",
                headers=headers,
                json={
                    "title": "Prueba ciclo completo A.3.12",
                    "description": "Incidente creado en prueba de ciclo completo CRUD.",
                    "severity": "A",
                    "iso27701_control_id": "A.3.12",
                    "create_mc_draft": True,
                },
            )
            assert create_resp.status_code == 201
            inc = create_resp.json()["incident"]
            inc_id = inc["id"]
            assert inc["incident_code"].startswith("INC-UNSA-")
            assert (inc.get("mc_code") or "").startswith("MC-UNSA-")

            # No puede cerrarse sin acciones A.3.12
            fail_close = client.patch(
                f"/api/incidents/{inc_id}/status",
                headers=headers,
                json={"status": "C"},
            )
            assert fail_close.status_code == 400

            # Registrar acción de contención y luego cerrar
            act_resp = client.post(
                f"/api/incidents/{inc_id}/actions",
                headers=headers,
                json={
                    "action_type": "C",
                    "description": "Aislamiento inmediato del endpoint afectado.",
                    "evidence": "Ticket CSIRT-TEST-01",
                },
            )
            assert act_resp.status_code == 201

            close_resp = client.patch(
                f"/api/incidents/{inc_id}/status",
                headers=headers,
                json={"status": "C"},
            )
            assert close_resp.status_code == 200
            closed_inc = close_resp.json()["incident"]
            assert closed_inc["status"] == "C"
            assert closed_inc["resolved_date"]

            hist_after_close = client.get(f"/api/incidents/{inc_id}/history").json()["history"]
            assert any(h["event_type"] == "CIERRE" for h in hist_after_close)

            # Reabrir sin motivo debe fallar con 400
            fail_reopen = client.patch(
                f"/api/incidents/{inc_id}/status",
                headers=headers,
                json={"status": "I", "reason": ""},
            )
            assert fail_reopen.status_code == 400

            # Reabrir con motivo válido limpia resolved_date y registra REAPERTURA
            reopen_resp = client.patch(
                f"/api/incidents/{inc_id}/status",
                headers=headers,
                json={"status": "I", "reason": "Se requiere validación adicional de logs."},
            )
            assert reopen_resp.status_code == 200
            reopened_inc = reopen_resp.json()["incident"]
            assert reopened_inc["status"] == "I"
            assert reopened_inc["resolved_date"] is None

            hist_after_reopen = client.get(f"/api/incidents/{inc_id}/history").json()["history"]
            assert any(h["event_type"] == "REAPERTURA" for h in hist_after_reopen)

            # Asignar responsable
            assign_resp = client.patch(
                f"/api/incidents/{inc_id}/assign",
                headers=headers,
                json={"assigned_to_id": 604},
            )
            assert assign_resp.status_code == 200
            assert "Marcos Ruiz Benavente" in assign_resp.json()["incident"]["assigned_to"]

            hist_after_assign = client.get(f"/api/incidents/{inc_id}/history").json()["history"]
            assert any(h["event_type"] == "ASIGNACION" for h in hist_after_assign)

            # Actualizar ficha B.3.12 y notificación documental ANPD
            patch_resp = client.patch(
                f"/api/incidents/{inc_id}",
                headers=headers,
                json={
                    "data_recovered_status": "RECUPERADO_TOTAL",
                    "consequences_summary": "Contención verificada sin exfiltración externa.",
                    "anpd_notified": True,
                    "anpd_official_ref": "Oficio N° 900-2026-DPO-UNSA",
                    "anpd_notified_at": "2026-11-18 11:30:00",
                },
            )
            assert patch_resp.status_code == 200
            patched_inc = patch_resp.json()["incident"]
            assert patched_inc["data_recovered_status"] == "RECUPERADO_TOTAL"
            assert patched_inc["consequences_summary"] == "Contención verificada sin exfiltración externa."
            assert patched_inc["anpd_notified"] is True
            assert patched_inc["anpd_official_ref"] == "Oficio N° 900-2026-DPO-UNSA"
    finally:
        if inc_id is not None:
            _cleanup_created_incident(inc_id)


def test_promote_dspm_finding_idempotent():
    promoted_inc_id = None
    try:
        with TestClient(app) as client:
            assert client.post("/api/reset").status_code == 200
            assert client.post("/api/load-mockups").status_code == 200
            view = client.get("/api/database-view").json()
            finding_id = view["hallazgos"][0]["id"]

            first = client.post(f"/api/incidents/from-finding/{finding_id}", headers={"X-Actor-Id": "601"})
            assert first.status_code == 200
            first_data = first.json()
            promoted_inc_id = first_data["incident"]["id"]
            assert first_data["already_exists"] is False
            assert first_data["incident"]["incident_code"].startswith("INC-UNSA-")

            second = client.post(f"/api/incidents/from-finding/{finding_id}", headers={"X-Actor-Id": "601"})
            assert second.status_code == 200
            second_data = second.json()
            assert second_data["already_exists"] is True
            assert second_data["incident"]["id"] == promoted_inc_id
    finally:
        if promoted_inc_id is not None:
            _cleanup_created_incident(promoted_inc_id)


def test_db_checkpoint_and_reset_demo_seed():
    with TestClient(app) as client:
        info0 = client.get("/api/db/info")
        assert info0.status_code == 200
        assert info0.json()["incidents_count"] == 15

        # 1. Guardar checkpoint con 15 incidentes
        snap = client.post("/api/db/checkpoint")
        assert snap.status_code == 200
        assert snap.json()["info"]["has_checkpoint"] is True

        # 2. Crear un incidente #16 de prueba
        created = client.post(
            "/api/incidents",
            headers={"X-Actor-Id": "601"},
            json={"title": "Incidente temporal antes de restaurar snapshot", "severity": "B"},
        )
        assert created.status_code == 201
        assert client.get("/api/db/info").json()["incidents_count"] == 16

        # 3. Restaurar checkpoint -> vuelve a 15 incidentes
        restored = client.post("/api/db/restore-checkpoint")
        assert restored.status_code == 200
        assert restored.json()["info"]["incidents_count"] == 15

        # 4. Reset demo seed -> vuelve al estado base canónico (15 incidentes)
        reset_seed = client.post("/api/db/reset-demo-seed")
        assert reset_seed.status_code == 200
        assert reset_seed.json()["info"]["incidents_count"] == 15


def test_legacy_sqlite_migrates_safely_on_init_db(tmp_path, monkeypatch):
    """Simula una BD SQLite antigua de VPS (solo 5 tablas DSPM) y verifica migración sin pérdida de datos."""
    import sqlite3
    from backend.db import init_db

    legacy_db = tmp_path / "legacy_vps.db"
    conn = sqlite3.connect(legacy_db)
    conn.executescript("""
        CREATE TABLE archivos_cargados (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_archivo TEXT NOT NULL, tipo_archivo TEXT NOT NULL, fecha_carga TEXT NOT NULL, tamano_bytes INTEGER, resumen_analisis TEXT);
        CREATE TABLE inventario_activos_datos (id INTEGER PRIMARY KEY AUTOINCREMENT, archivo_id INTEGER, nombre_tabla TEXT NOT NULL, nombre_columna TEXT NOT NULL, tipo_sql TEXT NOT NULL, es_clave_primaria INTEGER DEFAULT 0, es_clave_foranea INTEGER DEFAULT 0, categoria_sensible TEXT NOT NULL, es_dato_sensible INTEGER DEFAULT 0, nivel_confianza REAL DEFAULT 1.0, candado_deteccion TEXT, recomendacion_seguridad TEXT);
        CREATE TABLE clausulas_documentales (id INTEGER PRIMARY KEY AUTOINCREMENT, archivo_id INTEGER, documento TEXT NOT NULL, numero_clausula TEXT, titulo_clausula TEXT, texto_clausula TEXT NOT NULL, tipo_clausula TEXT, estado_cumplimiento TEXT DEFAULT 'OBSERVADO', alerta_legal TEXT);
        CREATE TABLE hallazgos_dspm (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo_regla TEXT NOT NULL, titulo TEXT NOT NULL, descripcion TEXT NOT NULL, nivel_riesgo TEXT NOT NULL, elemento_afectado TEXT NOT NULL, origen_archivo TEXT NOT NULL, control_iso27701 TEXT NOT NULL, principio_iso29100 TEXT NOT NULL, articulo_ley29733 TEXT NOT NULL, directiva_seguridad TEXT NOT NULL, multa_estimada_uit REAL NOT NULL, multa_estimada_pen REAL NOT NULL, precedente_anpd TEXT NOT NULL, estado TEXT DEFAULT 'PENDIENTE', fecha_deteccion TEXT NOT NULL);
        CREATE TABLE interacciones_coach (id INTEGER PRIMARY KEY AUTOINCREMENT, hallazgo_id INTEGER, timestamp TEXT NOT NULL, rol TEXT NOT NULL, mensaje TEXT NOT NULL, pensamiento_reasoning TEXT, parche_sql TEXT);
        INSERT INTO archivos_cargados (nombre_archivo, tipo_archivo, fecha_carga, tamano_bytes, resumen_analisis) VALUES ('viejo_esquema.sql', 'SQL', '2026-01-01', 123, 'previo');
    """)
    conn.commit()
    conn.close()

    monkeypatch.setenv("DATABASE_PATH", str(legacy_db))
    init_db()

    conn2 = sqlite3.connect(legacy_db)
    try:
        assert conn2.execute("SELECT COUNT(*) FROM archivos_cargados WHERE nombre_archivo='viejo_esquema.sql'").fetchone()[0] == 1
        assert conn2.execute("SELECT COUNT(*) FROM core_incident").fetchone()[0] == 15
        assert conn2.execute("SELECT COUNT(*) FROM auth_user").fetchone()[0] == 18
        assert conn2.execute("SELECT COUNT(*) FROM a6_corrective_action").fetchone()[0] == 10
    finally:
        conn2.close()


def test_demo_files_draft_from_finding_ai_and_has_mc_filter(monkeypatch):
    from backend.api.routers import files as files_router
    from backend.infrastructure.llm_client import LLMResponse

    created_inc_id = None
    uploaded_names = ["demo_esquema_clinica_unsa.sql", "demo_politica_portal_unsa.txt"]

    monkeypatch.setattr(
        incidents_router.default_luna_client,
        "generate",
        lambda **kwargs: LLMResponse(
            content=(
                '{"title": "Brecha IA: Diagnósticos clínicos sin cifrar en laboratorio",'
                ' "description": "Descripción pericial enriquecida por IA para diagnóstico CIE-10 en texto plano.",'
                ' "consequences_summary": "Riesgo grave de exposición de historias clínicas bajo A.3.26.",'
                ' "initial_action_description": "Activar pgcrypto AES-256 sobre pacientes_laboratorio."}'
            ),
            mode="openrouter",
        ),
    )

    try:
        with TestClient(app) as client:
            assert client.post("/api/reset").status_code == 200

            demo_sql = (PROJECT_ROOT / "media" / "demos" / "demo_esquema_clinica_unsa.sql").read_bytes()
            up_sql = client.post(
                "/api/upload",
                files={"file": ("demo_esquema_clinica_unsa.sql", demo_sql, "text/plain")},
            )
            assert up_sql.status_code == 200
            assert client.post("/api/reanalyze").status_code == 200

            view_sql = client.get("/api/database-view").json()
            codes_sql = {h["codigo_regla"] for h in view_sql["hallazgos"]}
            assert {"R-001", "R-002", "R-003"}.issubset(codes_sql)

            r001 = next(h for h in view_sql["hallazgos"] if h["codigo_regla"] == "R-001")
            draft_resp = client.post(f"/api/incidents/draft-from-finding/{r001['id']}")
            assert draft_resp.status_code == 200
            draft_payload = draft_resp.json()
            assert draft_payload["already_exists"] is False
            assert draft_payload["ai_enriched"] is True
            draft = draft_payload["draft"]
            assert draft["iso27701_control_id"] == "A.3.26"
            assert draft["asset_id"] == 102
            assert draft["assigned_to_id"] == 605
            assert draft["source_finding_id"] == r001["id"]
            assert draft["title"].startswith("Brecha IA:")
            assert client.get("/api/db/info").json()["incidents_count"] == 15

            confirm = client.post("/api/incidents", headers={"X-Actor-Id": "601"}, json=draft)
            assert confirm.status_code == 201
            created_inc = confirm.json()["incident"]
            created_inc_id = created_inc["id"]
            assert created_inc["mc_code"].startswith("MC-UNSA-")

            detail = client.get(f"/api/incidents/{created_inc_id}")
            assert detail.status_code == 200
            assert detail.json()["corrective_action"]["mc_code"] == created_inc["mc_code"]

            view_after = client.get("/api/database-view").json()
            r001_after = next(h for h in view_after["hallazgos"] if h["id"] == r001["id"])
            assert r001_after["promoted_incident_id"] == created_inc_id
            assert r001_after["promoted_incident_code"] == created_inc["incident_code"]

            draft_again = client.post(f"/api/incidents/draft-from-finding/{r001['id']}")
            assert draft_again.status_code == 200
            assert draft_again.json()["already_exists"] is True
            assert draft_again.json()["incident"]["id"] == created_inc_id

            # Verificar filtro has_mc y detección en demo TXT
            with_mc = client.get("/api/incidents?has_mc=WITH_MC").json()["incidents"]
            without_mc = client.get("/api/incidents?has_mc=WITHOUT_MC").json()["incidents"]
            assert all(i.get("mc_id") for i in with_mc)
            assert all(not i.get("mc_id") for i in without_mc)
            assert any(i["id"] == created_inc_id for i in with_mc)

            demo_txt = (PROJECT_ROOT / "media" / "demos" / "demo_politica_portal_unsa.txt").read_bytes()
            assert client.post(
                "/api/upload",
                files={"file": ("demo_politica_portal_unsa.txt", demo_txt, "text/plain")},
            ).status_code == 200
            assert client.post("/api/reanalyze").status_code == 200
            view_txt = client.get("/api/database-view").json()
            codes_txt = {h["codigo_regla"] for h in view_txt["hallazgos"]}
            assert {"R-004", "R-005", "R-007"}.issubset(codes_txt)
    finally:
        if created_inc_id is not None:
            _cleanup_created_incident(created_inc_id)
        for name in uploaded_names:
            for base_up in (
                Path(files_router._get_writable_uploads_dir()),
                PROJECT_ROOT / "media" / "uploads",
            ):
                p = base_up / name
                if p.exists():
                    p.unlink()
        repository.resetear_base_de_datos()



