-- =============================================================================
-- AGENTE 6: GESTIÓN DE INCIDENTES DE SEGURIDAD Y BRECHAS DE PII (PII BREACHES)
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- Marco Normativo: ISO/IEC 27701:2025 Cl. 7.2.9, 8.2 | ISO/IEC 27001:2022 A.5.24 - A.5.28
-- Marco Legal Nacional: Ley N° 29733, D.S. 003-2013-JUS, D.S. 016-2024-JUS, R.D. 019-2013-JUS
-- Marco Institucional: R.R. N° 0503-2026 (Creación CSIRT UNSA), RCU N° 0167-2020 (Procesos)
-- Catálogo Canónico de Reglas Periciales: R-001, R-002, R-003, R-004, R-005, R-006, R-007
-- Rango de Identificadores Primarios Reservado: 601 al 699
-- =============================================================================

SET search_path TO demo, public;

-- =============================================================================
-- 1. DESTINATARIOS INSTITUCIONALES DE ALERTAS DE BRECHA (demo.core_incidentrecipient)
-- Canales oficiales de comunicación inmediata ante incidentes y fiscalización ANPD
-- =============================================================================
INSERT INTO demo.core_incidentrecipient (id, email, label, is_active, created_at)
VALUES
(601, 'dpo@unsa.edu.pe', 'Oficial de Protección de Datos Personales (DPO UNSA)', true, NOW()),
(602, 'ciso@unsa.edu.pe', 'Oficial de Seguridad de la Información (CISO / OTI)', true, NOW()),
(603, 'csirt@unsa.edu.pe', 'Equipo de Respuesta ante Incidentes de Seguridad Digital (CSIRT UNSA - R.R. 0503-2026)', true, NOW()),
(604, 'rectorado@unsa.edu.pe', 'Despacho Rectoral UNSA (Representante Legal)', true, NOW()),
(605, 'auditoria.oci@unsa.edu.pe', 'Órgano de Control Institucional (OCI - Contraloría General)', true, NOW()),
(606, 'anpd.denuncias@minjus.gob.pe', 'Dirección de Fiscalización e Instrucción - ANPD Perú (MINJUSDH)', true, NOW())
ON CONFLICT (id) DO UPDATE
SET email = EXCLUDED.email, label = EXCLUDED.label, is_active = EXCLUDED.is_active;

-- =============================================================================
-- 2. TRAZAS DE AUDITORÍA Y EVENTOS DE SEGURIDAD DISPARADORES (demo.core_securitylog)
-- Registros técnicos capturados por WAF, proxies, base de datos y scripts de monitoreo
-- =============================================================================
INSERT INTO demo.core_securitylog (
    id, username, action, module, object_type, object_id, detail, ip_address, created_at, user_id
)
VALUES
-- Log 601: R-001 (Inyección SQL en historias clínicas del Hospital Docente de Zamácola)
(601, 'anon_attacker', 'SQL_INJECTION', 'Hospital_Docente_Zamacola', 'Table_FichaMedica', 102,
 '{"payload": "'' UNION SELECT id, dni, diagnostico_cie10, tratamiento, historia_clinica FROM ficha_medica --", "endpoint": "/consulta_paciente.php", "records_exfiltrated": 3420, "blocked": false, "source": "Tor Exit Node", "cve_pattern": "CWE-89"}'::jsonb,
 '190.119.180.55'::inet, NOW() - INTERVAL '10 days', 7),

-- Log 602: R-002 (Volcado masivo de contraseñas con hash MD5 en portal de postulantes)
(602, 'crawler_bot_adm', 'BULK_DUMP', 'Modulo_Admision_Postulantes', 'Table_Postulantes', 103,
 '{"query": "SELECT dni, password_hash, email FROM usuarios_postulantes WHERE proceso_id = 2026", "records_dumped": 18500, "hash_algorithm": "MD5_NO_SALT", "entropy": 3.2, "crack_rate_instant": "100%"}'::jsonb,
 '200.48.75.12'::inet, NOW() - INTERVAL '8 days', 7),

-- Log 603: R-003 (Exportación no autorizada de números de tarjeta y CVV en Tesorería Virtual)
(603, 'operador_caja_03', 'CARD_EXPORT', 'Tesoreria_UNSApay', 'Table_PagosOnline', 108,
 '{"action": "EXPORT_CSV", "contains_cvv": true, "contains_pan": true, "records_exported": 850, "gateway": "Pasarela_Web_Directa", "violation": "PCI-DSS 3.2 / Directiva R.D. 019-2013-JUS"}'::jsonb,
 '172.16.20.45'::inet, NOW() - INTERVAL '6 days', 7),

-- Log 604: R-006 (Sincronización automatizada hacia bucket S3 en Irlanda sin autorización)
(604, 'cron_backup_sync', 'CROSS_BORDER_SYNC', 'Infraestructura_Cloud_OTI', 'Table_SISUNSA_Backups', 101,
 '{"destination_cloud": "AWS S3 eu-west-1 (Ireland)", "bucket": "s3-unsa-db-backups-unencrypted", "records_synced": 25000, "size_gb": 42.5, "rnpdp_registered": false, "dpa_signed": false}'::jsonb,
 '52.218.40.10'::inet, NOW() - INTERVAL '5 days', 7),

-- Log 605: R-005 (Retención indefinida de padrones biométricos y personales de postulantes)
(605, 'auditor_profiler', 'DATA_RETENTION_SCAN', 'Direccion_Admision_DUA', 'Table_Historico_Postulantes', 103,
 '{"records_checked": 45200, "oldest_record_year": 2018, "unadmitted_candidates": 38900, "purge_policy_active": false, "violation": "Art. 7 y 8 Ley 29733 (Principio de Calidad y Proporcionalidad)"}'::jsonb,
 '10.0.5.15'::inet, NOW() - INTERVAL '4 days', 7),

-- Log 606: R-007 (Detección de cobro de tasas y exigencia de carta notarial para derechos ARCO)
(606, 'operador_mesa_partes', 'ARCO_RESTRICTION', 'Secretaria_General_TRAMITED', 'Table_TRAMITED_Expedientes', 107,
 '{"expediente_cut": "CUT-2026-004512", "derecho_solicitado": "CANCELACION", "tupa_tasa_exigida": 28.50, "notarial_requirement": true, "blocked_by_operator": true, "violation": "Art. 47 D.S. 003-2013-JUS"}'::jsonb,
 '10.0.8.22'::inet, NOW() - INTERVAL '3 days', 7),

