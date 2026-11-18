-- =============================================================================
-- [PLANTILLA / GUÍA DE EJEMPLO DE POBLACIÓN - GRUPO 1: INVENTARIO DE DATOS Y RAT]
-- Módulo: Registro de Actividades de Tratamiento (RAT) y Evaluaciones DPIA
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- Marco Normativo: ISO/IEC 27701:2025 Cláusula 7.2.2 y 7.2.5 / Ley 29733 Art. 11 y 34
-- =============================================================================
-- Rango de IDs Primarios Reservado para Grupo 1: 111 al 199
-- Creador por defecto: created_by_id = 2 (rat_inventario / Custodio de BD)
-- =============================================================================

SET search_path TO demo, public;

-- 1. EVALUACIÓN DE IMPACTO EN PROTECCIÓN DE DATOS - DPIA (demo.core_personaldataimpactassessment)
-- Ejemplo: DPIA realizado sobre el Servidor Central de Matrícula y Expedientes (SYS-SISUNSA, id=101)
INSERT INTO demo.core_personaldataimpactassessment (
    id, created_at, updated_at, is_deleted, deleted_at, assessment_date, responsible,
    necessity_justification, proportionality_justification, data_subject_risks,
    mitigation_measures, residual_risk_acceptable, prior_consultation_required, conclusion,
    next_review_date, asset_id, created_by_id, deleted_by_id, updated_by_id
)
VALUES
(111, NOW(), NOW(), false, NULL, '2026-03-01', 'Ing. Pedro Cornejo Quispe',
 'El tratamiento de datos académicos, calificaciones y datos de contacto es estrictamente necesario para la certificación curricular y emisión de grados universitarios conforme a la Ley Universitaria 30220.',
 'Solo se solicitan datos pertinentes para la relación académica alumno-universidad, descartando datos biométricos invasivos o patrimoniales no justificados en el proceso de matrícula.',
 'Riesgo de filtración no autorizada de historiales de calificaciones a terceros o indexación involuntaria de actas en buscadores web públicos.',
 'Implementación de autenticación de doble factor para administradores OTI, cifrado de base de datos en reposo (AES-256) y segregación de perfiles docentes.',
 true, false,
 'Favorable con controles técnicos obligatorios. El riesgo residual se mantiene en nivel ACEPTABLE bajo supervisión trimestral.',
 '2027-03-01', 101, 2, NULL, NULL)
ON CONFLICT (id) DO UPDATE
SET necessity_justification = EXCLUDED.necessity_justification,
    mitigation_measures = EXCLUDED.mitigation_measures,
    conclusion = EXCLUDED.conclusion;

-- 2. OPERACIONES DE TRATAMIENTO DE DATOS PERSONALES (demo.core_personaldataoperation)
-- Registra las actividades que componen el RAT (recolección, almacenamiento, transferencia)
INSERT INTO demo.core_personaldataoperation (
    id, operation_type, occurred_at, description, recipient, purpose, legal_basis, responsible,
    is_cross_border, destination_country, data_categories_involved, annulment_reason, created_at,
    annuls_id, assessment_id, created_by_id
)
VALUES
-- Operación 111: Registro y validación académica semestral de alumnos regulares
(111, 'RECOLECCION_Y_REGISTRO', NOW(),
 'Captura y validación de fichas de matrícula, cursos inscritos y actas de notas para 25,000 estudiantes de pregrado.',
 'Dirección Universitaria de Asuntos Académicos (DUAA)',
 'Gestión curricular ordinaria y emisión de reportes académicos oficiales ante SUNEDU.',
 'Ley Universitaria 30220 / Reglamento General de Matrícula UNSA',
 'Ing. Pedro Cornejo Quispe',
 false, 'Perú',
 '["IDENTIFICACION", "ACADEMICO", "CALIFICACIONES", "CORREO_INSTITUCIONAL"]'::jsonb,
 '', NOW(), NULL, 111, 2),

-- Operación 112: Sincronización y flujo transfronterizo de cuentas institucionales a Google Cloud
(112, 'TRANSFERENCIA_TRANSFRONTERIZA', NOW(),
 'Aprovisionamiento automatizado de cuentas de correo @unsa.edu.pe y almacenamiento educativo en servidores de Google LLC.',
 'Google LLC (Mountain View, California, EE.UU.)',
 'Provisión de servicios de mensajería, correo institucional, Google Drive y Google Classroom.',
 'Contrato de Servicios Cloud / Ley 29733 Art. 15 (Encargo de Tratamiento)',
 'Ing. Marcos Ruiz Benavente (USIRT / OTI)',
 true, 'Estados Unidos / Irlanda',
 '["IDENTIFICACION", "CORREO_ELECTRONICO", "ARCHIVOS_DRIVE"]'::jsonb,
 '', NOW(), NULL, 111, 2)
ON CONFLICT (id) DO UPDATE
SET description = EXCLUDED.description, purpose = EXCLUDED.purpose, recipient = EXCLUDED.recipient;

