-- =============================================================================
-- [PLANTILLA / GUÍA DE EJEMPLO DE POBLACIÓN - GRUPO 2: EVALUACIÓN DE RIESGOS]
-- Módulo: Gestión, Evaluación y Tratamiento de Riesgos de Privacidad y Seguridad
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- Marco Normativo: ISO/IEC 27001:2022 Cláusula 6.1.2 / ISO/IEC 27701:2025 Cláusula 5.4
-- =============================================================================
-- Rango de IDs Primarios Reservado para Grupo 2: 201 al 299 (Periodo ID 1)
-- Creador por defecto: created_by_id = 3 (ciso_riesgos / Oficial CISO UNSA)
-- =============================================================================

SET search_path TO demo, public;

-- 1. PERIODO DE EVALUACIÓN DE RIESGOS (demo.core_riskperiod)
INSERT INTO demo.core_riskperiod (
    id, created_at, updated_at, is_deleted, deleted_at, name, start_date, end_date,
    status, is_active, description, closed_at, snapshot_matrix_name, snapshot_dimension,
    snapshot_risk_ranges, created_by_id, deleted_by_id, updated_by_id
)
VALUES
(1, NOW(), NOW(), false, NULL, 'Campaña Anual de Riesgos PIMS 2026', '2026-01-01', '2026-12-31',
 'O', true, 'Evaluación institucional de riesgos sobre confidencialidad, integridad y privacidad de bancos de datos UNSA.',
 NULL, 'Matriz 5x5 Criterio OTI UNSA', 5,
 '[{"name": "Bajo", "color": "#28a745", "min": 1, "max": 5}, {"name": "Medio", "color": "#ffc107", "min": 6, "max": 12}, {"name": "Alto", "color": "#fd7e14", "min": 15, "max": 20}, {"name": "Critico", "color": "#dc3545", "min": 21, "max": 25}]'::jsonb,
 3, NULL, NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, is_active = EXCLUDED.is_active;

-- 2. MATRIZ DE EVALUACIÓN DE RIESGOS (demo.core_riskevaluation)
INSERT INTO demo.core_riskevaluation (
    id, created_at, updated_at, is_deleted, deleted_at, risk_code, risk_owner, threat, vulnerability,
    description, controlled_probability, controlled_score, controlled_severity, residual_probability,
    residual_score, residual_severity, reduction, is_effective, verification_date, verified_by,
    evidence, observations, status, created_by_id, deleted_by_id, updated_by_id, threat_code,
    vulnerability_code, controlled_impact, residual_impact, response_strategy, carried_from_id, period_id
)
VALUES
-- Riesgo 201: Inyección SQL y exfiltración de datos académicos en SISUNSA
(201, NOW(), NOW(), false, NULL, 'RSK-SISUNSA-01', 'Ing. Pedro Cornejo (DBA OTI)',
 'Ataque externo de inyección SQL mediante endpoints no saneados del portal web estudiantil.',
 'Falta de validación estricta de parámetros y ausencia de WAF perimetral activo en horario de matrícula.',
 'Exfiltración no autorizada de historiales académicos, notas y datos de contacto de estudiantes.',
 4, 16.00, 'A', 2, 6.00, 'M', 10.00, 'S', '2026-04-15', 'Ing. Marcos Ruiz Benavente',
 'Reporte de análisis de vulnerabilidades Nessus y reglas implementadas en WAF Fortinet.',
 'Riesgo mitigado mediante parametrización ORM y bloqueo de firmas SQLi por WAF.', 'A',
 3, NULL, NULL, 'TH-SQLI-01', 'VULN-PARAM-01', 4, 3, 'M', NULL, 1),

-- Riesgo 202: Acceso indebido a historias clínicas en Hospital Docente (Salud / Sensible)
(202, NOW(), NOW(), false, NULL, 'RSK-HOSPITAL-01', 'Dr. Roberto Huamaní Almirón',
 'Acceso concurrente no autorizado a historias clínicas mediante credenciales compartidas en consultorios.',
 'Contraseñas por defecto y estaciones de enfermería sin bloqueo de sesión automático.',
 'Visualización y fuga de diagnósticos médicos CIE-10 y tratamientos de pacientes del Hospital Docente.',
 5, 20.00, 'C', 2, 4.00, 'B', 16.00, 'S', '2026-05-10', 'Ing. Marcos Ruiz Benavente',
 'Directiva de seguridad en estaciones de salud y registro de accesos por usuario nominal.',
 'Se implementó bloqueo por inactividad tras 3 minutos y credenciales únicas obligatorias.', 'A',
 3, NULL, NULL, 'TH-AUTH-02', 'VULN-PASS-02', 4, 2, 'M', NULL, 1)
ON CONFLICT (id) DO UPDATE
SET description = EXCLUDED.description, residual_score = EXCLUDED.residual_score;

-- 3. ASOCIACIÓN RIESGO - ACTIVO DE INFORMACIÓN (demo.core_riskevaluationasset)
INSERT INTO demo.core_riskevaluationasset (id, asset_id, evaluation_id)
VALUES
(201, 101, 201), -- Riesgo 201 asociado a SISUNSA (id=101)
(202, 102, 202)  -- Riesgo 202 asociado a Hospital Docente (id=102)
ON CONFLICT (id) DO NOTHING;

-- 4. CONTROLES MITIGANTES TÉCNICOS (demo.core_riskcontrol)
INSERT INTO demo.core_riskcontrol (id, control_type, description, security_measures, line_id)
VALUES
(201, 'PREVENTIVO', 'Inspección de tráfico web y WAF perimetral para filtrado de sintaxis maliciosa.',
 '{"tipo": "WAF", "marca": "Fortinet", "regla": "Bloqueo firmas OWASP Top 10"}'::jsonb, 201),
(202, 'CORRECTIVO', 'Cierre automático de sesión y autenticación biométrica en terminales asistenciales.',
 '{"tipo": "GPO_WINDOWS", "politica": "ScreenSaverTimeout 180s", "mfa": true}'::jsonb, 202)
ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description;

-- 5. PLAN DE TRATAMIENTO DE RIESGOS (demo.core_risktreatment)
INSERT INTO demo.core_risktreatment (id, plan_code, description, annex_a_control_id, evaluation_id)
VALUES
(201, 'TRT-2026-001', 'Migración obligatoria de sentencias SQL dinámicas a procedimientos preparados y auditoría DAST semestral.', 1, 201),
(202, 'TRT-2026-002', 'Implementación de registro inmutable de trazabilidad de consulta de historias clínicas según NTS MINSA.', 8, 202)
ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description;



-- 6. ASOCIACIÓN CONTROL DE RIESGO - CONTROLES DEL ANEXO A (demo.core_riskcontrol_annex_a_controls)
INSERT INTO demo.core_riskcontrol_annex_a_controls (id, riskcontrol_id, annexacontrol_id)
VALUES
(201, 201, 24) -- Control 201 vinculado al control A.8.24 (Uso de Criptografía, id=24)
ON CONFLICT (id) DO NOTHING;

-- 7. ACTIVIDADES ESPECÍFICAS DEL PLAN DE TRATAMIENTO (demo.core_risktreatmentactivity)
INSERT INTO demo.core_risktreatmentactivity (
    id, description, responsible_area, responsible, requires_investment,
    estimated_time, start_date, end_date, treatment_id
)
VALUES
(201, 'Habilitación de tablas cifradas en PostgreSQL y rotación de claves maestras con HSM.',
 'Oficina de Tecnologías de la Información (OTI)', 'Ing. Pedro Cornejo Quispe', false,
 '3 semanas', '2026-05-01', '2026-05-22', 201)
ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description;