-- Log 607: R-004 (Consentimiento presunto con casilla pre-marcada en formulario web)
(607, 'web_inspector', 'UNCONSENTED_SHARING', 'Direccion_Desarrollo_DUDE', 'Table_Comedor_SISCOM', 110,
 '{"form": "Ficha_Socioeconomica_Comedor_2026", "checkbox_prechecked": true, "purpose": "Cesion de datos a empresas bancarias privadas aliadas", "mandatory_for_submission": true, "violation": "Art. 5 Ley 29733"}'::jsonb,
 '10.0.12.30'::inet, NOW() - INTERVAL '2 days', 7)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 3. REGISTRO MAESTRO DE BRECHAS DE SEGURIDAD (demo.core_incident)
-- Modelado exhaustivo de los 7 arquetipos (R-001 a R-007) en activos reales de la UNSA
-- =============================================================================
INSERT INTO demo.core_incident (
    id, created_at, updated_at, is_deleted, deleted_at, incident_code,
    rep_document_number, rep_document_expiry, rep_first_name, rep_last_name_p, rep_last_name_m,
    rep_position, rep_phone, rep_email, entity_type, entity_ruc, entity_name, entity_phone,
    entity_extension, entity_department, entity_province, entity_district, involves_personal_data,
    incident_date, incident_time, detection_date, detection_time, incident_type, status,
    severity, impact, title, description, reported_by, assigned_to, affected_treatment,
    dpo_contact_name, dpo_contact_email, dpo_contact_phone, affected_data_types,
    num_affected_subjects, compromised_system, affected_url, evidence_refs,
    measure_updated_registry, measure_new_security, measure_improved_policies,
    measure_considered_resolved, measure_reported_authorities, security_measures_adopted,
    resolved_date, affected_cid, created_by_id, deleted_by_id, updated_by_id
)
VALUES
-- -----------------------------------------------------------------------------
-- INCIDENTE 601: Regla R-001 (Datos de Salud Sensibles sin Cifrar en Hospital Docente)
-- -----------------------------------------------------------------------------
(601, NOW() - INTERVAL '10 days', NOW() - INTERVAL '1 day', false, NULL, 'INC-UNSA-2026-001',
 '29481230', '2028-12-31', 'Hugo', 'Rojas', 'Flores',
 'Rector de la UNSA (Representante Legal)', '054-282828', 'rectorado@unsa.edu.pe',
 'P', '20140798781', 'Universidad Nacional de San Agustín de Arequipa', '054-282828',
 '101', 'Arequipa', 'Arequipa', 'Arequipa', true,
 CURRENT_DATE - INTERVAL '10 days', '03:15:00', CURRENT_DATE - INTERVAL '9 days', '08:45:00',
 'BF', 'C', 'C', 'C',
 'Exfiltración de 3,420 historias clínicas electrónicas no cifradas en Hospital Docente UNSA',
 'Ataque de inyección SQL explotando endpoint asistencial del Hospital Docente de Zamácola (IPRESS N° 00012398). Se exfiltraron 3,420 fichas médicas con diagnósticos CIE-10 (salud mental, patologías crónicas, tratamientos). Los datos estaban en texto plano en PostgreSQL sin cifrado en reposo pgcrypto ni segregación de tablas. Vulneración a los Arts. 9 y 38.2.b de la Ley 29733, D.S. 016-2024-JUS y control ISO 27701 A.3.24. Precedente análogo ANPD: R.D. 1045-2020-JUS (Clínica Montefiori - Multa 15.0 UIT) y R.D. 038-2022-JUS (Clínica Peruano Americana - Multa 13.7 UIT). Multa estimada calculada: 12.5 UIT (S/ 64,375).',
 'Equipo de Respuestas ante Incidentes de Seguridad Digital (CSIRT UNSA)', 'Ing. Marcos Ruiz Benavente (CISO / OTI)',
 'Banco de Datos Personales de Pacientes e Historias Clínicas del Hospital Docente',
 'Abog. Carlos Mendoza Valdivia (DPO UNSA)', 'dpo@unsa.edu.pe', '959123456',
 '["SALUD", "HISTORIA_CLINICA", "DIAGNOSTICOS_CIE10", "DNI", "TRATAMIENTO_FARMACOLOGICO"]'::jsonb,
 3420, 'Servidor de Base de Datos PostgreSQL srv-hosp-db (SYS-HOSPITAL, id=102)',
 'https://hospital.unsa.edu.pe/consulta_paciente.php',
 'Informe Pericial Forense CSIRT-UNSA-INF-2026-001.pdf; Oficio N° 0142-2026-R-UNSA a la ANPD; Actas de secuestro de logs en firewall Fortinet',
 'S', 'S', 'S', 'S', 'S',
 '{"isolation": "Servidor aislado en VLAN hospitalaria segura", "patching": "Saneamiento de sentencias SQL preparadas", "crypto_migration": "Implementación de extensión pgcrypto con AES-256 en tablas sensibles", "rbac": "Restricción de acceso exclusivo por credencial biométrica médica"}'::jsonb,
 CURRENT_DATE - INTERVAL '1 day',
 '{"confidentiality": true, "integrity": false, "availability": false}'::jsonb,
 7, NULL, 7),

