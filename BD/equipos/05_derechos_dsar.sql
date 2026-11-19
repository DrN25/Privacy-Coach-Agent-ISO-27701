-- =============================================================================
-- [PLANTILLA / GUÍA DE EJEMPLO DE POBLACIÓN - GRUPO 5: DERECHOS ARCO Y DSAR]
-- Módulo: Atención de Solicitudes ARCO y Registro de Consentimientos
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- Marco Normativo: Ley 29733 Arts. 18 al 24 / ISO/IEC 27701:2025 Cláusula 7.3
-- =============================================================================
-- Rango de IDs Primarios Reservado para Grupo 5: 501 al 599
-- Creador por defecto: created_by_id = 6 (operador_arco / Mesa de Partes UNSA)
-- =============================================================================

SET search_path TO demo, public;

-- 1. SOLICITUDES DE EJERCICIO DE DERECHOS ARCO (demo.core_arcorequest)
INSERT INTO demo.core_arcorequest (
    id, created_at, updated_at, is_deleted, deleted_at, case_code, channel,
    applicant_first_names, applicant_last_names, applicant_doc_type, applicant_doc_number,
    applicant_address, applicant_district, applicant_province, applicant_department,
    applicant_phone, applicant_mobile, applicant_email, applicant_portability_email,
    has_representative, rep_first_names, rep_last_names, rep_doc_type, rep_doc_number,
    rep_address, rep_district, rep_province, rep_department, rep_phone, rep_mobile, rep_email,
    right_type, treatment, description, responsible, priority, status,
    reception_datetime, sla_days, response_datetime, response_notes,
    created_by_id, deleted_by_id, updated_by_id
)
VALUES
-- Caso 501: Solicitud de Cancelación de datos por postulante no ingresante
(501, NOW(), NOW(), false, NULL, 'ARCO-2026-001', 'TRAMITED_VIRTUAL',
 'Renzo', 'Chávez Medina', 'DNI', '72345678',
 'Av. Dolores 123', 'José Luis Bustamante y Rivero', 'Arequipa', 'Arequipa',
 '054-421234', '959123456', 'renzo.chavez@gmail.com', '',
 false, '', '', '', '', '', '', '', '', '', '', '',
 'C', 'C', 'Solicita supresión definitiva de huellas dactilares y fotografía tras culminar el proceso de admisión 2026 sin vacante.',
 'Lic. Rosa Fuentes Morales (Mesa de Partes)', 'M', 'A',
 NOW() - INTERVAL '8 days', 10, NOW() - INTERVAL '2 days',
 'Se procedió al borrado lógico del banco de postulantes y eliminación de registros biométricos conforme al Art. 21 de Ley 29733.',
 6, NULL, NULL),

-- Caso 502: Solicitud de Rectificación de correo y domicilio de estudiante
(502, NOW(), NOW(), false, NULL, 'ARCO-2026-002', 'MESA_DE_PARTES_PRESENCIAL',
 'Gabriela', 'Paredes Cáceres', 'DNI', '73456789',
 'Calle Paucarpata 456', 'Cercado', 'Arequipa', 'Arequipa',
 '054-219876', '958765432', 'gparedesc@unsa.edu.pe', '',
 false, '', '', '', '', '', '', '', '', '', '', '',
 'R', 'C', 'Rectificación de segundo apellido y actualización de domicilio registrado erróneamente en el padrón de matrícula.',
 'Lic. Rosa Fuentes Morales (Mesa de Partes)', 'B', 'A',
 NOW() - INTERVAL '5 days', 10, NOW() - INTERVAL '1 day',
 'Actualización ejecutada en la tabla de alumnos de SISUNSA previa verificación con ficha RENIEC.',
 6, NULL, NULL)
ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description, response_notes = EXCLUDED.response_notes;

-- 2. TRAZABILIDAD Y EVENTOS DE ATENCIÓN ARCO (demo.core_arcohistory)
INSERT INTO demo.core_arcohistory (
    id, event_type, changed_at, actor, new_status, note, changed_by_id, request_id
)
VALUES
(501, 'RECEPCION', NOW() - INTERVAL '8 days', 'Lic. Rosa Fuentes Morales', 'P', 'Expediente digital recepcionado mediante TRAMITED y derivado a OTI.', 6, 501),
(502, 'RESOLUCION', NOW() - INTERVAL '2 days', 'Abog. Carlos Mendoza Valdivia (DPO)', 'A', 'Informe legal favorable emitido y borrado criptográfico certificado.', 6, 501)
ON CONFLICT (id) DO UPDATE SET note = EXCLUDED.note;

-- 3. REGISTRO DE CONSENTIMIENTOS INFORMADOS (demo.core_consent)
INSERT INTO demo.core_consent (
    id, created_at, updated_at, is_deleted, deleted_at, consent_code,
    data_subject_id, data_subject_name, email, phone, purpose, purpose_category,
    legal_basis, privacy_notice_version, capture_method, granted_at, expires_at,
    evidence_type, evidence_file, evidence_file_name, evidence_hash, ip_address,
    evidence_url, observations, status, revoked_at, revoked_reason,
    created_by_id, deleted_by_id, revoked_by_id, updated_by_id
)
VALUES
(501, NOW(), NOW(), false, NULL, 'CNS-2026-001',
 '72345678', 'Renzo Chávez Medina', 'renzo.chavez@gmail.com', '959123456',
 'Tratamiento de fotografía y biometría dactilar con fines de autenticación anti-suplantación en el Concurso Ordinario 2026.',
 'ADMISIÓN_UNIVERSITARIA', 'Ley 29733 Art. 13.5 (Consentimiento Expreso)', 'v2.1-2026', 'W',
 NOW() - INTERVAL '30 days', NOW() + INTERVAL '1 year',
 'D', '', 'formulario_admision_cns.pdf', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
 '200.48.56.12'::inet, 'https://admision.unsa.edu.pe/constancia/cns-001',
 'Aceptado digitalmente mediante checkbox obligatorio no pre-marcado en formulario web.',
 'A', NULL, NULL, 6, NULL, NULL, NULL)
ON CONFLICT (id) DO UPDATE SET purpose = EXCLUDED.purpose, status = EXCLUDED.status;

-- 4. HISTORIAL DE CONSENTIMIENTO (demo.core_consenthistory)
INSERT INTO demo.core_consenthistory (
    id, status, changed_at, actor, reason, capture_method, note, changed_by_id, consent_id
)
VALUES
(501, 'A', NOW() - INTERVAL '30 days', 'Renzo Chávez Medina', 'Registro inicial en concurso de admisión', 'W', 'Consentimiento otorgado con registro de IP y timestamp.', 6, 501)
ON CONFLICT (id) DO UPDATE SET note = EXCLUDED.note;



-- 5. ADJUNTOS PROBATORIOS DE SOLICITUDES ARCO (demo.core_arcoattachment)
INSERT INTO demo.core_arcoattachment (
    id, attachment_type, file, file_name, label, uploaded_at, uploaded_by_id, request_id
)
VALUES
(501, 'DNI_SOLICITANTE', 'adjuntos/arco/dni_solicitante_72345678.pdf', 'dni_solicitante_72345678.pdf',
 'Copia digital escaneada del DNI del titular para acreditación de identidad', NOW() - INTERVAL '8 days', 6, 501)
ON CONFLICT (id) DO UPDATE SET file_name = EXCLUDED.file_name;
