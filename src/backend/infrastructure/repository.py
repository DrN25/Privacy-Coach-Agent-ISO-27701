"""
Patrón Repositorio Unificado (Repository Pattern).
Encapsula el acceso a la base de datos institucional de la UNSA (PostgreSQL unsa_pims_db, esquema demo)
y proporciona fallback transparente a SQLite/memoria local para pruebas offline.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from .db import (
    get_db_connection,
    get_postgres_connection,
    get_sqlite_connection,
    check_postgres_alive,
    RealDictCursor,
    PSYCOPG2_AVAILABLE
)

logger = logging.getLogger("pims.repository")

# Datos canónicos de contingencia institucional (Incidentes UNSA 601 al 607)
FALLBACK_INCIDENTES_UNSA = [
    {
        "id": 601,
        "incident_code": "INC-UNSA-2026-001",
        "title": "Exfiltración de 3,420 historias clínicas electrónicas no cifradas en Hospital Docente UNSA",
        "severity": "C",
        "impact": "C",
        "status": "C",
        "incident_type": "BF",
        "num_affected_subjects": 3420,
        "compromised_system": "Servidor PostgreSQL srv-hosp-db (SYS-HOSPITAL, id=102)",
        "affected_url": "https://hospital.unsa.edu.pe/consulta_paciente.php",
        "affected_data_types": ["SALUD", "HISTORIA_CLINICA", "DIAGNOSTICOS_CIE10", "DNI", "TRATAMIENTO"],
        "dpo_contact_name": "Abog. Carlos Mendoza Valdivia (DPO UNSA)",
        "dpo_contact_email": "dpo@unsa.edu.pe",
        "multa_estimada_uit": 12.5,
        "multa_estimada_pen": 64375.0,
        "precedente_anpd": "Resolución Directoral N° 1045-2020-JUS / R.D. 89-2021-JUS (Clínica Montefiori)",
        "regla_codigo": "R-001",
        "detection_date": "2026-10-24",
        "detection_time": "08:45:00"
    },
    {
        "id": 602,
        "incident_code": "INC-UNSA-2026-002",
        "title": "Volcado y descifrado masivo de 18,500 credenciales de postulantes con hash MD5 en SISADMISION",
        "severity": "A",
        "impact": "A",
        "status": "C",
        "incident_type": "BF",
        "num_affected_subjects": 18500,
        "compromised_system": "Portal Web SISADMISION (SYS-SISADMIS, id=103)",
        "affected_url": "https://admision.unsa.edu.pe/login",
        "affected_data_types": ["CREDENCIALES_ACCESO", "HASH_MD5_OBSOLETO", "DNI", "CORREO"],
        "dpo_contact_name": "Abog. Carlos Mendoza Valdivia (DPO UNSA)",
        "dpo_contact_email": "dpo@unsa.edu.pe",
        "multa_estimada_uit": 8.8,
        "multa_estimada_pen": 45320.0,
        "precedente_anpd": "Resolución Directoral N° 018-2021-JUS/DGTAIPD (Medidas técnicas en autenticación)",
        "regla_codigo": "R-002",
        "detection_date": "2026-10-26",
        "detection_time": "09:00:00"
    },
    {
        "id": 603,
        "incident_code": "INC-UNSA-2026-003",
        "title": "Retención indebida y exportación no autorizada de 850 tarjetas de crédito y CVV en Tesorería",
        "severity": "C",
        "impact": "C",
        "status": "C",
        "incident_type": "BF",
        "num_affected_subjects": 850,
        "compromised_system": "Servidor de Pagos Tesorería (APP-UNSAPAY, id=108)",
        "affected_url": "https://pagos.unsa.edu.pe/checkout",
        "affected_data_types": ["TARJETAS_CREDITO_PAN", "CODIGO_SEGURIDAD_CVV", "FECHA_EXPIRACION", "MONTO"],
        "dpo_contact_name": "Abog. Carlos Mendoza Valdivia (DPO UNSA)",
        "dpo_contact_email": "dpo@unsa.edu.pe",
        "multa_estimada_uit": 15.0,
        "multa_estimada_pen": 77250.0,
        "precedente_anpd": "Resolución Directoral N° 089-2021-JUS/DGTAIPD / R.D. 1169-2020-JUS (BCP)",
        "regla_codigo": "R-003",
        "detection_date": "2026-10-28",
        "detection_time": "16:00:00"
    },
    {
        "id": 604,
        "incident_code": "INC-UNSA-2026-004",
        "title": "Transferencia transfronteriza no autorizada de expedientes académicos de 25,000 alumnos a bucket Cloud",
        "severity": "A",
        "impact": "A",
        "status": "I",
        "incident_type": "BF",
        "num_affected_subjects": 25000,
        "compromised_system": "Data Center OTI / AWS S3 Bucket eu-west-1 (SYS-SISUNSA, id=101)",
        "affected_url": "https://s3.eu-west-1.amazonaws.com/unsa-backups-unencrypted",
        "affected_data_types": ["EXPEDIENTES_ACADEMICOS", "ACTAS_NOTAS", "DNI", "DOMICILIO"],
        "dpo_contact_name": "Abog. Carlos Mendoza Valdivia (DPO UNSA)",
        "dpo_contact_email": "dpo@unsa.edu.pe",
        "multa_estimada_uit": 11.0,
        "multa_estimada_pen": 56650.0,
        "precedente_anpd": "Resolución Directoral N° 125-2019-JUS (Flujo transfronterizo sin RNPDP)",
        "regla_codigo": "R-006",
        "detection_date": "2026-10-29",
        "detection_time": "11:30:00"
    },
    {
        "id": 605,
        "incident_code": "INC-UNSA-2026-005",
        "title": "Conservación indefinida sin política de purga de datos biométricos de 45,200 postulantes no ingresantes",
        "severity": "M",
        "impact": "M",
        "status": "I",
        "incident_type": "PI",
        "num_affected_subjects": 45200,
        "compromised_system": "Sistema SISADMISION (SYS-SISADMIS, id=103)",
        "affected_url": "https://admision.unsa.edu.pe/historico",
        "affected_data_types": ["BIOMETRICO_HUELLA", "FOTOGRAFIA_FACIAL", "DNI", "COLEGIO"],
        "dpo_contact_name": "Abog. Carlos Mendoza Valdivia (DPO UNSA)",
        "dpo_contact_email": "dpo@unsa.edu.pe",
        "multa_estimada_uit": 5.0,
        "multa_estimada_pen": 25750.0,
        "precedente_anpd": "Resolución Directoral N° 005-2016-JUS/DGPDP (Conservación y caducidad de datos)",
        "regla_codigo": "R-005",
        "detection_date": "2026-10-30",
        "detection_time": "15:00:00"
    },
    {
        "id": 606,
        "incident_code": "INC-UNSA-2026-006",
        "title": "Exigencia de tasa administrativa (TUPA) de S/ 28.50 y carta notarial para atender derechos ARCO en TRAMITED",
        "severity": "A",
        "impact": "M",
        "status": "I",
        "incident_type": "PI",
        "num_affected_subjects": 120,
        "compromised_system": "Sistema de Trámite Documentario (APP-TRAMITED, id=107)",
        "affected_url": "https://ouis.unsa.edu.pe/tramited/",
        "affected_data_types": ["SOLICITUDES_ARCO", "DNI", "DOMICILIO", "EXPEDIENTES_CUT"],
        "dpo_contact_name": "Abog. Carlos Mendoza Valdivia (DPO UNSA)",
        "dpo_contact_email": "dpo@unsa.edu.pe",
        "multa_estimada_uit": 9.0,
        "multa_estimada_pen": 46350.0,
        "precedente_anpd": "Resolución Directoral N° 022-2016-JUS/DGPDP (Gratuidad irrestricta de derechos ARCO)",
        "regla_codigo": "R-007",
        "detection_date": "2026-10-31",
        "detection_time": "10:00:00"
    },
    {
        "id": 607,
        "incident_code": "INC-UNSA-2026-007",
        "title": "Casilla pre-marcada obligatoria para cesión comercial de datos personales en ficha de matrícula y comedor",
        "severity": "A",
        "impact": "M",
        "status": "I",
        "incident_type": "PI",
        "num_affected_subjects": 22000,
        "compromised_system": "Portal de Matrícula y Comedor (SYS-SISUNSA id=101 / APP-SISCOM id=110)",
        "affected_url": "http://matricula.unsa.edu.pe/",
        "affected_data_types": ["DATOS_CONTACTO", "CORREO_PERSONAL", "TELEFONO", "CONDICION_SOCIOECONOMICA"],
        "dpo_contact_name": "Abog. Carlos Mendoza Valdivia (DPO UNSA)",
        "dpo_contact_email": "dpo@unsa.edu.pe",
        "multa_estimada_uit": 10.0,
        "multa_estimada_pen": 51500.0,
        "precedente_anpd": "Resolución Directoral N° 018-2021-JUS / R.D. 2196-2020-JUS (BBVA - Consentimiento tácito)",
        "regla_codigo": "R-004",
        "detection_date": "2026-11-01",
        "detection_time": "09:30:00"
    }
]


class AuditRepository:
    def __init__(self, connection_factory=get_db_connection):
        self.get_conn = connection_factory

    # =========================================================================
    # 1. CONSULTAS INSTITUCIONALES DE INCIDENTES Y BRECHAS (demo.core_incident)
    # =========================================================================

    def listar_incidentes_unsa(self) -> List[Dict[str, Any]]:
        """Retorna las brechas e incidentes registrados en PostgreSQL o fallback."""
        if check_postgres_alive():
            try:
                conn = get_postgres_connection()
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, incident_code, title, severity, impact, status,
                               incident_type, num_affected_subjects, compromised_system,
                               affected_url, affected_data_types, dpo_contact_name,
                               dpo_contact_email, detection_date, detection_time,
                               created_at, updated_at
                        FROM demo.core_incident
                        ORDER BY id ASC;
                    """)
                    rows = cur.fetchall()
                    incidentes = []
                    for r in rows:
                        d = dict(r)
                        # Cálculo pericial directo si no está en columnas
                        # Mapeo de multa según id
                        f_match = next((f for f in FALLBACK_INCIDENTES_UNSA if f["id"] == d["id"]), None)
                        d["multa_estimada_uit"] = f_match["multa_estimada_uit"] if f_match else 5.0
                        d["multa_estimada_pen"] = f_match["multa_estimada_pen"] if f_match else 25750.0
                        d["precedente_anpd"] = f_match["precedente_anpd"] if f_match else "Precedente ANPD"
                        d["regla_codigo"] = f_match["regla_codigo"] if f_match else "R-001"
                        incidentes.append(d)
                conn.close()
                return incidentes
            except Exception as e:
                logger.error(f"Error consultando demo.core_incident en PostgreSQL: {e}")
        
        # Fallback de contingencia institucional
        return FALLBACK_INCIDENTES_UNSA

    def obtener_incidente_unsa(self, incident_id: int) -> Optional[Dict[str, Any]]:
        """Retorna el detalle completo de un incidente de brecha."""
        incidentes = self.listar_incidentes_unsa()
        for inc in incidentes:
            if inc["id"] == incident_id or str(inc["id"]) == str(incident_id):
                return inc
        return None

    def listar_acciones_incidente(self, incident_id: int) -> List[Dict[str, Any]]:
        """Retorna las acciones de contención, remediación y mitigación (demo.core_incidentaction)."""
        if check_postgres_alive():
            try:
                conn = get_postgres_connection()
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, action_type, responsible, action_date, description, evidence, "position", incident_id
                        FROM demo.core_incidentaction
                        WHERE incident_id = %s
                        ORDER BY "position" ASC;
                    """, (incident_id,))
                    actions = [dict(r) for r in cur.fetchall()]
                conn.close()
                return actions
            except Exception as e:
                logger.error(f"Error consultando core_incidentaction: {e}")

        # Acciones sintéticas para el fallback según el incidente
        return [
            {"id": incident_id * 10 + 1, "action_type": "C", "responsible": "CSIRT UNSA", "action_date": "2026-10-25", "description": "Aislamiento preventivo y bloqueo del vector vulnerable.", "evidence": "Log Fortinet / AWS IAM", "position": 1, "incident_id": incident_id},
            {"id": incident_id * 10 + 2, "action_type": "R", "responsible": "OTI UNSA / DBA", "action_date": "2026-10-26", "description": "Aplicación de parche técnico definitivo y actualización criptográfica.", "evidence": "Git commit de saneamiento", "position": 2, "incident_id": incident_id},
            {"id": incident_id * 10 + 3, "action_type": "M", "responsible": "DPO / Rectorado", "action_date": "2026-10-27", "description": "Emisión de directiva rectoral de cumplimiento y notificación ANPD.", "evidence": "Oficio Rectoral N° 0142-2026", "position": 3, "incident_id": incident_id}
        ]

    def listar_historial_incidente(self, incident_id: int) -> List[Dict[str, Any]]:
        """Retorna la línea de tiempo forense (demo.core_incidenthistory)."""
        if check_postgres_alive():
            try:
                conn = get_postgres_connection()
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, event_type, changed_at, actor, description, recipients_snapshot, incident_id
                        FROM demo.core_incidenthistory
                        WHERE incident_id = %s
                        ORDER BY changed_at ASC;
                    """, (incident_id,))
                    historial = [dict(r) for r in cur.fetchall()]
                conn.close()
                return historial
            except Exception as e:
                logger.error(f"Error consultando core_incidenthistory: {e}")
        return [
            {"id": 1, "event_type": "DETECCION", "changed_at": "2026-10-24 08:45:00", "actor": "Privacy Coach / CSIRT", "description": "Identificación de vulnerabilidad en escaneo pericial.", "recipients_snapshot": "dpo@unsa.edu.pe", "incident_id": incident_id},
            {"id": 2, "event_type": "NOTIFICACION_ANPD", "changed_at": "2026-10-25 10:15:00", "actor": "DPO Carlos Mendoza", "description": "Notificación dentro del plazo de 48h a la ANPD.", "recipients_snapshot": "anpd.denuncias@minjus.gob.pe", "incident_id": incident_id}
        ]

    def listar_destinatarios_notificacion(self) -> List[Dict[str, Any]]:
        """Retorna los canales formales de notificación (demo.core_incidentrecipient)."""
        if check_postgres_alive():
            try:
                conn = get_postgres_connection()
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, email, label, is_active FROM demo.core_incidentrecipient WHERE is_active = true ORDER BY id ASC;
                    """)
                    dest = [dict(r) for r in cur.fetchall()]
                conn.close()
                return dest
            except Exception as e:
                logger.error(f"Error consultando core_incidentrecipient: {e}")
        return [
            {"id": 601, "email": "dpo@unsa.edu.pe", "label": "Oficial de Protección de Datos (DPO UNSA)", "is_active": True},
            {"id": 602, "email": "ciso@unsa.edu.pe", "label": "Oficial de Seguridad OTI (CISO)", "is_active": True},
            {"id": 603, "email": "csirt@unsa.edu.pe", "label": "Equipo de Respuesta a Incidentes (CSIRT UNSA)", "is_active": True},
            {"id": 604, "email": "rectorado@unsa.edu.pe", "label": "Despacho Rectoral UNSA", "is_active": True},
            {"id": 606, "email": "anpd.denuncias@minjus.gob.pe", "label": "Dirección de Fiscalización e Instrucción (ANPD)", "is_active": True}
        ]

    def listar_trazas_seguridad(self) -> List[Dict[str, Any]]:
        """Retorna trazas técnicas disparadoras (demo.core_securitylog)."""
        if check_postgres_alive():
            try:
                conn = get_postgres_connection()
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, username, action, module, object_type, object_id, detail, ip_address, created_at
                        FROM demo.core_securitylog
                        ORDER BY id DESC LIMIT 50;
                    """)
                    logs = [dict(r) for r in cur.fetchall()]
                conn.close()
                return logs
            except Exception as e:
                logger.error(f"Error consultando core_securitylog: {e}")
        return [
            {"id": 601, "username": "anon_attacker", "action": "SQL_INJECTION", "module": "Hospital_Docente_Zamacola", "ip_address": "190.119.180.55", "created_at": "2026-10-24 03:15:00"},
            {"id": 602, "username": "crawler_bot_adm", "action": "BULK_DUMP", "module": "Modulo_Admision_Postulantes", "ip_address": "200.48.75.12", "created_at": "2026-10-26 22:30:00"},
            {"id": 603, "username": "operador_caja_03", "action": "CARD_EXPORT", "module": "Tesoreria_UNSApay", "ip_address": "172.16.20.45", "created_at": "2026-10-28 14:20:00"}
        ]

    def listar_activos_unsa(self) -> List[Dict[str, Any]]:
        """Retorna los activos institucionales (demo.core_asset)."""
        if check_postgres_alive():
            try:
                conn = get_postgres_connection()
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, name, code, description, category, classification, location,
                               owner, custodians, purpose, data_categories, pii_controls, legal_basis,
                               retention_period, disposal_method
                        FROM demo.core_asset
                        ORDER BY id ASC;
                    """)
                    activos = [dict(r) for r in cur.fetchall()]
                conn.close()
                if activos:
                    return activos
            except Exception as e:
                logger.error(f"Error consultando core_asset: {e}")
        return [
            {
                "id": 101, "code": "SYS-SISUNSA", "name": "Servidor de Base de Datos SISUNSA (PostgreSQL)",
                "category": "DATABASE", "classification": "CONFIDENCIAL",
                "description": "Base de datos relacional central que almacena expedientes académicos, actas de notas y matrículas.",
                "location": "Data Center Pabellón Central OTI - Área de Ingenierías",
                "custodians": "Ing. Pedro Cornejo (DBA OTI)",
                "legal_basis": "Ley Universitaria 30220 / Contrato de Matrícula",
                "retention_period": "Permanente durante condición de alumno + 10 años egresado",
                "pii_controls": ["CIFRADO_REPOSO", "MFA_ADMIN", "BACKUP_INMUTABLE", "CONTROL_ACCESO_RBAC"]
            },
            {
                "id": 102, "code": "SYS-HOSPITAL", "name": "Servidor de Historias Clínicas - Hospital Docente UNSA",
                "category": "DATABASE", "classification": "SECRETO",
                "description": "Base de datos del Hospital Docente que contiene historias clínicas, diagnósticos médicos CIE-10 y análisis.",
                "location": "Av. Aeropuerto N° 504, Zamácola, Cerro Colorado, Arequipa",
                "custodians": "Ing. Manuel Soto (Sistemas Hospital)",
                "legal_basis": "Ley General de Salud 26842 / Ley 29733 Art. 13",
                "retention_period": "20 años según Norma Técnica N° 139-MINSA/2018",
                "pii_controls": ["CONTROL_ACCESO_RBAC", "REGISTRO_TRAZABILIDAD", "PGCRYPTO_AES256"]
            },
            {
                "id": 103, "code": "SYS-SISADMIS", "name": "Portal Web SISADMISION y Banco de Postulantes",
                "category": "APPLICATION", "classification": "CONFIDENCIAL",
                "description": "Plataforma web donde los postulantes ingresan datos personales, fotos y huellas dactilares para admisión.",
                "location": "Servidores DMZ OTI (admision.unsa.edu.pe)",
                "custodians": "Área de Desarrollo OTI / DUA",
                "legal_basis": "Consentimiento del Postulante / RCU N° 0103-2026",
                "retention_period": "1 año para no ingresantes / Permanente para ingresantes",
                "pii_controls": ["WAF_FORTINET", "HTTPS_TLS_1_3", "HASH_ARGON2ID"]
            },
            {
                "id": 104, "code": "CLOUD-GSUITE", "name": "Google Workspace for Education Fundamentals (@unsa.edu.pe)",
                "category": "CLOUD_SERVICE", "classification": "CONFIDENCIAL",
                "description": "Servicio en la nube de Google LLC para correo electrónico institucional, Google Drive y Classroom.",
                "location": "Centros de Datos Google Cloud (EE.UU. e Irlanda)",
                "custodians": "Google LLC (Encargado) / OTI",
                "legal_basis": "Contrato de Servicios Cloud / Ley 29733 Art. 15 y 17",
                "retention_period": "Durante la vinculación académica o laboral + 180 días",
                "pii_controls": ["CONTRATO_DPA", "CIFRADO_TRANSITO_TLS", "MFA_OBLIGATORIO", "CLAUSULAS_SCC"]
            },
            {
                "id": 105, "code": "APP-MOODLE", "name": "Plataforma Aula Virtual Moodle UNSA",
                "category": "APPLICATION", "classification": "CONFIDENCIAL",
                "description": "Sistema de gestión de aprendizaje (LMS) donde se evalúa a los alumnos y se registran tareas.",
                "location": "Cluster Virtualizado OTI (aulavirtual.unsa.edu.pe)",
                "custodians": "Área de Servidores OTI / DUTE",
                "legal_basis": "Contrato de Matrícula Universitaria",
                "retention_period": "5 años tras la conclusión del semestre lectivo",
                "pii_controls": ["AUTENTICACION_GOOGLE_OAUTH", "HTTPS", "BACKUP_DIARIO"]
            },
            {
                "id": 106, "code": "ARCH-SANAGUSTIN", "name": "Archivo Central Físico de Grados, Títulos y Actas Históricas",
                "category": "PHYSICAL_ARCHIVE", "classification": "CONFIDENCIAL",
                "description": "Repositorio documental físico que custodia actas de notas originales, resoluciones rectorales y legajos.",
                "location": "Calle San Agustín N° 115, Cercado de Arequipa",
                "custodians": "Jefatura de Archivo Central / Secretaría General",
                "legal_basis": "Ley Nacional de Archivos / Ley Universitaria 30220",
                "retention_period": "Permanente / Histórico",
                "pii_controls": ["CONTROL_ACCESO_BIOMETRICO", "EXTINTORES_GAS_LIMPIO", "CCTV_24_7"]
            },
            {
                "id": 107, "code": "APP-TRAMITED", "name": "Sistema de Trámite Documentario Electrónico (TRAMITED)",
                "category": "APPLICATION", "classification": "CONFIDENCIAL",
                "description": "Sistema web para la recepción y seguimiento de expedientes con Código Único de Trámite (CUT) y solicitudes ARCO.",
                "location": "Servidores Web OTI (ouis.unsa.edu.pe/tramited/)",
                "custodians": "Área de Sistemas OTI / Mesa de Partes",
                "legal_basis": "Ley 27444 del Procedimiento Administrativo General / Ley 29733",
                "retention_period": "10 años según normativa de trámite documentario",
                "pii_controls": ["FIRMA_DIGITAL_RENIEC", "HTTPS", "FOLIO_ELECTRONICO_INALTERABLE"]
            },
            {
                "id": 108, "code": "APP-UNSAPAY", "name": "Pasarela de Recaudación de Tasas (Convenio Banco de la Nación)",
                "category": "APPLICATION", "classification": "CONFIDENCIAL",
                "description": "Módulo de recaudación de tasas de matrícula, certificados y trámites mediante convenio Págalo.pe y Caja Central.",
                "location": "Plataforma estatal pagalo.pe y ventanillas de Tesorería",
                "custodians": "Área de Desarrollo OTI / Tesorería",
                "legal_basis": "Ley General del Sistema Nacional de Tesorería",
                "retention_period": "10 años por normativa contable y tributaria SUNAT",
                "pii_controls": ["TOKENIZACION_PASARELA", "HTTPS_TLS_1_3", "POLITICA_NO_STORAGE_CVV"]
            },
            {
                "id": 109, "code": "APP-SISTUTORIA", "name": "Sistema de Tutoría y Acompañamiento Psicopedagógico",
                "category": "APPLICATION", "classification": "SECRETO",
                "description": "Módulo de seguimiento y entrevistas de tutoría académica y psicopedagógica para estudiantes.",
                "location": "Módulo interno en extranet.unsa.edu.pe/sisacad",
                "custodians": "Dirección Universitaria de Tutoría / OTI",
                "legal_basis": "Ley Universitaria 30220 Art. 69 / Ley 29733 Art. 13",
                "retention_period": "Durante la permanencia del estudiante en la facultad",
                "pii_controls": ["CONTROL_ACCESO_ESTRICTO", "ACCESO_SOLO_TUTOR_ASIGNADO"]
            },
            {
                "id": 110, "code": "APP-SISCOM", "name": "Sistema de Control de Comedor Universitario (DUDE)",
                "category": "APPLICATION", "classification": "CONFIDENCIAL",
                "description": "Sistema interno para la asignación de becas de comedor y control de entrega de raciones con carnet.",
                "location": "Red interna de comedores universitarios DUDE (Ingenierías, Sociales, Biomédicas)",
                "custodians": "Área de Sistemas OTI / DUDE",
                "legal_basis": "Estatuto UNSA / RCU N° 0340-2025",
                "retention_period": "3 años tras finalizar la beca alimentaria",
                "pii_controls": ["CONTROL_ACCESO_RBAC", "HTTPS"]
            }
        ]

    def listar_documentos_unsa(self) -> List[Dict[str, Any]]:
        """Retorna documentos oficiales registrados en demo.core_document."""
        if check_postgres_alive():
            try:
                conn = get_postgres_connection()
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, code, name, category, status, responsible, current_version
                        FROM demo.core_document
                        WHERE is_deleted = false
                        ORDER BY id ASC;
                    """)
                    docs = [dict(r) for r in cur.fetchall()]
                conn.close()
                return docs
            except Exception as e:
                logger.error(f"Error consultando core_document: {e}")
        return [
            {"id": 1, "code": "DOC-UNSA-DUA-001", "name": "Reglamento General de Admisión a Pregrado", "category": "REGLAMENTO", "responsible": "Director DUA"},
            {"id": 2, "code": "DOC-UNSA-SG-002", "name": "TUPA y Directiva de Trámite Documentario", "category": "DIRECTIVA", "responsible": "Secretaría General"},
            {"id": 3, "code": "DOC-UNSA-OTI-004", "name": "Resolución Rectoral N° 0503-2026 CSIRT UNSA", "category": "RESOLUCION", "responsible": "Jefatura OTI"}
        ]

    def actualizar_estado_incidente(self, incident_id: int, nuevo_estado: str) -> bool:
        """Actualiza el estado de un incidente en PostgreSQL."""
        if check_postgres_alive():
            try:
                conn = get_postgres_connection()
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE demo.core_incident
                        SET status = %s, updated_at = NOW()
                        WHERE id = %s;
                    """, (nuevo_estado, incident_id))
                conn.commit()
                conn.close()
                return True
            except Exception as e:
                logger.error(f"Error actualizando estado en core_incident: {e}")
        return True

    # =========================================================================
    # 2. OPERACIONES HEREDADAS / SQLITE LOCAL (COMPATIBILIDAD CON INGESTIÓN)
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
        return {
            "num_archivos": num_archivos,
            "num_activos": num_activos,
            "num_hallazgos": num_hallazgos
        }

    def registrar_archivo(self, nombre: str, tipo: str, tamano: int, resumen: Optional[str] = None) -> int:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO archivos_cargados (nombre_archivo, tipo_archivo, fecha_carga, tamano_bytes, resumen_analisis)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nombre, tipo, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tamano, resumen or "")
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
                activo.get("candado_deteccion"), activo.get("recomendacion_seguridad")
            )
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
                clausula.get("estado_cumplimiento", "OBSERVADO"), clausula.get("alerta_legal")
            )
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
                hallazgo.get("estado", "PENDIENTE")
            )
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
        conn = get_sqlite_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM archivos_cargados ORDER BY id DESC")
        archivos = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM inventario_activos_datos ORDER BY id ASC")
        inventario = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM clausulas_documentales ORDER BY id ASC")
        clausulas = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM hallazgos_dspm ORDER BY multa_estimada_uit DESC")
        hallazgos = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {
            "archivos": archivos,
            "inventario": inventario,
            "clausulas": clausulas,
            "hallazgos": hallazgos
        }

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
            (hallazgo_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rol, mensaje, reasoning or "", parche or "")
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
__all__ = ["repository", "AuditRepository", "FALLBACK_INCIDENTES_UNSA"]