-- -----------------------------------------------------------------------------
-- INCIDENTE 602: Regla R-002 (Almacenamiento de Contraseñas con Algoritmo Hash Débil MD5)
-- -----------------------------------------------------------------------------
(602, NOW() - INTERVAL '8 days', NOW() - INTERVAL '2 days', false, NULL, 'INC-UNSA-2026-002',
 '29481230', '2028-12-31', 'Hugo', 'Rojas', 'Flores',
 'Rector de la UNSA (Representante Legal)', '054-282828', 'rectorado@unsa.edu.pe',
 'P', '20140798781', 'Universidad Nacional de San Agustín de Arequipa', '054-282828',
 '101', 'Arequipa', 'Arequipa', 'Arequipa', true,
 CURRENT_DATE - INTERVAL '8 days', '22:30:00', CURRENT_DATE - INTERVAL '7 days', '09:00:00',
 'BF', 'C', 'A', 'A',
 'Volcado y descifrado masivo de 18,500 credenciales de postulantes con hash MD5 en SISADMISION',
 'Se detectó la publicación en foros externos de un volcado de base de datos conteniendo 18,500 cuentas de postulantes a CEPRUNSA y Examen Ordinario 2026. Las credenciales estaban almacenadas mediante hash obsoleto MD5 sin sal criptográfica heredado del sistema anterior. Las contraseñas fueron revertidas mediante tablas rainbow en menos de dos horas. Vulneración al Art. 9 y 38.2.b de la Ley 29733, D.S. 003-2013-JUS Art. 40 y control ISO 27701 A.3.13. Precedente análogo ANPD: R.D. 018-2021-JUS/DGTAIPD (Multa 8.8 UIT) y R.D. 074-2014-JUS (DatosPerú - Multa 30.0 UIT). Multa estimada calculada: 8.8 UIT (S/ 45,320).',
 'Privacy Coach Agent / Monitor CSIRT UNSA', 'Ing. Pedro Cornejo Quispe (DBA OTI)',
 'Banco de Datos de Postulantes a Pregrado de la Dirección de Admisión (DUA)',
 'Abog. Carlos Mendoza Valdivia (DPO UNSA)', 'dpo@unsa.edu.pe', '959123456',
 '["CREDENCIALES_ACCESO", "HASH_MD5_OBSOLETO", "DNI", "CORREO_ELECTRONICO", "TELEFONO"]'::jsonb,
 18500, 'Portal Web SISADMISION (SYS-SISADMIS, id=103)',
 'https://admision.unsa.edu.pe/login',
 'Informe de Vulnerabilidad USIRT-MD5-2026.pdf; Muestreo de hashes descifrados rainbow_proof.csv; Notificación ANPD Oficio N° 0158-2026-R-UNSA',
 'S', 'S', 'S', 'S', 'S',
 '{"force_reset": "Invalidadación masiva y forzado de reseteo de claves de 18,500 postulantes", "hash_upgrade": "Migración obligatoria a esquema Argon2id con salt aleatorio de 128 bits", "mfa": "Activación de código de verificación vía correo institucional"}'::jsonb,
 CURRENT_DATE - INTERVAL '2 days',
 '{"confidentiality": true, "integrity": false, "availability": false}'::jsonb,
 7, NULL, 7),

-- -----------------------------------------------------------------------------
-- INCIDENTE 603: Regla R-003 (Almacenamiento Ilegal de Tarjetas y CVV en Tesorería UNSApay)
-- -----------------------------------------------------------------------------
(603, NOW() - INTERVAL '6 days', NOW() - INTERVAL '1 day', false, NULL, 'INC-UNSA-2026-003',
 '29481230', '2028-12-31', 'Hugo', 'Rojas', 'Flores',
 'Rector de la UNSA (Representante Legal)', '054-282828', 'rectorado@unsa.edu.pe',
 'P', '20140798781', 'Universidad Nacional de San Agustín de Arequipa', '054-282828',
 '101', 'Arequipa', 'Arequipa', 'Arequipa', true,
 CURRENT_DATE - INTERVAL '6 days', '14:20:00', CURRENT_DATE - INTERVAL '5 days', '16:00:00',
 'BF', 'C', 'C', 'C',
 'Retención indebida y exportación no autorizada de 850 tarjetas de crédito y CVV en Tesorería',
 'Auditoría interna forense descubrió que el aplicativo de Tesorería almacenaba en base de datos los números de tarjeta (PAN), fecha de expiración y el código de seguridad CVV tras completarse el pago de matrículas y tasas universitarias. Un operador de ventanilla realizó la exportación no autorizada de un archivo CSV con 850 tarjetas. Vulneración grave al Principio de Proporcionalidad (Art. 7 Ley 29733), numeral 5.2 de la Directiva R.D. 019-2013-JUS, estándar PCI-DSS v4.0 Req 3.2.2 y control ISO 27701 A.1.4.5. Precedente análogo ANPD: R.D. 089-2021-JUS/DGTAIPD (Multa 15.0 UIT) y R.D. 1169-2020-JUS (Banco de Crédito del Perú - Multa 40.0 UIT). Multa estimada calculada: 15.0 UIT (S/ 77,250).',
 'Órgano de Control Institucional (OCI) / Auditor Líder', 'Ing. Marcos Ruiz Benavente (CISO / OTI)',
 'Sistema de Recaudación y Tesorería Virtual UNSApay',
 'Abog. Carlos Mendoza Valdivia (DPO UNSA)', 'dpo@unsa.edu.pe', '959123456',
 '["TARJETAS_CREDITO_PAN", "CODIGO_SEGURIDAD_CVV", "FECHA_EXPIRACION", "TITULAR_TARJETA", "MONTO_PAGO"]'::jsonb,
 850, 'Servidor de Pagos Tesorería (APP-UNSAPAY, id=108)',
 'https://pagos.unsa.edu.pe/checkout',
 'Acta_Constatacion_OCI_CVV_2026.pdf; Log_Export_Operador_03.csv; Oficio Notificación ANPD N° 0171-2026-R-UNSA; Denuncia Fiscal N° 4512-2026',
 'S', 'S', 'S', 'S', 'S',
 '{"immediate_purge": "Ejecución de script transaccional DROP COLUMN para eliminar columnas pan y cvv con sobreescritura DoD 5220.22-M", "tokenization": "Redirección total de pagos a pasarela externa tokenizada de Págalo.pe (Banco de la Nación)", "legal_action": "Procedimiento administrativo disciplinario y denuncia penal contra el operador"}'::jsonb,
 CURRENT_DATE - INTERVAL '1 day',
 '{"confidentiality": true, "integrity": false, "availability": false}'::jsonb,
 7, NULL, 7),

