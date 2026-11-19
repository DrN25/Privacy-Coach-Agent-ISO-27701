"""
Esquema SQLite unificado e idempotente para Agente 6 (ISO/IEC 27701:2025 PIMS).
Alineado a las tablas institucionales de BD/gestitel_base_de_datos.sql + nuevas tablas a6_*.
"""

import json
import sqlite3
from typing import Optional

from ..core.rules_catalog import VALOR_UIT_PEN


def init_pims_tables(conn: sqlite3.Connection) -> None:
    """Crea tablas core_* y a6_* si no existen y ejecuta semilla determinista 2023-2026."""
    cur = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS auth_user (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        password TEXT NOT NULL DEFAULT '!unusable',
        last_login TEXT,
        is_superuser INTEGER NOT NULL DEFAULT 0,
        username TEXT NOT NULL UNIQUE,
        first_name TEXT NOT NULL DEFAULT '',
        last_name TEXT NOT NULL DEFAULT '',
        email TEXT NOT NULL DEFAULT '',
        is_staff INTEGER NOT NULL DEFAULT 0,
        is_active INTEGER NOT NULL DEFAULT 1,
        date_joined TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS core_userprofile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area TEXT,
        position TEXT,
        user_id INTEGER NOT NULL REFERENCES auth_user(id),
        is_platform_admin INTEGER NOT NULL DEFAULT 0,
        must_change_password INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS core_process (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        is_deleted INTEGER NOT NULL DEFAULT 0,
        deleted_at TEXT,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        area TEXT NOT NULL,
        responsible TEXT NOT NULL,
        objective TEXT NOT NULL,
        status TEXT NOT NULL,
        created_by_id INTEGER NOT NULL DEFAULT 1,
        deleted_by_id INTEGER,
        updated_by_id INTEGER
    );

    CREATE TABLE IF NOT EXISTS core_asset (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        is_deleted INTEGER NOT NULL DEFAULT 0,
        deleted_at TEXT,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        owner TEXT,
        custodians TEXT,
        location TEXT,
        is_data_asset INTEGER NOT NULL DEFAULT 1,
        category TEXT,
        classification TEXT,
        usage_frequency TEXT,
        confidentiality TEXT,
        integrity TEXT,
        availability TEXT,
        weight_confidentiality REAL NOT NULL DEFAULT 1.0,
        weight_integrity REAL NOT NULL DEFAULT 1.0,
        weight_availability REAL NOT NULL DEFAULT 1.0,
        purpose TEXT,
        data_categories TEXT NOT NULL DEFAULT '[]',
        role TEXT,
        pii_controls TEXT NOT NULL DEFAULT '[]',
        legal_basis TEXT,
        purpose_detail TEXT,
        collection_origin TEXT,
        collection_procedure TEXT,
        data_usage TEXT,
        retention_period TEXT,
        disposal_method TEXT,
        third_party_transfer INTEGER NOT NULL DEFAULT 0,
        national_transfers TEXT NOT NULL DEFAULT '[]',
        cross_border_flow INTEGER NOT NULL DEFAULT 0,
        international_flows TEXT NOT NULL DEFAULT '[]',
        times_compromised INTEGER DEFAULT 0,
        processes_affected TEXT,
        loss_range TEXT,
        relevance TEXT,
        created_by_id INTEGER NOT NULL DEFAULT 1,
        deleted_by_id INTEGER,
        updated_by_id INTEGER,
        process_id INTEGER,
        asset_value REAL DEFAULT 3.0,
        cid_method TEXT NOT NULL DEFAULT 'A',
        legacy_code TEXT
    );

    CREATE TABLE IF NOT EXISTS core_incident (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        is_deleted INTEGER NOT NULL DEFAULT 0,
        deleted_at TEXT,
        incident_code TEXT NOT NULL UNIQUE,
        rep_document_number TEXT,
        rep_document_expiry TEXT,
        rep_first_name TEXT,
        rep_last_name_p TEXT,
        rep_last_name_m TEXT,
        rep_position TEXT,
        rep_phone TEXT,
        rep_email TEXT,
        entity_type TEXT DEFAULT 'P',
        entity_ruc TEXT DEFAULT '20140798781',
        entity_name TEXT DEFAULT 'Universidad Nacional de San Agustín de Arequipa',
        entity_phone TEXT DEFAULT '054-282828',
        entity_extension TEXT DEFAULT '101',
        entity_department TEXT DEFAULT 'Arequipa',
        entity_province TEXT DEFAULT 'Arequipa',
        entity_district TEXT DEFAULT 'Arequipa',
        involves_personal_data INTEGER NOT NULL DEFAULT 1,
        incident_date TEXT NOT NULL,
        incident_time TEXT,
        detection_date TEXT,
        detection_time TEXT,
        incident_type TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'I',
        severity TEXT DEFAULT 'M',
        impact TEXT DEFAULT 'M',
        title TEXT NOT NULL,
        description TEXT,
        reported_by TEXT,
        assigned_to TEXT,
        affected_treatment TEXT,
        dpo_contact_name TEXT,
        dpo_contact_email TEXT,
        dpo_contact_phone TEXT,
        affected_data_types TEXT NOT NULL DEFAULT '[]',
        num_affected_subjects INTEGER DEFAULT 0,
        compromised_system TEXT,
        affected_url TEXT,
        evidence_refs TEXT,
        measure_updated_registry TEXT DEFAULT 'N',
        measure_new_security TEXT DEFAULT 'N',
        measure_improved_policies TEXT DEFAULT 'N',
        measure_considered_resolved TEXT DEFAULT 'N',
        measure_reported_authorities TEXT DEFAULT 'N',
        security_measures_adopted TEXT NOT NULL DEFAULT '{}',
        resolved_date TEXT,
        affected_cid TEXT NOT NULL DEFAULT '{}',
        created_by_id INTEGER NOT NULL DEFAULT 601,
        deleted_by_id INTEGER,
        updated_by_id INTEGER
    );

    CREATE TABLE IF NOT EXISTS core_incidentaction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_type TEXT NOT NULL,
        responsible TEXT,
        action_date TEXT,
        description TEXT NOT NULL,
        evidence TEXT,
        position INTEGER NOT NULL DEFAULT 1,
        incident_id INTEGER NOT NULL REFERENCES core_incident(id)
    );

    CREATE TABLE IF NOT EXISTS core_incidenthistory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        changed_at TEXT NOT NULL,
        actor TEXT,
        description TEXT NOT NULL,
        recipients_snapshot TEXT,
        changed_by_id INTEGER,
        incident_id INTEGER NOT NULL REFERENCES core_incident(id)
    );

    CREATE TABLE IF NOT EXISTS core_incidentattachment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file TEXT NOT NULL,
        file_name TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        incident_id INTEGER NOT NULL REFERENCES core_incident(id),
        uploaded_by_id INTEGER
    );

    CREATE TABLE IF NOT EXISTS core_incidentrecipient (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        label TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS core_securitylog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        action TEXT NOT NULL,
        module TEXT NOT NULL,
        object_type TEXT,
        object_id INTEGER,
        detail TEXT,
        ip_address TEXT,
        created_at TEXT NOT NULL,
        user_id INTEGER
    );

    CREATE TABLE IF NOT EXISTS core_auditfinding (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        classification TEXT NOT NULL,
        description TEXT NOT NULL,
        evidence TEXT,
        position INTEGER NOT NULL DEFAULT 1,
        audit_id INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS a6_system_config (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        org_name TEXT NOT NULL,
        org_ruc TEXT NOT NULL,
        legal_rep_name TEXT NOT NULL,
        dpo_user_id INTEGER,
        dpo_name TEXT NOT NULL,
        dpo_email TEXT NOT NULL,
        ciso_user_id INTEGER,
        uit_value_pen REAL NOT NULL DEFAULT 5150.0,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS a6_incident_ext (
        incident_id INTEGER PRIMARY KEY REFERENCES core_incident(id),
        involves_personal_data INTEGER NOT NULL DEFAULT 1,
        iso27701_control_id TEXT NOT NULL DEFAULT 'A.3.12',
        regla_codigo TEXT,
        asset_id INTEGER,
        source_finding_id INTEGER,
        consequences_summary TEXT,
        data_recovered_status TEXT NOT NULL DEFAULT 'NO_APLICA',
        data_recovered_detail TEXT,
        anpd_notified INTEGER NOT NULL DEFAULT 0,
        anpd_notified_at TEXT,
        anpd_official_ref TEXT,
        anpd_delay_justification TEXT,
        subjects_notified INTEGER NOT NULL DEFAULT 0,
        subjects_notified_at TEXT,
        subjects_notice_channel TEXT,
        multa_estimada_uit REAL DEFAULT 0.0,
        precedente_anpd TEXT,
        updated_at TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS a6_corrective_action (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id INTEGER UNIQUE REFERENCES core_incident(id),
        mc_code TEXT UNIQUE NOT NULL,
        nonconformity_desc TEXT,
        identified_on TEXT,
        identified_by_id INTEGER,
        identified_by_name TEXT,
        identified_signature TEXT,
        root_cause TEXT,
        similar_mc_ref TEXT,
        action_required INTEGER NOT NULL DEFAULT 1,
        action_to_implement TEXT,
        notify_who TEXT,
        approved_by_name TEXT,
        due_date TEXT,
        responsible_id INTEGER,
        responsible_name TEXT,
        implemented_on TEXT,
        implemented_signature TEXT,
        effectiveness_reviewed_on TEXT,
        effectiveness_signature TEXT,
        doc_changes_required TEXT,
        doc_changes_signature TEXT,
        status TEXT NOT NULL DEFAULT 'ABIERTA',
        source_type TEXT NOT NULL DEFAULT 'INCIDENTE',
        iso27701_control_id TEXT DEFAULT 'A.3.12',
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_core_incident_status ON core_incident(status);
    CREATE INDEX IF NOT EXISTS idx_core_incident_detdate ON core_incident(detection_date);
    CREATE INDEX IF NOT EXISTS idx_a6_ext_control ON a6_incident_ext(iso27701_control_id);
    CREATE INDEX IF NOT EXISTS idx_a6_mc_status ON a6_corrective_action(status);
    """)
    conn.commit()
    ensure_pims_migrations(conn)
    seed_pims_data(conn)


def ensure_pims_migrations(conn: sqlite3.Connection) -> None:
    """Agrega de forma idempotente columnas nuevas a tablas PIMS ya existentes."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(a6_corrective_action)").fetchall()}
    if not cols:
        return
    changed = False
    if "source_type" not in cols:
        conn.execute("ALTER TABLE a6_corrective_action ADD COLUMN source_type TEXT NOT NULL DEFAULT 'INCIDENTE'")
        changed = True
    if "iso27701_control_id" not in cols:
        conn.execute("ALTER TABLE a6_corrective_action ADD COLUMN iso27701_control_id TEXT DEFAULT 'A.3.12'")
        changed = True
    if changed:
        conn.commit()


def seed_pims_data(conn: sqlite3.Connection) -> None:
    """Puebla empleados (18), activos (10), destinatarios (6), incidentes 2023-2026 (15) y MC D34 (10) de manera idempotente."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM core_incident")
    if cur.fetchone()[0] > 0:
        return

    now = "2026-11-01 10:00:00"

    # 1. 18 Empleados UNSA (IDs 1..9 base + 601..609 Agente 6)
    users = [
        (1, "hrojas", "Hugo", "Rojas Flores", "rectorado@unsa.edu.pe", "Rectorado UNSA", "Rector (Representante Legal)", 1),
        (2, "lcarrera", "Luis", "Carrera Ramos", "vicerrectorado.acad@unsa.edu.pe", "Vicerrectorado Académico", "Vicerrector Académico", 0),
        (3, "mquispe", "Marisol", "Quispe Calla", "vri@unsa.edu.pe", "Vicerrectorado de Investigación", "Vicerrectora de Investigación", 0),
        (4, "rcaceres", "Roberto", "Cáceres Mamani", "secgeneral@unsa.edu.pe", "Secretaría General", "Secretario General", 0),
        (5, "acarpio", "Alberto", "Carpio Pinto", "ouaj@unsa.edu.pe", "Oficina Universitaria de Asesoría Jurídica", "Asesor Jurídico Principal", 0),
        (6, "jvaldivia_dua", "Juan", "Valdivia Valdivia", "dua@unsa.edu.pe", "Dirección Universitaria de Admisión", "Director de Admisión (DUA)", 0),
        (7, "csirt_ops", "Operador", "CSIRT UNSA", "csirt@unsa.edu.pe", "CSIRT Institucional UNSA", "Analista CSIRT", 1),
        (8, "lfuentes", "Rosa", "Fuentes Morales", "tramited@unsa.edu.pe", "Mesa de Partes / TRAMITED", "Jefa de Mesa de Partes", 0),
        (9, "ecornejo", "Elena", "Cornejo Valdivia", "calidad@unsa.edu.pe", "Oficina de Gestión de la Calidad", "Directora de Calidad", 0),
        (601, "cmendoza", "Carlos", "Mendoza Valdivia", "dpo@unsa.edu.pe", "Oficina de Protección de Datos Personales", "Oficial de Datos Personales (DPO)", 1),
        (602, "sparedes", "Sofía", "Paredes Huamán", "sparedes@unsa.edu.pe", "CSIRT / OTI UNSA", "Ingeniera de Seguridad Aplicativa", 0),
        (603, "dquispe", "Diego", "Quispe Condori", "dquispe@unsa.edu.pe", "Infraestructura y Plataformas OTI", "Especialista en Servicios Educativos", 0),
        (604, "mruiz", "Marcos", "Ruiz Benavente", "ciso@unsa.edu.pe", "Oficina de Tecnologías de la Información (OTI)", "Oficial de Seguridad y Confianza Digital (CISO)", 1),
        (605, "msoto", "Manuel", "Soto Paredes", "msoto@unsa.edu.pe", "Hospital Docente Zamácola UNSA", "Jefe de Sistemas Clínicos", 0),
        (606, "rvargas", "Rosa", "Vargas Apaza", "rvargas@unsa.edu.pe", "Soporte e Infraestructura OTI", "Administradora de Servidores Linux", 0),
        (607, "lfernandez", "Lucía", "Fernández Ticona", "lfernandez@unsa.edu.pe", "Cumplimiento y Atención ARCO", "Especialista Legal de Privacidad", 0),
        (608, "jvaldivia_tes", "Jorge", "Valdivia Choque", "jvaldivia.tes@unsa.edu.pe", "Tesorería Central UNSA", "Coordinador de Pagos Digitales", 0),
        (609, "pcornejo", "Pedro", "Cornejo Quispe", "pcornejo@unsa.edu.pe", "Base de Datos OTI", "Administrador de Base de Datos (DBA)", 0),
    ]
    for uid, uname, fn, ln, email, area, pos, is_admin in users:
        cur.execute("""
            INSERT INTO auth_user (id, password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)
            VALUES (?, '!unusable', ?, ?, ?, ?, ?, 1, 1, ?)
        """, (uid, is_admin, uname, fn, ln, email, now))
        cur.execute("""
            INSERT INTO core_userprofile (id, area, position, user_id, is_platform_admin, must_change_password)
            VALUES (?, ?, ?, ?, ?, 0)
        """, (uid, area, pos, uid, is_admin))

    # 2. Configuración institucional (a6_system_config)
    cur.execute("""
        INSERT INTO a6_system_config (id, org_name, org_ruc, legal_rep_name, dpo_user_id, dpo_name, dpo_email, ciso_user_id, uit_value_pen, updated_at)
        VALUES (1, 'Universidad Nacional de San Agustín de Arequipa', '20140798781', 'Dr. Hugo Rojas Flores', 601,
                'Abog. Carlos Mendoza Valdivia (DPO UNSA)', 'dpo@unsa.edu.pe', 604, ?, ?)
    """, (VALOR_UIT_PEN, now))

    # 3. 10 Activos Institucionales (core_asset)
    assets = [
        (101, "SYS-SISUNSA", "Servidor de Base de Datos SISUNSA (PostgreSQL)", "Base de datos relacional central de expedientes académicos, actas de notas y matrículas.", "Vicerrectorado Académico", "Ing. Pedro Cornejo Quispe (DBA OTI)", "Data Center Pabellón Central OTI", "DATABASE", "CONFIDENCIAL", "Ley Universitaria 30220 / Contrato de Matrícula", "Permanente alumno + 10 años", ["CIFRADO_REPOSO", "MFA_ADMIN", "BACKUP_INMUTABLE", "RBAC"], 1, 1),
        (102, "SYS-HOSPITAL", "Servidor de Historias Clínicas - Hospital Docente UNSA", "Historias clínicas, diagnósticos CIE-10 y tratamientos médicos.", "Hospital Docente Zamácola", "Ing. Manuel Soto Paredes", "Av. Aeropuerto N° 504, Zamácola", "DATABASE", "SECRETO", "Ley General de Salud 26842 / Ley 29733 Art. 13", "20 años (NTS 139-MINSA)", ["RBAC", "TRAZABILIDAD", "PGCRYPTO_AES256"], 0, 0),
        (103, "SYS-SISADMIS", "Portal Web SISADMISION y Banco de Postulantes", "Plataforma web con datos, fotos y biometría de postulantes.", "Dirección Universitaria de Admisión", "Ing. Sofía Paredes Huamán", "Servidores DMZ OTI (admision.unsa.edu.pe)", "APPLICATION", "CONFIDENCIAL", "Consentimiento / RCU N° 0085-2026", "1 año no ingresantes / Permanente ingresantes", ["WAF_FORTINET", "TLS_1_3", "HASH_ARGON2ID"], 0, 0),
        (104, "CLOUD-GSUITE", "Google Workspace for Education Fundamentals (@unsa.edu.pe)", "Correo institucional, Drive y Classroom.", "OTI UNSA", "Google LLC / OTI", "Centros de Datos Cloud (EE.UU. / UE)", "CLOUD_SERVICE", "CONFIDENCIAL", "Contrato Cloud / Ley 29733 Art. 15", "Vinculación + 180 días", ["DPA", "TLS", "MFA_OBLIGATORIO", "SCC"], 1, 1),
        (105, "APP-MOODLE", "Plataforma Aula Virtual Moodle UNSA", "LMS para evaluaciones y seguimiento académico.", "Vicerrectorado Académico", "Ing. Diego Quispe Condori", "Cluster Virtualizado OTI", "APPLICATION", "CONFIDENCIAL", "Contrato de Matrícula", "5 años", ["GOOGLE_OAUTH", "HTTPS", "BACKUP_DIARIO"], 0, 0),
        (106, "ARCH-SANAGUSTIN", "Archivo Central Físico y Digitalización San Agustín 115", "Actas de notas históricas, grados, títulos y legajos.", "Secretaría General", "Ing. Marcos Ruiz Benavente / Archivo Central", "Calle San Agustín N° 115, Arequipa", "PHYSICAL_ARCHIVE", "CONFIDENCIAL", "Ley Nacional de Archivos / Ley 30220", "Permanente / Histórico", ["ACCESO_BIOMETRICO", "CCTV_24_7"], 0, 0),
        (107, "APP-TRAMITED", "Sistema de Trámite Documentario Electrónico (TRAMITED)", "Recepción de expedientes CUT y solicitudes de derechos ARCO.", "Secretaría General", "Abog. Lucía Fernández Ticona / Mesa de Partes", "Servidores Web OTI (ouis.unsa.edu.pe/tramited/)", "APPLICATION", "CONFIDENCIAL", "Ley 27444 / Ley 29733", "10 años", ["FIRMA_RENIEC", "HTTPS", "FOLIO_INALTERABLE"], 0, 0),
        (108, "APP-UNSAPAY", "Pasarela de Recaudación UNSApay / Págalo.pe", "Recaudación de tasas de matrícula, certificados y servicios.", "Tesorería Central", "CPC Jorge Valdivia Choque", "pagalo.pe y servidores Tesorería", "APPLICATION", "CONFIDENCIAL", "Ley Sistema Nacional de Tesorería", "10 años (SUNAT)", ["TOKENIZACION", "TLS_1_3", "NO_STORAGE_CVV"], 1, 0),
        (109, "APP-SISTUTORIA", "Sistema de Tutoría y Acompañamiento Psicopedagógico", "Entrevistas psicopedagógicas y seguimiento tutores.", "Dirección Universitaria de Tutoría", "Abog. Lucía Fernández Ticona / DUDE", "extranet.unsa.edu.pe/sisacad", "APPLICATION", "SECRETO", "Ley Universitaria 30220 Art. 69", "Durante permanencia", ["ACCESO_ESTRICTO", "SOLO_TUTOR_ASIGNADO"], 0, 0),
        (110, "APP-SISCOM", "Sistema de Control de Comedor Universitario (DUDE)", "Becas alimentarias y fichas socioeconómicas estudiantiles.", "Dirección Universitaria de Desarrollo Estudiantil", "Abog. Carlos Mendoza Valdivia / DUDE", "Red interna comedores UNSA", "APPLICATION", "CONFIDENCIAL", "Estatuto UNSA / RCU N° 0340-2025", "3 años", ["RBAC", "HTTPS"], 0, 0),
    ]
    for aid, code, name, desc, owner, cust, loc, cat, cls, lb, ret, ctrls, tpt, cbf in assets:
        cur.execute("""
            INSERT INTO core_asset (
                id, created_at, updated_at, code, name, description, owner, custodians, location,
                category, classification, legal_basis, retention_period, pii_controls,
                third_party_transfer, cross_border_flow
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (aid, now, now, code, name, desc, owner, cust, loc, cat, cls, lb, ret, json.dumps(ctrls, ensure_ascii=False), tpt, cbf))

    # 4. 6 Destinatarios de notificación
    recipients = [
        (601, "dpo@unsa.edu.pe", "Oficial de Protección de Datos Personales (DPO UNSA)"),
        (602, "ciso@unsa.edu.pe", "Oficial de Seguridad y Confianza Digital (CISO / OTI)"),
        (603, "csirt@unsa.edu.pe", "Equipo de Respuesta a Incidentes Digitales (CSIRT UNSA)"),
        (604, "rectorado@unsa.edu.pe", "Despacho Rectoral UNSA (Representante Legal)"),
        (605, "ouaj@unsa.edu.pe", "Oficina Universitaria de Asesoría Jurídica (OUAJ)"),
        (606, "anpd.denuncias@minjus.gob.pe", "Dirección de Fiscalización e Instrucción - ANPD Perú (Auxiliar)"),
    ]
    for rid, email, label in recipients:
        cur.execute("""
            INSERT INTO core_incidentrecipient (id, email, label, is_active, created_at)
            VALUES (?, ?, ?, 1, ?)
        """, (rid, email, label, now))

    # 5. 15 Incidentes y Brechas UNSA (2023-2026)
    # Tupla: (id, code, title, desc, inc_date, inc_time, det_date, det_time, res_date, status, sev, imp, itype, pii,
    #         rep_by, assigned_to, asset_id, comp_sys, url, data_types, n_subj, ctrl, regla, mult_uit, prec,
    #         conseq, rec_status, rec_detail, anpd_not, anpd_at, anpd_ref, anpd_just, subj_not, subj_at, subj_chan)
    incidents = [
        # --- 2026 (601..607) ---
        (601, "INC-UNSA-2026-001",
         "Exfiltración de 3,420 historias clínicas electrónicas no cifradas en Hospital Docente UNSA",
         "Ataque de inyección SQL explotando endpoint asistencial del Hospital Docente de Zamácola. Los diagnósticos CIE-10 y tratamientos estaban en texto plano en PostgreSQL sin cifrado pgcrypto.",
         "2026-10-23", "03:15:00", "2026-10-24", "08:45:00", "2026-10-27", "C", "C", "C", "BF", 1,
         "CSIRT UNSA", "Ing. Manuel Soto Paredes", 102, "Servidor PostgreSQL srv-hosp-db (SYS-HOSPITAL, id=102)",
         "https://hospital.unsa.edu.pe/consulta_paciente.php", ["SALUD", "HISTORIA_CLINICA", "DIAGNOSTICOS_CIE10", "DNI"], 3420,
         "A.3.26", "R-001", 12.5, "R.D. 1045-2020-JUS (Clínica Montefiori)",
         "Exposición externa de diagnósticos CIE-10 de pacientes; vector cerrado y tablas migradas a pgcrypto AES-256.",
         "RECUPERADO_TOTAL", "Tabla restaurada sin pérdida de integridad desde respaldo verificado; credenciales rotadas.",
         1, "2026-10-25 10:15:00", "Oficio N° 0142-2026-R-UNSA", None, 1, "2026-10-26 14:00:00", "Correo electrónico y carta institucional"),

        (602, "INC-UNSA-2026-002",
         "Volcado y descifrado masivo de 18,500 credenciales de postulantes con hash MD5 en SISADMISION",
         "Publicación externa de volcado con 18,500 cuentas de postulantes almacenadas con hash MD5 heredado sin salt criptográfico.",
         "2026-10-25", "22:30:00", "2026-10-26", "09:00:00", "2026-10-29", "C", "A", "A", "BF", 1,
         "CSIRT UNSA", "Ing. Sofía Paredes Huamán", 103, "Portal Web SISADMISION (SYS-SISADMIS, id=103)",
         "https://admision.unsa.edu.pe/login", ["CREDENCIALES_ACCESO", "HASH_MD5_OBSOLETO", "DNI", "CORREO"], 18500,
         "A.3.23", "R-002", 8.0, "R.D. 018-2021-JUS/DGTAIPD (Medidas técnicas en autenticación)",
         "Compromiso de contraseñas legacy; migrado a Argon2id y reseteo forzado a los 18,500 postulantes.",
         "RECUPERADO_TOTAL", "Hashes MD5 invalidados; integridad de cuentas restablecida con Argon2id.",
         1, "2026-10-27 11:30:00", "Oficio N° 0158-2026-R-UNSA", None, 1, "2026-10-28 09:00:00", "Correo masivo institucional SMTP"),

        (603, "INC-UNSA-2026-003",
         "Retención indebida y exportación no autorizada de 850 tarjetas de crédito y CVV en Tesorería",
         "Auditoría interna descubrió almacenamiento de PAN y CVV tras pagos completados y exportación CSV no autorizada por operador de caja.",
         "2026-10-27", "14:20:00", "2026-10-28", "16:00:00", "2026-10-30", "C", "C", "C", "BF", 1,
         "Órgano de Control Institucional (OCI)", "CPC Jorge Valdivia Choque", 108, "Servidor de Pagos Tesorería (APP-UNSAPAY, id=108)",
         "https://pagos.unsa.edu.pe/checkout", ["TARJETAS_CREDITO_PAN", "CODIGO_SEGURIDAD_CVV", "FECHA_EXPIRACION"], 850,
         "A.1.4.5", "R-003", 15.0, "R.D. 089-2021-JUS/DGTAIPD (Retención indebida CVV)",
         "Riesgo de fraude financiero; columnas eliminadas por DROP COLUMN y migración a pasarela tokenizada Págalo.pe.",
         "RECUPERADO_TOTAL", "Soportes destruidos con borrado seguro y archivo CSV incautado en custodia fiscal.",
         1, "2026-10-29 12:00:00", "Oficio N° 0171-2026-R-UNSA", None, 1, "2026-10-29 17:30:00", "Comunicado directo a titulares"),

        (604, "INC-UNSA-2026-004",
         "Transferencia transfronteriza no autorizada de expedientes académicos de 25,000 alumnos a bucket Cloud",
         "Cronjob automatizado replicaba copias de SISUNSA hacia bucket AWS S3 eu-west-1 (Irlanda) sin contrato DPA/SCC ni inscripción de flujo transfronterizo.",
         "2026-10-28", "10:00:00", "2026-10-29", "11:30:00", None, "I", "C", "C", "BF", 1,
         "DPO / Inspector DSPM", "Ing. Pedro Cornejo Quispe", 101, "Data Center OTI / AWS S3 eu-west-1 (SYS-SISUNSA, id=101)",
         "https://s3.eu-west-1.amazonaws.com/unsa-backups-unencrypted", ["EXPEDIENTES_ACADEMICOS", "ACTAS_NOTAS", "DNI"], 25000,
         "A.1.5.2", "R-006", 11.0, "R.D. 125-2019-JUS (Flujo transfronterizo sin registro)",
         "Respaldos replicados fuera de jurisdicción nacional sin cláusulas tipo; pendiente completar purga en bucket europeo.",
         "RECUPERADO_PARCIAL", "Cronjob detenido y keys IAM revocadas; en trámite borrado certificado en región eu-west-1.",
         0, None, None, "Documentación técnica del proveedor AWS en acopio para expediente de notificación.", 0, None, None),

        (605, "INC-UNSA-2026-005",
         "Conservación indefinida sin política de purga de datos biométricos de 45,200 postulantes no ingresantes",
         "La DUA conserva huellas dactilares y fotografías faciales de postulantes no ingresantes 2018-2025 sin plazo de caducidad ni procedimiento de borrado.",
         "2026-10-29", "09:00:00", "2026-10-30", "15:00:00", None, "I", "M", "M", "PI", 1,
         "Auditoría Interna RAT", "Ing. Sofía Paredes Huamán", 103, "Sistema SISADMISION (SYS-SISADMIS, id=103)",
         "https://admision.unsa.edu.pe/historico", ["BIOMETRICO_HUELLA", "FOTOGRAFIA_FACIAL", "DNI"], 45200,
         "A.1.4.8", "R-005", 5.0, "R.D. 005-2016-JUS/DGPDP (Conservación indefinida)",
         "Acumulación excesiva de datos biométricos sin finalidad activa; pendiente aprobación de directiva de purga en Consejo.",
         "NO_APLICA", "Incidente de no conformidad por exceso de conservación (sin exfiltración externa).",
         0, None, None, None, 0, None, None),

        (606, "INC-UNSA-2026-006",
         "Exigencia de tasa administrativa (TUPA) de S/ 28.50 y carta notarial para atender derechos ARCO en TRAMITED",
         "Sistema TRAMITED y Mesa de Partes exigían pago de tasa de S/ 28.50 y carta notarial para solicitudes de cancelación y oposición de datos.",
         "2026-10-30", "11:15:00", "2026-10-31", "10:00:00", None, "I", "A", "M", "PI", 1,
         "Queja Ciudadana / Egresados", "Abog. Lucía Fernández Ticona", 107, "Sistema TRAMITED (APP-TRAMITED, id=107)",
         "https://ouis.unsa.edu.pe/tramited/", ["SOLICITUDES_ARCO", "DNI", "DOMICILIO"], 120,
         "A.1.3.7", "R-007", 9.0, "R.D. 022-2016-JUS/DGPDP (Gratuidad derechos ARCO)",
         "Obstaculización documental del ejercicio gratuito de derechos ARCO por 120 solicitantes.",
         "NO_APLICA", "No hubo pérdida ni acceso ilícito; en curso eliminación de validadores TUPA.",
         1, "2026-11-01 09:00:00", "EXP-2026-ARCO-0034", None, 1, "2026-11-01 12:00:00", "Portal de Transparencia UNSA"),

        (607, "INC-UNSA-2026-007",
         "Casilla pre-marcada obligatoria para cesión comercial de datos personales en ficha de matrícula y comedor",
         "Portales de matrícula y SISCOM incluían casilla pre-marcada obligatoria para ceder contactos a patrocinadores comerciales.",
         "2026-10-31", "16:45:00", "2026-11-01", "09:30:00", None, "E", "A", "M", "PI", 1,
         "Oficina de Gestión de la Calidad", "Abog. Carlos Mendoza Valdivia", 110, "Comedor SISCOM y Matrícula (APP-SISCOM, id=110)",
         "http://matricula.unsa.edu.pe/", ["DATOS_CONTACTO", "CORREO_PERSONAL", "CONDICION_SOCIOECONOMICA"], 22000,
         "A.1.2.4", "R-004", 10.0, "R.D. 2196-2020-JUS (BBVA - Consentimiento presunto)",
         "Captura de consentimiento inválido por imposición y pre-marcado; front-end corregido, en curso revocación de envíos a terceros.",
         "NO_APLICA", "En mitigación organizativa y depuración de listas enviadas.",
         0, None, None, None, 0, None, None),

        # --- 2023 (608..609) ---
        (608, "INC-UNSA-2023-001",
         "Fuga de credenciales OAuth de cuentas Google Workspace institucionales por phishing dirigido a docentes",
         "Campaña de suplantación capturó tokens OAuth de 145 cuentas docentes con acceso a Google Drive y actas preliminares de evaluación.",
         "2023-05-12", "18:10:00", "2023-05-14", "09:20:00", None, "I", "A", "A", "BF", 1,
         "Soporte OTI / Mesa de Ayuda", "Ing. Sofía Paredes Huamán", 104, "Google Workspace UNSA (CLOUD-GSUITE, id=104)",
         "https://mail.google.com/a/unsa.edu.pe", ["CORREO_INSTITUCIONAL", "TOKENS_OAUTH", "ACTAS_DOCENTES"], 145,
         "A.3.8", None, 7.5, "R.D. 018-2021-JUS/DGTAIPD (Gestión de identidades y accesos)",
         "Acceso temporal de terceros a bandejas docentes; sigue abierta la verificación de permisos OAuth de aplicaciones heredadas.",
         "RECUPERADO_PARCIAL", "Tokens revocados en Admin Console; resta auditar archivos compartidos externamente.",
         1, "2023-05-18 15:40:00", "Oficio N° 0312-2023-OTI-UNSA", "La consolidación de bitácoras de Google Workspace tomó 4 días hábiles por falta de SIEM centralizado en 2023.",
         1, "2023-05-19 10:00:00", "Comunicado interno a docentes afectados"),

        (609, "INC-UNSA-2023-002",
         "Alteración indebida de registros de asistencia en Aula Virtual Moodle por falta de devolución de accesos",
         "Ex-docente contratado conservó privilegios de editor en Moodle tras finalizar vínculo laboral y modificó registros académicos de 320 alumnos.",
         "2023-11-06", "20:00:00", "2023-11-08", "10:15:00", "2023-12-02", "C", "M", "M", "BI", 1,
         "Decanato de Ingeniería", "Ing. Diego Quispe Condori", 105, "Aula Virtual Moodle (APP-MOODLE, id=105)",
         "https://aulavirtual.unsa.edu.pe", ["REGISTROS_ASISTENCIA", "CALIFICACIONES", "CORREO_ESTUDIANTIL"], 320,
         "A.3.9", None, 4.0, "Jurisprudencia ANPD sobre revocación oportuna de accesos",
         "Alteración puntual de integridad en cursos virtuales; actas restauradas y vinculado el cese de RR.HH. con baja en Moodle.",
         "RECUPERADO_TOTAL", "Restauración íntegra ejecutada desde copia diaria del 2023-11-05.",
         0, None, None, "Incidente de integridad contenido sin afectación masiva externa.", 0, None, None),

        # --- 2024 (610..612) ---
        (610, "INC-UNSA-2024-001",
         "Exposición de 9,800 registros reales de alumnos en servidor de pruebas QA SISUNSA indexado",
         "Backup de producción SISUNSA fue restaurado sin enmascaramiento ni disociación en entorno de pruebas QA expuesto en subred accesible.",
         "2024-04-17", "11:05:00", "2024-04-19", "08:30:00", None, "E", "C", "C", "BF", 1,
         "Auditoría OTI", "Ing. Marcos Ruiz Benavente", 101, "Base de Datos SISUNSA QA (SYS-SISUNSA, id=101)",
         "https://qa-sisunsa.unsa.edu.pe", ["DNI", "NOTAS_ACADEMICAS", "DIRECCION", "TELEFONO"], 9800,
         "A.3.31", None, 12.0, "Art. 39.6 D.S. 003-2013-JUS (Prohibición de datos reales en pruebas)",
         "Datos reales de estudiantes expuestos en servidor de desarrollo; servidor QA apagado pero continúa migración a generador sintético.",
         "RECUPERADO_PARCIAL", "Instancia QA desmontada y caché de buscador depurada; pendiente cierre documental de script de anonimización.",
         1, "2024-04-23 16:20:00", "Oficio N° 0089-2024-DPO-UNSA", "Demora de 96 horas al requerirse validación forense de logs Apache para determinar alcance exacto.",
         0, None, None),

        (611, "INC-UNSA-2024-002",
         "Exposición de respaldo clínico sin cifrar en unidad compartida interna del Hospital Docente Zamácola",
         "Carpeta de red SMB de intercambio radiológico y reportes clínicos contenía exportaciones mensuales en texto claro accesibles sin cifrado ni ACL restrictiva.",
         "2024-09-01", "16:40:00", "2024-09-03", "09:10:00", None, "I", "C", "C", "BF", 1,
         "Jefatura Médica Zamácola", "Ing. Manuel Soto Paredes", 102, "Servidor Clínico Zamácola (SYS-HOSPITAL, id=102)",
         "\\\\srv-hosp-fs\\compartidos\\radiologia", ["SALUD", "RADIOGRAFIAS", "DIAGNOSTICO", "DNI"], 1940,
         "A.3.26", "R-001", 13.0, "R.D. 038-2022-JUS (Clínica Peruano Americana - Datos clínicos sin cifrado)",
         "Alta criticidad por tratarse de datos sensibles de salud accesibles en red interna sin cifrado.",
         "NO_RECUPERADO", "Permisos SMB restringidos de emergencia, pero aún no se acredita inventario completo de copias locales.",
         1, "2024-09-05 08:50:00", "Oficio N° 0210-2024-DPO-UNSA", None, 0, None, None),

        (612, "INC-UNSA-2024-003",
         "Caída eléctrica y corte de servicio por fallo de UPS en nodo secundario de Aula Virtual (Sin PII)",
         "Interrupción de 6 horas en nodo secundario de Moodle por agotamiento de baterías UPS durante mantenimiento eléctrico programado. Sin acceso no autorizado ni exposición de PII.",
         "2024-11-22", "02:15:00", "2024-11-22", "06:00:00", "2024-11-24", "C", "B", "B", "IT", 0,
         "Monitoreo Infraestructura OTI", "Ing. Rosa Vargas Apaza", 105, "Cluster Virtualizado Moodle (APP-MOODLE, id=105)",
         "https://aulavirtual.unsa.edu.pe", [], 0,
         "A.3.12", None, 0.0, "No aplica sanción PII — Incidente técnico operativo (B.3.12 NOTE 1)",
         "Solo indisponibilidad operativa temporal del aula virtual; verificación descartó afectación a datos personales.",
         "NO_APLICA", "No hubo pérdida ni corrupción de datos personales.",
         0, None, None, "B.3.12 NOTE 1: Evento descartado como brecha de PII tras triaje inicial.", 0, None, None),

        # --- 2025 (613..615) ---
        (613, "INC-UNSA-2025-001",
         "Fallo y pérdida parcial de copias de respaldo de actas digitalizadas en Archivo Central San Agustín",
         "Corrupción de arreglo RAID y falla en cinta de respaldo de expedientes digitalizados de grados 2010-2015 en San Agustín 115 sin prueba previa de restauración.",
         "2025-03-15", "19:00:00", "2025-03-17", "09:45:00", None, "E", "C", "C", "BD", 1,
         "Secretaría General / Archivo Central", "Ing. Marcos Ruiz Benavente", 106, "Archivo San Agustín 115 (ARCH-SANAGUSTIN, id=106)",
         "https://archivo.unsa.edu.pe", ["ACTAS_GRADOS", "CERTIFICADOS_ESTUDIOS", "DNI"], 6200,
         "A.3.24", None, 9.5, "D.S. 003-2013-JUS Art. 39.5 (Obligación de copias y restauración)",
         "Pérdida de disponibilidad digital temporal de 6,200 actas; en curso re-digitalización desde folios físicos originales.",
         "RECUPERADO_PARCIAL", "Recuperado el 72% desde réplica secundaria; el 28% restante se re-digitaliza desde legajos físicos intactos.",
         1, "2025-03-21 11:00:00", "Oficio N° 0064-2025-DPO-UNSA", "Diagnóstico de sectores dañados en cabinas de almacenamiento NAS requirió 90 horas.",
         0, None, None),

        (614, "INC-UNSA-2025-002",
         "Acceso indebido de perfiles no autorizados a informes psicopedagógicos de tutoría (SISACAD)",
         "Configuración permisiva en rol de coordinadores permitía visualizar notas confidenciales de sesiones psicopedagógicas de 580 estudiantes.",
         "2025-08-28", "14:00:00", "2025-08-29", "11:00:00", None, "I", "A", "A", "BF", 1,
         "Dirección Universitaria de Tutoría", "Abog. Lucía Fernández Ticona", 109, "Sistema Tutoría (APP-SISTUTORIA, id=109)",
         "https://extranet.unsa.edu.pe/sisacad", ["INFORME_PSICOPEDAGOGICO", "SALUD_MENTAL", "DNI"], 580,
         "A.3.9", None, 8.5, "Ley 29733 Art. 13.6 y Directiva R.D. 019-2013-JUS (Derechos de acceso)",
         "Exposición interna horizontal de informes sensibles; pendiente auditoría completa de descargas históricas.",
         "RECUPERADO_PARCIAL", "Matriz de permisos RBAC corregida en módulo de tutoría; en revisión bitácora de accesos 2024-2025.",
         0, None, None, "En evaluación de impacto para determinar procedencia de notificación formal.", 0, None, None),

        (615, "INC-UNSA-2025-003",
         "Degradación y falsas alertas de monitoreo por certificado TLS caducado en balanceador interno (Sin PII)",
         "Vencimiento de certificado TLS en balanceador interno de pruebas generó errores 502 durante 45 minutos en ventana nocturna sin fuga de información personal.",
         "2025-10-15", "01:10:00", "2025-10-15", "07:30:00", "2025-11-10", "C", "M", "B", "IT", 0,
         "NOC OTI UNSA", "Ing. Diego Quispe Condori", 101, "Balanceador Interno OTI / SISUNSA (SYS-SISUNSA, id=101)",
         "https://internal-lb.unsa.edu.pe", [], 0,
         "A.3.28", None, 0.0, "No aplica sanción PII — Incidente técnico de configuración (A.3.12 / B.3.12)",
         "Falla de disponibilidad menor en ventana nocturna; renovación automática ACME implementada.",
         "NO_APLICA", "Certificado renovado sin compromiso de PII.",
         0, None, None, "B.3.12 NOTE 1: Confirmado incidente técnico sin impacto sobre datos personales.", 0, None, None),
    ]

    for row in incidents:
        (
            iid, code, title, desc, inc_d, inc_t, det_d, det_t, res_d, st, sev, imp, itype, pii,
            rep_by, ass_to, aid, comp_sys, url, dtypes, nsubj, ctrl, regla, mult_uit, prec,
            conseq, rec_st, rec_det, anpd_n, anpd_at, anpd_ref, anpd_just, sub_n, sub_at, sub_ch
        ) = row
        cur.execute("""
            INSERT INTO core_incident (
                id, created_at, updated_at, incident_code,
                rep_document_number, rep_first_name, rep_last_name_p, rep_last_name_m, rep_position, rep_email,
                involves_personal_data, incident_date, incident_time, detection_date, detection_time,
                incident_type, status, severity, impact, title, description,
                reported_by, assigned_to, dpo_contact_name, dpo_contact_email,
                affected_data_types, num_affected_subjects, compromised_system, affected_url,
                measure_considered_resolved, measure_reported_authorities, resolved_date,
                affected_cid, created_by_id
            ) VALUES (?, ?, ?, ?, '29481230', 'Hugo', 'Rojas', 'Flores', 'Rector UNSA', 'rectorado@unsa.edu.pe',
                      ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Abog. Carlos Mendoza Valdivia (DPO UNSA)', 'dpo@unsa.edu.pe',
                      ?, ?, ?, ?, ?, ?, ?, ?, 601)
        """, (
            iid, f"{det_d} {det_t}", now, code, pii, inc_d, inc_t, det_d, det_t,
            itype, st, sev, imp, title, desc, rep_by, ass_to,
            json.dumps(dtypes, ensure_ascii=False), nsubj, comp_sys, url,
            "S" if st == "C" else "N", "S" if anpd_n else "N", res_d,
            json.dumps({"confidentiality": itype in ("BF", "PI"), "integrity": itype in ("BI", "PI"), "availability": itype in ("BD", "IT")})
        ))
        cur.execute("""
            INSERT INTO a6_incident_ext (
                incident_id, involves_personal_data, iso27701_control_id, regla_codigo, asset_id,
                consequences_summary, data_recovered_status, data_recovered_detail,
                anpd_notified, anpd_notified_at, anpd_official_ref, anpd_delay_justification,
                subjects_notified, subjects_notified_at, subjects_notice_channel,
                multa_estimada_uit, precedente_anpd, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            iid, pii, ctrl, regla, aid, conseq, rec_st, rec_det,
            anpd_n, anpd_at, anpd_ref, anpd_just, sub_n, sub_at, sub_ch, mult_uit, prec, now
        ))

    # 6. Acciones A.3.12 (core_incidentaction)
    actions = [
        (601, "C", "Ing. Manuel Soto Paredes", "2026-10-24", "Aislamiento de servidor srv-hosp-db y bloqueo de puerto 5432 en firewall.", "Log Fortinet FW-UNSA-01", 1, 601),
        (602, "R", "Ing. Pedro Cornejo Quispe", "2026-10-25", "Saneamiento SQL parametrizado y cifrado pgcrypto AES-256 en columna diagnostico.", "Commit 7f8a12e", 2, 601),
        (603, "M", "Abog. Carlos Mendoza Valdivia", "2026-10-27", "Emisión de Directiva de Custodia de Historias Clínicas según NTS 139-MINSA.", "Resolución Hospital N° 045-2026", 3, 601),
        (604, "C", "Ing. Marcos Ruiz Benavente", "2026-10-26", "Revocación masiva de sesiones y bloqueo de portal legacy.", "Bitácora nginx reload", 1, 602),
        (605, "R", "Ing. Sofía Paredes Huamán", "2026-10-28", "Migración de algoritmo de contraseñas a Argon2id e invalidación de MD5.", "Reporte Pentest Argon2id", 2, 602),
        (606, "C", "Ing. Pedro Cornejo Quispe", "2026-10-28", "Eliminación de columnas pan y cvv con borrado seguro.", "Certificado saneamiento DB", 1, 603),
        (607, "R", "CPC Jorge Valdivia Choque", "2026-10-30", "Integración exclusiva con pasarela tokenizada Págalo.pe sin almacenamiento local de tarjetas.", "Validación PCI-DSS 3.2", 2, 603),
        (608, "C", "Ing. Marcos Ruiz Benavente", "2026-10-29", "Detención del cronjob de sincronización y revocación de AWS Access Keys.", "AWS CloudTrail DeleteAccessKey", 1, 604),
        (609, "C", "Ing. Sofía Paredes Huamán", "2026-10-30", "Etiquetado lógico BLOCKED_PENDING_PURGE sobre postulantes no ingresantes 2018-2024.", "Script etiqueta SQL", 1, 605),
        (610, "C", "Abog. Lucía Fernández Ticona", "2026-10-31", "Publicación de Circular Rectoral N° 012-2026 declarando gratuidad irrestricta ARCO.", "Circular N° 012-2026", 1, 606),
        (611, "R", "Abog. Carlos Mendoza Valdivia", "2026-11-01", "Desmarcado automático (checked=false) de casillas de patrocinio comercial.", "PR #412 matricula.unsa.edu.pe", 1, 607),
        (612, "C", "Ing. Sofía Paredes Huamán", "2023-05-15", "Revocación de tokens OAuth sospechosos y activación obligatoria de MFA para docentes.", "Log Google Admin Workspace", 1, 608),
        (613, "R", "Ing. Diego Quispe Condori", "2023-11-15", "Restauración de actas desde respaldo del 2023-11-05 y desactivación de cuenta ex-docente.", "Acta de restauración Moodle", 1, 609),
        (614, "C", "Ing. Marcos Ruiz Benavente", "2024-04-20", "Apagado inmediato de instancia QA y bloqueo en firewall perimetral.", "Ticket CSIRT-2024-019", 1, 610),
        (615, "C", "Ing. Manuel Soto Paredes", "2024-09-04", "Cierre de recurso compartido SMB público y habilitación de ACL por servicio clínico.", "Captura GPO SMB", 1, 611),
        (616, "R", "Ing. Rosa Vargas Apaza", "2024-11-23", "Reemplazo de banco de baterías UPS y validación de recuperación sin afectación PII.", "Orden trabajo OTI-2024-118", 1, 612),
        (617, "C", "Ing. Marcos Ruiz Benavente", "2025-03-18", "Aislamiento de cabinas NAS degradadas e inicio de recuperación desde réplica.", "Reporte hardware NAS", 1, 613),
        (618, "C", "Abog. Lucía Fernández Ticona", "2025-08-30", "Corrección de roles RBAC en módulo SISACAD restringiendo fichas al tutor asignado.", "Commit fix-rbac-tutoria", 1, 614),
        (619, "R", "Ing. Diego Quispe Condori", "2025-10-16", "Renovación de certificado TLS y configuración de renovación automática.", "Log Certbot ACME", 1, 615),
    ]
    for row in actions:
        cur.execute("""
            INSERT INTO core_incidentaction (id, action_type, responsible, action_date, description, evidence, position, incident_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    # 7. Bitácora forense A.3.14 (core_incidenthistory)
    histories = [
        (601, "DETECCION", "2026-10-24 08:45:00", "CSIRT UNSA", "Detección de exfiltración SQLi en Hospital Docente (A.3.26).", "dpo@unsa.edu.pe, ciso@unsa.edu.pe", 7, 601),
        (602, "NOTIFICACION_ANPD", "2026-10-25 10:15:00", "Abog. Carlos Mendoza Valdivia", "Registro documental de notificación Oficio N° 0142-2026-R-UNSA.", "anpd.denuncias@minjus.gob.pe", 601, 601),
        (603, "CIERRE", "2026-10-27 17:00:00", "Abog. Carlos Mendoza Valdivia", "Cierre formal tras cifrado AES-256 pgcrypto.", "dpo@unsa.edu.pe, ciso@unsa.edu.pe", 601, 601),
        (604, "DETECCION", "2026-10-26 09:00:00", "CSIRT UNSA", "Detección de volcado de hashes MD5 (A.3.23).", "dpo@unsa.edu.pe, ciso@unsa.edu.pe", 7, 602),
        (605, "CIERRE", "2026-10-29 18:10:00", "Ing. Sofía Paredes Huamán", "Cierre validado con migración a Argon2id.", "dpo@unsa.edu.pe", 602, 602),
        (606, "DETECCION", "2026-10-28 16:00:00", "OCI UNSA", "Detección de retención ilegal CVV/PAN (A.1.4.5).", "dpo@unsa.edu.pe, rectorado@unsa.edu.pe", 7, 603),
        (607, "CIERRE", "2026-10-30 16:30:00", "CPC Jorge Valdivia Choque", "Cierre tras eliminación de columnas sensibles y migración a Págalo.pe.", "rectorado@unsa.edu.pe", 608, 603),
        (608, "DETECCION", "2026-10-29 11:30:00", "DPO UNSA", "Detección de flujo transfronterizo AWS Irlanda (A.1.5.2).", "dpo@unsa.edu.pe", 601, 604),
        (609, "DETECCION", "2026-10-30 15:00:00", "Auditoría RAT", "Identificación de retención biométrica indefinida (A.1.4.8).", "dpo@unsa.edu.pe", 601, 605),
        (610, "DETECCION", "2026-10-31 10:00:00", "Defensoría Universitaria", "Reclamo por tasa ARCO TUPA en TRAMITED (A.1.3.7).", "dpo@unsa.edu.pe", 607, 606),
        (611, "DETECCION", "2026-11-01 09:30:00", "Oficina de Calidad", "Casilla pre-marcada detectada en matrícula y comedor (A.1.2.4).", "dpo@unsa.edu.pe", 601, 607),
        (612, "DETECCION", "2023-05-14 09:20:00", "OTI UNSA", "Alerta de compromiso OAuth en cuentas docentes Google Workspace (A.3.20).", "ciso@unsa.edu.pe", 602, 608),
        (613, "CIERRE", "2023-12-02 15:00:00", "Ing. Diego Quispe Condori", "Cierre tras restauración Moodle y automatización de bajas de ex-docentes.", "ciso@unsa.edu.pe", 603, 609),
        (614, "DETECCION", "2024-04-19 08:30:00", "Auditoría OTI", "Detección de PII real de 9,800 alumnos en servidor QA (A.3.31).", "ciso@unsa.edu.pe, dpo@unsa.edu.pe", 604, 610),
        (615, "DETECCION", "2024-09-03 09:10:00", "Hospital Zamácola", "Hallazgo de carpeta compartida SMB con respaldos médicos sin cifrado (A.3.26).", "dpo@unsa.edu.pe", 605, 611),
        (616, "CIERRE", "2024-11-24 12:00:00", "Ing. Rosa Vargas Apaza", "Incidente técnico UPS cerrado; descartada afectación a PII.", "ciso@unsa.edu.pe", 606, 612),
        (617, "DETECCION", "2025-03-17 09:45:00", "Archivo Central", "Falla RAID sin prueba previa de restauración de actas (A.3.24).", "ciso@unsa.edu.pe", 604, 613),
        (618, "DETECCION", "2025-08-29 11:00:00", "Dirección de Tutoría", "Exposición de perfiles en informes psicopedagógicos (A.3.7).", "dpo@unsa.edu.pe", 607, 614),
        (619, "CIERRE", "2025-11-10 10:00:00", "Ing. Diego Quispe Condori", "Incidente técnico TLS cerrado tras automatizar renovación.", "ciso@unsa.edu.pe", 603, 615),
    ]
    for row in histories:
        cur.execute("""
            INSERT INTO core_incidenthistory (id, event_type, changed_at, actor, description, recipients_snapshot, changed_by_id, incident_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    # 8. Adjuntos de evidencia (16 archivos reales en media/evidencias/)
    attachments = [
        (601, "evidencias/reporte_forense_hospital_zamacola_601.pdf", "reporte_forense_hospital_zamacola_601.pdf", "2026-10-24 14:00:00", 601, 605),
        (602, "evidencias/oficio_anpd_notificacion_brecha_salud_601.pdf", "oficio_anpd_notificacion_brecha_salud_601.pdf", "2026-10-25 10:20:00", 601, 601),
        (603, "evidencias/analisis_rainbow_hashes_md5_admision_602.pdf", "analisis_rainbow_hashes_md5_admision_602.pdf", "2026-10-26 12:00:00", 602, 602),
        (604, "evidencias/oficio_anpd_notificacion_credenciales_602.pdf", "oficio_anpd_notificacion_credenciales_602.pdf", "2026-10-27 11:45:00", 602, 601),
        (605, "evidencias/acta_constatacion_oci_cvv_tesoreria_603.pdf", "acta_constatacion_oci_cvv_tesoreria_603.pdf", "2026-10-28 17:10:00", 603, 608),
        (606, "evidencias/denuncia_penal_revelacion_cvv_fiscalia_603.pdf", "denuncia_penal_revelacion_cvv_fiscalia_603.pdf", "2026-10-29 15:00:00", 603, 5),
        (607, "evidencias/informe_tecnico_flujo_transfronterizo_cloud_604.pdf", "informe_tecnico_flujo_transfronterizo_cloud_604.pdf", "2026-10-29 18:00:00", 604, 609),
        (608, "evidencias/informe_auditoria_rat_retencion_postulantes_605.pdf", "informe_auditoria_rat_retencion_postulantes_605.pdf", "2026-10-30 16:30:00", 605, 602),
        (609, "evidencias/circular_rectoral_gratuidad_derechos_arco_606.pdf", "circular_rectoral_gratuidad_derechos_arco_606.pdf", "2026-10-31 15:20:00", 606, 607),
        (610, "evidencias/inspeccion_dom_consentimiento_presunto_matricula_607.pdf", "inspeccion_dom_consentimiento_presunto_matricula_607.pdf", "2026-11-01 11:00:00", 607, 601),
        (611, "evidencias/reporte_oauth_token_leak_2023_608.pdf", "reporte_oauth_token_leak_2023_608.pdf", "2023-05-15 16:00:00", 608, 602),
        (612, "evidencias/acta_incidente_moodle_2023_609.pdf", "acta_incidente_moodle_2023_609.pdf", "2023-11-09 10:00:00", 609, 603),
        (613, "evidencias/informe_qa_pii_pruebas_2024_610.pdf", "informe_qa_pii_pruebas_2024_610.pdf", "2024-04-20 09:30:00", 610, 604),
        (614, "evidencias/alerta_respaldo_clinico_2024_611.pdf", "alerta_respaldo_clinico_2024_611.pdf", "2024-09-03 14:20:00", 611, 605),
        (615, "evidencias/informe_backup_archivo_2025_613.pdf", "informe_backup_archivo_2025_613.pdf", "2025-03-18 11:15:00", 613, 604),
        (616, "evidencias/reporte_acceso_tutoria_2025_614.pdf", "reporte_acceso_tutoria_2025_614.pdf", "2025-08-30 13:00:00", 614, 607),
    ]
    for row in attachments:
        cur.execute("""
            INSERT INTO core_incidentattachment (id, file, file_name, uploaded_at, incident_id, uploaded_by_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, row)

    # 9. Security Logs disparadores (object_id = asset_id)
    sec_logs = [
        (601, "anon_attacker", "SQL_INJECTION", "Hospital_Docente_Zamacola", "core_asset", 102, json.dumps({"endpoint": "/consulta_paciente.php", "rows": 3420}), "190.119.180.55", "2026-10-23 03:15:00", 7),
        (602, "crawler_bot_adm", "BULK_DUMP", "Modulo_Admision_Postulantes", "core_asset", 103, json.dumps({"table": "usuarios_postulantes", "rows": 18500}), "200.48.75.12", "2026-10-25 22:30:00", 7),
        (603, "operador_caja_03", "CARD_EXPORT", "Tesoreria_UNSApay", "core_asset", 108, json.dumps({"contains_cvv": True, "rows": 850}), "172.16.20.45", "2026-10-27 14:20:00", 7),
        (604, "cron_backup_sync", "CROSS_BORDER_SYNC", "Infraestructura_Cloud_OTI", "core_asset", 101, json.dumps({"region": "eu-west-1", "rows": 25000}), "52.218.40.10", "2026-10-28 10:00:00", 7),
        (605, "web_inspector", "UNCONSENTED_SHARING", "Direccion_Desarrollo_DUDE", "core_asset", 110, json.dumps({"checkbox_prechecked": True}), "10.0.12.30", "2026-10-31 16:45:00", 7),
        (606, "oauth_sentinel", "TOKEN_COMPROMISE", "Cloud_Workspace_OTI", "core_asset", 104, json.dumps({"accounts": 145, "phishing": True}), "181.65.12.40", "2023-05-12 18:10:00", 602),
        (607, "audit_qa_scanner", "PII_IN_QA_ENV", "SISUNSA_QA_Staging", "core_asset", 101, json.dumps({"students_exposed": 9800}), "10.0.4.88", "2024-04-17 11:05:00", 604),
        (608, "nas_monitor", "RAID_DEGRADATION", "Archivo_San_Agustin", "core_asset", 106, json.dumps({"unreadable_sectors": 412}), "10.0.9.15", "2025-03-15 19:00:00", 604),
    ]
    for row in sec_logs:
        cur.execute("""
            INSERT INTO core_securitylog (id, username, action, module, object_type, object_id, detail, ip_address, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    # 10. 10 Formularios de Medidas Correctivas D34 (Clause 10.2 / a6_corrective_action)
    mc_rows = [
        (1, 601, "MC-UNSA-2026-001", "Historias clínicas CIE-10 almacenadas en texto plano sin cifrado AES-256 ni consultas parametrizadas (A.3.26).",
         "2026-10-24", 7, "Equipo CSIRT UNSA", "CSIRT-UNSA / Firmado",
         "Ausencia de módulo criptográfico en PostgreSQL hospitalario y uso de SQL concatenado en PHP legacy.",
         "MC-UNSA-2024-002", 1,
         "Habilitar extensión pgcrypto con AES-256, refactorizar consultas a PDO preparado y segregar VLAN médica.",
         "Director Médico Zamácola, CISO OTI, DPO UNSA", "Abog. Carlos Mendoza Valdivia (DPO)", "2026-10-28",
         605, "Ing. Manuel Soto Paredes", "2026-10-26", "Ing. Manuel Soto / Firmado",
         "2026-10-27", "Abog. Carlos Mendoza (DPO) / Verificado", "Manual de Procedimientos Hospital Docente Zamácola v2.1", "Abog. Carlos Mendoza", "VERIFICADA"),

        (2, 602, "MC-UNSA-2026-002", "Almacenamiento de contraseñas de postulantes SISADMISION mediante MD5 sin salt (A.3.23).",
         "2026-10-26", 7, "Equipo CSIRT UNSA", "CSIRT-UNSA / Firmado",
         "Módulo de autenticación heredado de 2016 sin actualización a funciones de derivación resistentes.",
         None, 1,
         "Migrar autenticación a Argon2id con salt de 128 bits y forzar renovación de credenciales a los 18,500 postulantes.",
         "Director DUA, CISO OTI, DPO UNSA", "Abog. Carlos Mendoza Valdivia (DPO)", "2026-10-30",
         602, "Ing. Sofía Paredes Huamán", "2026-10-28", "Ing. Sofía Paredes / Firmado",
         "2026-10-29", "Ing. Marcos Ruiz (CISO) / Verificado", "Política Institucional de Contraseñas y Autenticación UNSA", "Ing. Marcos Ruiz", "VERIFICADA"),

        (3, 603, "MC-UNSA-2026-003", "Retención de PAN y código CVV en base de datos de Tesorería con exportación CSV habilitada (A.1.4.5).",
         "2026-10-28", 601, "Órgano de Control Institucional (OCI)", "Jefatura OCI / Firmado",
         "Diseño deficiente del módulo de pagos local y privilegio de exportación CSV sin aprobación.",
         None, 1,
         "Eliminar columnas pan y cvv, aplicar borrado seguro y delegar cobro íntegramente a pasarela Págalo.pe.",
         "Dirección General de Administración, Tesorería, DPO, OUAJ", "Dr. Hugo Rojas Flores (Rector)", "2026-10-31",
         608, "CPC Jorge Valdivia Choque", "2026-10-30", "CPC Jorge Valdivia / Firmado",
         "2026-10-30", "Abog. Carlos Mendoza (DPO) / Verificado", "Convenio Pasarela Pagos y Manual de Tesorería", "CPC Jorge Valdivia", "VERIFICADA"),

        (4, 604, "MC-UNSA-2026-004", "Replicación automática de respaldos SISUNSA hacia AWS eu-west-1 sin DPA/SCC ni inscripción de flujo (A.1.5.2).",
         "2026-10-29", 601, "Abog. Carlos Mendoza Valdivia (DPO)", "DPO UNSA / Firmado",
         "Script de respaldo configurado en OTI sin evaluación previa de transferencias internacionales por el DPO.",
         None, 1,
         "Detener cronjob hacia región europea, firmar Addendum DPA con cláusulas tipo SCC y migrar respaldos a bóveda nacional aprobada.",
         "Jefatura OTI, Asesoría Jurídica OUAJ, DPO", "Abog. Carlos Mendoza Valdivia (DPO)", "2026-11-15",
         609, "Ing. Pedro Cornejo Quispe", None, None,
         None, None, "Procedimiento de Acreditación de Proveedores Cloud OTI", None, "EN_PROGRESO"),

        (5, 605, "MC-UNSA-2026-005", "Conservación indefinida de huellas dactilares y fotos biométricas de postulantes no ingresantes (A.1.4.8).",
         "2026-10-30", 601, "Auditoría Interna RAT", "DPO UNSA / Firmado",
         "Reglamento de Admisión omite plazo de caducidad documental y rutina automática de purga.",
         None, 1,
         "Aprobar directiva de caducidad a 12 meses para no ingresantes e implementar rutina mensual de borrado seguro NIST SP 800-88.",
         "Director DUA, Secretaría General, DPO", "Abog. Carlos Mendoza Valdivia (DPO)", "2026-11-30",
         602, "Ing. Sofía Paredes Huamán", None, None,
         None, None, "Reglamento General de Admisión Pregrado (Cláusula de Retención)", None, "ABIERTA"),

        (6, 606, "MC-UNSA-2026-006", "Cobro de tasa administrativa de S/ 28.50 y exigencia de carta notarial para derechos ARCO en TRAMITED (A.1.3.7).",
         "2026-10-31", 607, "Abog. Lucía Fernández Ticona", "DPO / Legal / Firmado",
         "Desactualización del TUPA respecto a gratuidad obligatoria de derechos ARCO según Ley 29733.",
         None, 1,
         "Suprimir campos obligatorios de pago y carta notarial en TRAMITED; emitir circular y modificar procedimiento TUPA.",
         "Secretaría General, Mesa de Partes, Desarrollo OTI", "Dr. Hugo Rojas Flores (Rector)", "2026-11-10",
         607, "Abog. Lucía Fernández Ticona", "2026-11-01", "Abog. Lucía Fernández / Firmado",
         None, None, "TUPA Institucional UNSA — Procedimiento ARCO gratuito", None, "IMPLEMENTADA"),

        (7, 607, "MC-UNSA-2026-007", "Checkbox pre-marcado obligatorio para cesión comercial de datos estudiantiles en matrícula/SISCOM (A.1.2.4).",
         "2026-11-01", 9, "Mg. Elena Cornejo Valdivia (Calidad)", "Dirección Calidad / Firmado",
         "Falta de revisión de privacidad desde el diseño en formularios web estudiantiles.",
         None, 1,
         "Desmarcar casillas opcionales por defecto en portales y publicar política de privacidad con finalidades diferenciadas.",
         "DUDE, OTI Desarrollo, Oficina de Calidad, DPO", "Abog. Carlos Mendoza Valdivia (DPO)", "2026-11-12",
         601, "Abog. Carlos Mendoza Valdivia", None, None,
         None, None, "Reglamento de Comedor SISCOM y Manual de Matrícula", None, "EN_PROGRESO"),

        (8, 608, "MC-UNSA-2023-001", "Compromiso de 145 cuentas docentes en Google Workspace por ausencia de MFA y permisos OAuth abiertos (A.3.20).",
         "2023-05-14", 602, "Ing. Sofía Paredes Huamán", "CSIRT UNSA",
         "Falta de verificación multifactor obligatoria y lista blanca de aplicaciones OAuth de terceros.",
         None, 1,
         "Habilitar 2FA obligatorio para plana docente, restringir catálogo OAuth aprobado y auditar archivos Drive compartidos.",
         "Vicerrectorado Académico, CISO OTI, Decanatos", "Ing. Marcos Ruiz Benavente (CISO)", "2023-06-30",
         602, "Ing. Sofía Paredes Huamán", None, None,
         None, None, "Directiva de Correo Institucional y Servicios Nube OTI", None, "EN_PROGRESO"),

        (9, 610, "MC-UNSA-2024-001", "Uso de datos personales reales de 9,800 alumnos en servidor de pruebas QA expuesto (A.3.31).",
         "2024-04-19", 604, "Ing. Marcos Ruiz Benavente (CISO)", "CISO OTI",
         "Inexistencia de script de enmascaramiento antes de clonar base de datos de producción hacia QA.",
         None, 1,
         "Implementar pipeline automatizado de anonimización/datos sintéticos antes de cualquier despliegue en QA y aislar red de pruebas.",
         "DBA OTI, Equipo Desarrollo, DPO", "Ing. Marcos Ruiz Benavente (CISO)", "2024-05-31",
         604, "Ing. Marcos Ruiz Benavente", None, None,
         None, None, "Lineamiento de Ambientes de Desarrollo y Pruebas OTI", None, "ABIERTA"),

        (10, 613, "MC-UNSA-2025-001", "Pérdida parcial en arreglo de copias de respaldo de Archivo Central sin pruebas periódicas de restauración (A.3.24).",
         "2025-03-17", 4, "Secretaría General UNSA", "Secretario General",
         "Ausencia de cronograma trimestral de verificación de integridad y restauración de backups documentales.",
         None, 1,
         "Desplegar estrategia de respaldo 3-2-1 inmutable con verificación automática checksum SHA-256 y simulacro trimestral de restauración.",
         "Archivo Central, OTI Servidores, CISO, DPO", "Ing. Marcos Ruiz Benavente (CISO)", "2025-05-15",
         604, "Ing. Marcos Ruiz Benavente", None, None,
         None, None, "Plan de Respaldo, Continuidad y Restauración de Actas Digitales", None, "EN_PROGRESO"),
    ]
    for row in mc_rows:
        cur.execute("""
            INSERT INTO a6_corrective_action (
                id, incident_id, mc_code, nonconformity_desc, identified_on, identified_by_id,
                identified_by_name, identified_signature, root_cause, similar_mc_ref, action_required,
                action_to_implement, notify_who, approved_by_name, due_date, responsible_id,
                responsible_name, implemented_on, implemented_signature, effectiveness_reviewed_on,
                effectiveness_signature, doc_changes_required, doc_changes_signature, status,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (*row, now, now))

    conn.commit()