-- -----------------------------------------------------------------------------
-- INCIDENTE 604: Regla R-006 (Flujo Transfronterizo a Nube Extranjera sin Registro ANPD)
-- -----------------------------------------------------------------------------
(604, NOW() - INTERVAL '5 days', NOW(), false, NULL, 'INC-UNSA-2026-004',
 '29481230', '2028-12-31', 'Hugo', 'Rojas', 'Flores',
 'Rector de la UNSA (Representante Legal)', '054-282828', 'rectorado@unsa.edu.pe',
 'P', '20140798781', 'Universidad Nacional de San Agustín de Arequipa', '054-282828',
 '101', 'Arequipa', 'Arequipa', 'Arequipa', true,
 CURRENT_DATE - INTERVAL '5 days', '10:00:00', CURRENT_DATE - INTERVAL '4 days', '11:30:00',
 'BF', 'E', 'A', 'A',
 'Transferencia transfronteriza no autorizada de expedientes académicos de 25,000 alumnos a bucket Cloud',
 'Se descubrió la ejecución de un cronjob automatizado en el Data Center Central que sincronizaba copias completas de la base de datos SISUNSA conteniendo datos académicos de 25,000 estudiantes hacia un bucket de almacenamiento AWS S3 en Irlanda (eu-west-1), sin contar con un contrato de encargo DPA con Cláusulas Contractuales Tipo (SCC) ni haberse inscrito la transferencia transfronteriza ante el Registro Nacional de Protección de Datos Personales (RNPDP). Infracción Muy Grave bajo el Art. 15, Art. 17 y Art. 38.3.c de la Ley 29733, D.S. 003-2013-JUS Art. 66 y control ISO 27701 A.1.5.2. Precedente análogo ANPD: R.D. 125-2019-JUS y R.D. 234-2016-JUS. Multa estimada calculada: 11.0 UIT (S/ 56,650).',
 'Privacy Coach Agent / DSPM Engine', 'Dr. Alberto Carpio Pinto (Asesor Jurídico OUAJ)',
 'Copias de Seguridad y Base de Datos SISUNSA (PM.01 / PA.05)',
 'Abog. Carlos Mendoza Valdivia (DPO UNSA)', 'dpo@unsa.edu.pe', '959123456',
 '["EXPEDIENTES_ACADEMICOS", "ACTAS_NOTAS", "DNI", "DOMICILIO", "CORREO_INSTITUCIONAL"]'::jsonb,
 25000, 'Data Center Central OTI / AWS S3 Bucket s3-unsa-db-backups-unencrypted (SYS-SISUNSA, id=101)',
 'https://s3.eu-west-1.amazonaws.com/unsa-backups-unencrypted',
 'Dictamen Legal OUAJ N° 089-2026-UNSA; Configuración de script de backup sync_pg_dump.sh; Solicitud de inscripción de flujo transfronterizo ante la ANPD',
 'S', 'S', 'S', 'N', 'S',
 '{"cron_halt": "Suspensión inmediata de tareas programadas de sincronización externa", "iam_revocation": "Revocación de credenciales AWS Access Keys del servicio de respaldo", "dpa_negotiation": "Inicio de firma de anexo de transferencia internacional con Cláusulas Contractuales Tipo", "anpd_registration": "Trámite de inscripción en el Registro Nacional de Bancos de Datos Personales"}'::jsonb,
 NULL,
 '{"confidentiality": true, "integrity": false, "availability": false}'::jsonb,
 7, NULL, 7),

-- -----------------------------------------------------------------------------
-- INCIDENTE 605: Regla R-005 (Conservación Indefinida de Datos de Postulantes No Ingresantes)
-- -----------------------------------------------------------------------------
(605, NOW() - INTERVAL '4 days', NOW(), false, NULL, 'INC-UNSA-2026-005',
 '29481230', '2028-12-31', 'Hugo', 'Rojas', 'Flores',
 'Rector de la UNSA (Representante Legal)', '054-282828', 'rectorado@unsa.edu.pe',
 'P', '20140798781', 'Universidad Nacional de San Agustín de Arequipa', '054-282828',
 '101', 'Arequipa', 'Arequipa', 'Arequipa', true,
 CURRENT_DATE - INTERVAL '4 days', '09:00:00', CURRENT_DATE - INTERVAL '3 days', '15:00:00',
 'PI', 'E', 'M', 'M',
 'Conservación indefinida sin política de purga de datos biométricos de 45,200 postulantes no ingresantes',
 'Inspección de gobernanza digital identificó que la Dirección Universitaria de Admisión (DUA) mantiene en bases de datos relacionales activas los registros personales, fotografías y huellas dactilares biométricas de 45,200 postulantes no ingresantes de los periodos 2018 al 2024. El Reglamento de Admisión carece de plazo límite de conservación y de procedimiento de purga automática, contraviniendo el deber de cancelación y bloqueo una vez extinguida la finalidad de la postulación. Infracción Leve bajo los Arts. 7 y 8 de la Ley 29733, D.S. 003-2013-JUS Arts. 9 y 28, y control ISO 27701 A.1.4.8. Precedente análogo ANPD: R.D. 005-2016-JUS/DGPDP y R.D. 542-2019-JUS/DGTAIPD-DPDP. Multa estimada calculada: 5.0 UIT (S/ 25,750).',
 'Privacy Coach Agent / Auditor de RAT', 'Dr. Juan Valdivia Valdivia (Director de Admisión DUA)',
 'Banco de Datos de Postulantes de Pregrado y Posgrado (DUA)',
 'Abog. Carlos Mendoza Valdivia (DPO UNSA)', 'dpo@unsa.edu.pe', '959123456',
 '["BIOMETRICO_HUELLA", "FOTOGRAFIA_FACIAL", "DNI", "DOMICILIO", "COLEGIO_PROCEDENCIA"]'::jsonb,
 45200, 'Sistema SISADMISION (SYS-SISADMIS, id=103)',
 'https://admision.unsa.edu.pe/historico',
 'Informe de Auditoría RAT-DUA-2026-02.pdf; Propuesta de Directiva de Cancelación de Datos de Postulantes; Registro de tablas relacionales con retención indefinida',
 'S', 'N', 'S', 'N', 'N',
 '{"policy_formulation": "Redacción de la Política de Retención y Purga Documental de la DUA estableciendo caducidad a los 12 meses de culminado el concurso", "database_cleanup": "Programación de procedimiento almacenado para anonimización y borrado seguro de huellas de no ingresantes"}'::jsonb,
 NULL,
 '{"confidentiality": false, "integrity": true, "availability": false}'::jsonb,
 7, NULL, 7),

-- -----------------------------------------------------------------------------
-- INCIDENTE 606: Regla R-007 (Trabas al Ejercicio de Derechos ARCO y Cobro de Tasas en TRAMITED)
-- -----------------------------------------------------------------------------
(606, NOW() - INTERVAL '3 days', NOW(), false, NULL, 'INC-UNSA-2026-006',
 '29481230', '2028-12-31', 'Hugo', 'Rojas', 'Flores',
 'Rector de la UNSA (Representante Legal)', '054-282828', 'rectorado@unsa.edu.pe',
 'P', '20140798781', 'Universidad Nacional de San Agustín de Arequipa', '054-282828',
 '101', 'Arequipa', 'Arequipa', 'Arequipa', true,
 CURRENT_DATE - INTERVAL '3 days', '11:15:00', CURRENT_DATE - INTERVAL '2 days', '10:00:00',
 'PI', 'I', 'A', 'M',
 'Exigencia de tasa administrativa (TUPA) de S/ 28.50 y carta notarial para atender solicitudes ARCO en TRAMITED',
 'Queja formal de un grupo de egresados ante la DFI-ANPD reveló que el sistema de trámite documentario TRAMITED y la Mesa de Partes presencial (Calle San Agustín N° 115) rechazaban solicitudes de Cancelación y Oposición de datos personales si el titular no adjuntaba recibo de pago de tasa TUPA por S/ 28.50 y carta notarial legalizada. Esta práctica obstaculiza ilegalmente los derechos fundamentales ARCO, violando el principio de gratuidad obligatoria y sencillez procesal establecido en la Ley 29733 Arts. 19 al 24, D.S. 003-2013-JUS Art. 47 y control ISO 27701 A.1.3.7. Infracción Grave bajo el Art. 38.2.a de la Ley 29733. Precedente análogo ANPD: R.D. 022-2016-JUS/DGPDP y R.D. 112-2022-JUS. Multa estimada calculada: 9.0 UIT (S/ 46,350).',
 'Mesa de Ayuda de Transparencia / Queja de Ciudadanos', 'Lic. Rosa Fuentes Morales (Jefatura de Mesa de Partes)',
 'Sistema de Trámite Documentario TRAMITED y Atención al Usuario',
 'Abog. Carlos Mendoza Valdivia (DPO UNSA)', 'dpo@unsa.edu.pe', '959123456',
 '["SOLICITUDES_ARCO", "DNI", "DOMICILIO", "CORREO", "EXPEDIENTES_CUT"]'::jsonb,
 120, 'Sistema de Trámite Documentario Electrónico (APP-TRAMITED, id=107)',
 'https://ouis.unsa.edu.pe/tramited/',
 'Expediente CUT-2026-004512; Notificación de Reclamo ANPD EXP-2026-ARCO-0034; Capturas de pantalla de validación obligatoria de recibo de caja en portal web',
 'N', 'S', 'S', 'N', 'S',
 '{"immediate_waiver": "Emisión de Circular Rectoral declarando la gratuidad irrestricta de las solicitudes ARCO", "portal_hotfix": "Modificación del formulario web TRAMITED eliminando el campo obligatorio de subida de tasa TUPA y carta notarial", "training_staff": "Instrucción formal a los operadores de mesa de partes sobre los plazos legales de respuesta"}'::jsonb,
 NULL,
 '{"confidentiality": false, "integrity": true, "availability": false}'::jsonb,
 7, NULL, 7),

-- -----------------------------------------------------------------------------
-- INCIDENTE 607: Regla R-004 (Consentimiento Presunto / Casillas Pre-marcadas en Matrícula y Comedor)
-- -----------------------------------------------------------------------------
(607, NOW() - INTERVAL '2 days', NOW(), false, NULL, 'INC-UNSA-2026-007',
 '29481230', '2028-12-31', 'Hugo', 'Rojas', 'Flores',
 'Rector de la UNSA (Representante Legal)', '054-282828', 'rectorado@unsa.edu.pe',
 'P', '20140798781', 'Universidad Nacional de San Agustín de Arequipa', '054-282828',
 '101', 'Arequipa', 'Arequipa', 'Arequipa', true,
 CURRENT_DATE - INTERVAL '2 days', '16:45:00', CURRENT_DATE - INTERVAL '1 day', '09:30:00',
 'PI', 'I', 'A', 'M',
 'Casilla pre-marcada obligatoria para cesión comercial de datos personales en ficha de matrícula y comedor',
 'Auditoría pericial sobre los portales de autoservicio estudiantil (matricula.unsa.edu.pe y siscom.unsa.edu.pe) detectó la inclusión de un checkbox pre-marcado por defecto donde se imputaba consentimiento al alumno para transferir sus números de contacto, correo y rendimiento académico a empresas patrocinadoras de ferias de empleo y entidades bancarias privadas. El formulario impedía el envío de la matrícula si el estudiante desmarcaba la casilla. Vulneración flagrante al Principio de Consentimiento (Art. 5 Ley 29733), D.S. 003-2013-JUS Art. 12 (el consentimiento no puede ser presumido ni impuesto) y control ISO 27701 A.1.2.4. Infracción Grave bajo el Art. 38.2.b de la Ley 29733. Precedente análogo ANPD: R.D. 018-2021-JUS y R.D. 2196-2020-JUS (Banco BBVA Perú - Multa 16.0 UIT). Multa estimada calculada: 10.0 UIT (S/ 51,500).',
 'Privacy Coach Agent / DSPM Scanner Web', 'Mg. Elena Cornejo Valdivia (Dirección de Calidad)',
 'Sistema de Matrícula (SISUNSA) y Control de Comedor (SISCOM)',
 'Abog. Carlos Mendoza Valdivia (DPO UNSA)', 'dpo@unsa.edu.pe', '959123456',
 '["DATOS_CONTACTO", "CORREO_PERSONAL", "TELEFONO", "CONDICION_SOCIOECONOMICA", "HISTORIAL_ACADEMICO"]'::jsonb,
 22000, 'Portal de Matrícula y Sistema Comedor (SYS-SISUNSA id=101 / APP-SISCOM id=110)',
 'http://matricula.unsa.edu.pe/',
 'Reporte de Inspección Web DOM_Checkbox_Inspect_2026.pdf; Código fuente JavaScript matricula_validation.js; Acta de Alerta Pericial Privacy Coach',
 'N', 'S', 'S', 'N', 'N',
 '{"opt_in_refactor": "Desmarcado automático por defecto de todas las casillas de finalidades complementarias en los portales web", "disassociation": "Garantía de que la negativa a la cesión publicitaria no afecte en modo alguno la matrícula o el acceso al comedor universitario", "privacy_notice_update": "Publicación de política de privacidad clara y diferenciada por finalidades"}'::jsonb,
 NULL,
 '{"confidentiality": false, "integrity": true, "availability": false}'::jsonb,
 7, NULL, 7)
ON CONFLICT (id) DO UPDATE
SET title = EXCLUDED.title,
    description = EXCLUDED.description,
    severity = EXCLUDED.severity,
    impact = EXCLUDED.impact,
    evidence_refs = EXCLUDED.evidence_refs,
    security_measures_adopted = EXCLUDED.security_measures_adopted;

-- =============================================================================
-- 4. ACCIONES DE CONTENCIÓN, REMEDIACIÓN Y MITIGACIÓN (demo.core_incidentaction)
-- Pasos técnicos y jurídicos ejecutados para el cese del daño y cumplimiento de ley
-- =============================================================================
INSERT INTO demo.core_incidentaction (
    id, action_type, responsible, action_date, description, evidence, "position", incident_id
)
VALUES
-- Acciones Incidente 601 (R-001 - Hospital Docente)
(601, 'C', 'Ing. Manuel Soto (Sistemas Hospital)', CURRENT_DATE - INTERVAL '9 days',
 'Desconexión de cable de red del servidor srv-hosp-db y bloqueo del puerto 5432 en el firewall perimetral.',
 'Log de eventos Fortinet FW-UNSA-01; Registro de desconexión física en rack C-12 del Data Center Zamácola.', 1, 601),
(602, 'R', 'Ing. Pedro Cornejo Quispe (DBA OTI)', CURRENT_DATE - INTERVAL '8 days',
 'Saneamiento del endpoint con consultas parametrizadas y despliegue del módulo pgcrypto con cifrado simétrico AES-256 en columnas de diagnóstico y tratamiento.',
 'Git commit 7f8a12e "fix: sql injection sanitization and pgcrypto encryption on diagnostico column".', 2, 601),
(603, 'M', 'Abog. Carlos Mendoza Valdivia (DPO UNSA)', CURRENT_DATE - INTERVAL '7 days',
 'Emisión de Directiva de Seguridad de Historias Clínicas según NTS N° 139-MINSA/DGIEM y control de accesos por rol asistencial.',
 'Resolución Directoral Hospital Docente N° 045-2026-HD-UNSA.', 3, 601),

-- Acciones Incidente 602 (R-002 - Hashes MD5 en Admisión)
(604, 'C', 'Ing. Marcos Ruiz Benavente (CISO / OTI)', CURRENT_DATE - INTERVAL '7 days',
 'Revocación forzada de todas las sesiones web activas y bloqueo del acceso al portal de postulantes legacy.',
 'Bitácora de comando nginx reload y redirección de tráfico al nuevo portal seguro con HTTPS estricto.', 1, 602),
(605, 'R', 'Área de Desarrollo de Sistemas OTI', CURRENT_DATE - INTERVAL '6 days',
 'Despliegue del algoritmo de derivación de claves Argon2id con salt aleatorio de 128 bits e invalidación de hashes MD5.',
 'Pruebas de penetración automatizadas confirmando resistencia ante ataques de diccionario y rainbow tables.', 2, 602),
(606, 'M', 'Dirección Universitaria de Admisión (DUA)', CURRENT_DATE - INTERVAL '5 days',
 'Envío de correo masivo a los 18,500 postulantes requiriendo actualización obligatoria de contraseña mediante enlace firmado.',
 'Reporte de envíos del servidor SMTP institucional con 98.4% de tasa de entrega exitosa.', 3, 602),

-- Acciones Incidente 603 (R-003 - Retención de Tarjetas y CVV en Tesorería)
(607, 'C', 'Ing. Pedro Cornejo Quispe (DBA OTI)', CURRENT_DATE - INTERVAL '5 days',
 'Ejecución de script transaccional de borrado seguro con sobreescritura aleatoria sobre las columnas pan y cvv de la base de datos.',
 'Certificado de borrado criptográfico emitido por software de saneamiento de medios digitales.', 1, 603),
(608, 'R', 'Área de Sistemas OTI / Tesorería', CURRENT_DATE - INTERVAL '4 days',
 'Refactorización del código de checkout eliminando variables temporales de captura de CVV y conectando por API tokenizada con Págalo.pe.',
 'Informe de validación PCI-DSS v4.0 Req 3.2 suscrito por asesor externo.', 2, 603),
(609, 'M', 'Oficina Universitaria de Asesoría Jurídica (OUAJ)', CURRENT_DATE - INTERVAL '3 days',
 'Interposición de denuncia penal ante la Fiscalía Provincial Corporativa Especializada en Delitos Informáticos de Arequipa.',
 'Cargo de recepción de denuncia penal Expediente N° 4512-2026-MP-FN.', 3, 603),

-- Acciones Incidente 604 (R-006 - Flujo Transfronterizo a Cloud)
(610, 'C', 'Ing. Marcos Ruiz Benavente (CISO / OTI)', CURRENT_DATE - INTERVAL '4 days',
 'Revocación de API Keys de AWS IAM asociadas al bucket no registrado y detención del cronjob de sincronización de copias de seguridad.',
 'AWS CloudTrail Event: DeleteAccessKey para el usuario backup-svc-unsa.', 1, 604),
(611, 'R', 'Dr. Alberto Carpio Pinto (OUAJ) / OTI', CURRENT_DATE - INTERVAL '3 days',
 'Suscripción de Anexo de Tratamiento de Datos (DPA) con Amazon Web Services incorporando Cláusulas Contractuales Tipo (SCC).',
 'Contrato de Adhesión AWS Customer Agreement con Addendum de Privacidad N° 2026-AWS-UNSA.', 2, 604),
(612, 'M', 'Oficina de Protección de Datos Personales (DPO)', CURRENT_DATE - INTERVAL '2 days',
 'Presentación de solicitud de inscripción de flujo transfronterizo ante el Registro Nacional de Protección de Datos Personales (RNPDP).',
 'Cargo de trámite virtual ante el Ministerio de Justicia y Derechos Humanos (Expediente RNPDP-2026-FT-0041).', 3, 604),

-- Acciones Incidente 605 (R-005 - Conservación Indefinida de Postulantes)
(613, 'C', 'Dr. Juan Valdivia Valdivia (DUA)', CURRENT_DATE - INTERVAL '3 days',
 'Identificación y marcado lógico de 45,200 registros de postulantes no ingresantes de los años 2018 al 2024 para bloqueo temporal.',
 'Consulta SQL de etiquetado status = BLOCKED_PENDING_PURGE.', 1, 605),
(614, 'R', 'Oficina de Tecnologías de la Información (OTI)', CURRENT_DATE - INTERVAL '2 days',
 'Creación de tarea programada (cron job) mensual que ejecuta procedimiento de purga definitiva y borrado seguro tras 12 meses de concluido el concurso.',
 'Código fuente del procedimiento almacenado sp_purge_unadmitted_candidates.sql.', 2, 605),

-- Acciones Incidente 606 (R-007 - Trabas ARCO en TRAMITED)
(615, 'C', 'Secretaría General / Rectorado', CURRENT_DATE - INTERVAL '2 days',
 'Emisión de la Circular Rectoral N° 012-2026-R-UNSA recordando la gratuidad absoluta del ejercicio de derechos ARCO conforme al Art. 47 del D.S. 003-2013-JUS.',
 'Copia digital de Circular Rectoral publicada en el portal de transparencia institucional.', 1, 606),
(616, 'R', 'Área de Desarrollo de Sistemas OTI', CURRENT_DATE - INTERVAL '1 day',
 'Actualización del código del portal TRAMITED eliminando los requisitos bloqueantes de comprobante de pago TUPA y carta notarial.',
 'Deploy en producción del release v3.4.1 de TRAMITED; pruebas de envío de solicitud sin costo exitosas.', 2, 606),

-- Acciones Incidente 607 (R-004 - Consentimiento Presunto en Matrícula)
(617, 'C', 'Área de Desarrollo de Sistemas OTI', CURRENT_DATE - INTERVAL '1 day',
 'Modificación del front-end en matricula.unsa.edu.pe y siscom.unsa.edu.pe eliminando la marca predeterminada (checked=false).',
 'Pull Request mergeado #412 "fix: uncheck third party marketing consent boxes by default".', 1, 607),
(618, 'R', 'Dirección de Desarrollo Estudiantil (DUDE) / Calidad', CURRENT_DATE,
 'Aprobación del nuevo formato de Ficha Socioeconómica y Política de Privacidad de Comedor con finalidades claramente desglosadas.',
 'Resolución de Dirección Universitaria N° 028-2026-DUDE-UNSA.', 2, 607)
ON CONFLICT (id) DO UPDATE
SET description = EXCLUDED.description, evidence = EXCLUDED.evidence;

-- =============================================================================
-- 5. LÍNEA DE TIEMPO FORENSE Y BITÁCORA DE AUDITORÍA (demo.core_incidenthistory)
-- Cadena de custodia legal de eventos, notificaciones a la ANPD en 48h y comunicaciones
-- =============================================================================
INSERT INTO demo.core_incidenthistory (
    id, event_type, changed_at, actor, description, recipients_snapshot, changed_by_id, incident_id
)
VALUES
-- Historia Incidente 601 (R-001)
(601, 'DETECCION', NOW() - INTERVAL '9 days', 'Privacy Coach Agent',
 'Detección automática de brecha de confidencialidad R-001 por escaneo DSPM sobre base de datos en reposo.',
 'dpo@unsa.edu.pe, ciso@unsa.edu.pe', 7, 601),
(602, 'NOTIFICACION_ANPD', NOW() - INTERVAL '8 days', 'Abog. Carlos Mendoza Valdivia (DPO)',
 'Remisión formal del Reporte de Brecha de Seguridad a la ANPD dentro de las 48 horas exigidas por ley (Oficio N° 0142-2026-R-UNSA).',
 'anpd.denuncias@minjus.gob.pe, rectorado@unsa.edu.pe', 7, 601),
(603, 'CIERRE', NOW() - INTERVAL '1 day', 'Ing. Marcos Ruiz Benavente (CISO)',
 'Validación de remediación técnica y cierre formal del incidente tras verificación de cifrado pgcrypto.',
 'dpo@unsa.edu.pe, csirt@unsa.edu.pe', 7, 601),

-- Historia Incidente 602 (R-002)
(604, 'DETECCION', NOW() - INTERVAL '7 days', 'CSIRT UNSA (R.R. 0503-2026)',
 'Identificación de credenciales con cifrado roto MD5 (Regla R-002) expuestas en repositorio público.',
 'dpo@unsa.edu.pe, ciso@unsa.edu.pe', 7, 602),
(605, 'NOTIFICACION_ANPD', NOW() - INTERVAL '6 days', 'Abog. Carlos Mendoza Valdivia (DPO)',
 'Notificación formal a la Dirección de Fiscalización e Instrucción de la ANPD (Oficio N° 0158-2026-R-UNSA).',
 'anpd.denuncias@minjus.gob.pe', 7, 602),
(606, 'COMUNIC_AFECTADOS', NOW() - INTERVAL '5 days', 'Dirección Universitaria de Admisión',
 'Envío de correo masivo a 18,500 postulantes alertando del incidente y solicitando actualización de contraseña.',
 'postulantes2026@unsa.edu.pe', 7, 602),

-- Historia Incidente 603 (R-003)
(607, 'DETECCION', NOW() - INTERVAL '5 days', 'Órgano de Control Institucional (OCI)',
 'Descubrimiento de retención indebida de tarjetas de crédito y códigos CVV en servidor de Tesorería (Regla R-003).',
 'dpo@unsa.edu.pe, rectorado@unsa.edu.pe', 7, 603),
(608, 'NOTIFICACION_ANPD', NOW() - INTERVAL '4 days', 'Abog. Carlos Mendoza Valdivia (DPO)',
 'Notificación formal de la brecha de tesorería ante la ANPD (Expediente N° 2026-BRECHA-0089).',
 'anpd.denuncias@minjus.gob.pe', 7, 603),
(609, 'CIERRE', NOW() - INTERVAL '1 day', 'Dr. Hugo Rojas Flores (Rector)',
 'Cierre del incidente tras verificación de eliminación de CVV y remisión de actuados a la Fiscalía de Arequipa.',
 'rectorado@unsa.edu.pe, oci@unsa.edu.pe', 7, 603),

-- Historia Incidente 604 (R-006)
(610, 'DETECCION', NOW() - INTERVAL '4 days', 'Privacy Coach Agent / DSPM',
 'Identificación de flujo transfronterizo no registrado hacia la región eu-west-1 de AWS (Regla R-006).',
 'dpo@unsa.edu.pe, ciso@unsa.edu.pe', 7, 604),
(611, 'CONTENCION', NOW() - INTERVAL '3 days', 'Ing. Marcos Ruiz Benavente (CISO)',
 'Revocación de credenciales y detención de la transferencia de datos hacia la nube extranjera.',
 'ciso@unsa.edu.pe, oti@unsa.edu.pe', 7, 604),

-- Historia Incidente 605 (R-005)
(612, 'DETECCION', NOW() - INTERVAL '3 days', 'Auditoría Interna de Privacidad',
 'Hallazgo de conservación indefinida de datos biométricos de postulantes de periodos 2018-2024 (Regla R-005).',
 'dpo@unsa.edu.pe, admision@unsa.edu.pe', 7, 605),
(613, 'CONTENCION', NOW() - INTERVAL '2 days', 'Director DUA / OTI',
 'Bloqueo preventivo de acceso a los registros históricos y diseño de directiva de purga periódica.',
 'dpo@unsa.edu.pe, dua@unsa.edu.pe', 7, 605),

-- Historia Incidente 606 (R-007)
(614, 'DETECCION', NOW() - INTERVAL '2 days', 'Defensoría Universitaria / Queja Ciudadana',
 'Recepción de denuncia de egresados por cobro de tasa TUPA de S/ 28.50 para ejercer derecho de cancelación (Regla R-007).',
 'dpo@unsa.edu.pe, mesadepartes@unsa.edu.pe', 7, 606),
(615, 'CONTENCION', NOW() - INTERVAL '1 day', 'Secretaría General UNSA',
 'Instrucción a ventanillas y mesa virtual para trámite 100% gratuito sin exigencia notarial.',
 'rectorado@unsa.edu.pe, tramited@unsa.edu.pe', 7, 606),

-- Historia Incidente 607 (R-004)
(616, 'DETECCION', NOW() - INTERVAL '1 day', 'Privacy Coach Agent / Web Profiler',
 'Identificación de casilla pre-marcada obligatoria para fines comerciales en formulario de matrícula (Regla R-004).',
 'dpo@unsa.edu.pe, calidad@unsa.edu.pe', 7, 607),
(617, 'CONTENCION', NOW(), 'Área de Desarrollo de Sistemas OTI',
 'Actualización en caliente del front-end web eliminando el consentimiento presunto forzado.',
 'oti@unsa.edu.pe, dpo@unsa.edu.pe', 7, 607)
ON CONFLICT (id) DO UPDATE
SET description = EXCLUDED.description;

-- =============================================================================
-- 6. ARCHIVOS Y EVIDENCIAS ADJUNTAS DE INCIDENTES (demo.core_incidentattachment)
-- Informes periciales forenses, oficios remitidos a la ANPD y reportes de auditoría
-- =============================================================================
INSERT INTO demo.core_incidentattachment (
    id, file, file_name, uploaded_at, incident_id, uploaded_by_id
)
VALUES
(601, 'evidencias/reporte_forense_hospital_zamacola_601.pdf', 'reporte_forense_hospital_zamacola_601.pdf', NOW() - INTERVAL '9 days', 601, 7),
(602, 'evidencias/oficio_anpd_notificacion_brecha_salud_601.pdf', 'oficio_anpd_notificacion_brecha_salud_601.pdf', NOW() - INTERVAL '8 days', 601, 7),
(603, 'evidencias/analisis_rainbow_hashes_md5_admision_602.pdf', 'analisis_rainbow_hashes_md5_admision_602.pdf', NOW() - INTERVAL '7 days', 602, 7),
(604, 'evidencias/oficio_anpd_notificacion_credenciales_602.pdf', 'oficio_anpd_notificacion_credenciales_602.pdf', NOW() - INTERVAL '6 days', 602, 7),
(605, 'evidencias/acta_constatacion_oci_cvv_tesoreria_603.pdf', 'acta_constatacion_oci_cvv_tesoreria_603.pdf', NOW() - INTERVAL '5 days', 603, 7),
(606, 'evidencias/denuncia_penal_revelacion_cvv_fiscalia_603.pdf', 'denuncia_penal_revelacion_cvv_fiscalia_603.pdf', NOW() - INTERVAL '4 days', 603, 7),
(607, 'evidencias/informe_tecnico_flujo_transfronterizo_cloud_604.pdf', 'informe_tecnico_flujo_transfronterizo_cloud_604.pdf', NOW() - INTERVAL '3 days', 604, 7),
(608, 'evidencias/informe_auditoria_rat_retencion_postulantes_605.pdf', 'informe_auditoria_rat_retencion_postulantes_605.pdf', NOW() - INTERVAL '2 days', 605, 7),
(609, 'evidencias/circular_rectoral_gratuidad_derechos_arco_606.pdf', 'circular_rectoral_gratuidad_derechos_arco_606.pdf', NOW() - INTERVAL '1 day', 606, 7),
(610, 'evidencias/inspeccion_dom_consentimiento_presunto_matricula_607.pdf', 'inspeccion_dom_consentimiento_presunto_matricula_607.pdf', NOW(), 607, 7)
ON CONFLICT (id) DO UPDATE
SET file_name = EXCLUDED.file_name;
