-- =============================================================================
-- [PLANTILLA / GUÍA DE EJEMPLO DE POBLACIÓN - GRUPO 8: FORMACIÓN Y CONCIENCIA]
-- Módulo: Programas de Capacitación, Exámenes y Concientización en Privacidad
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- Marco Normativo: ISO/IEC 27001:2022 Control A.6.3 / ISO/IEC 27701:2025 Cláusula 5.4.3
-- =============================================================================
-- Rango de IDs Primarios Reservado para Grupo 8: 801 al 899
-- Creador por defecto: created_by_id = 9 (rrhh_formacion / Subdirección de RRHH)
-- =============================================================================

SET search_path TO demo, public;

-- 1. CURSO INSTITUCIONAL DE CAPACITACIÓN (demo.core_training)
INSERT INTO demo.core_training (
    id, created_at, updated_at, is_deleted, deleted_at, training_code, area, title,
    description, presenter, min_score, start_date, end_date, video_url,
    material_name, material_url, certificate_background, certificate_background_name,
    status, created_by_id, deleted_by_id, updated_by_id, duration
)
VALUES
(801, NOW(), NOW(), false, NULL, 'CAP-2026-PRIV-01', 'Subdirección de Recursos Humanos / OTI',
 'Curso Oficial: Protección de Datos Personales y Cumplimiento de la Ley 29733 en la UNSA',
 'Capacitación obligatoria para el personal administrativo y docente sobre el tratamiento de datos sensibles de estudiantes, deber de secreto y reporte de brechas.',
 'Abog. Carlos Mendoza Valdivia (Oficial DPO UNSA)', 14.00, '2026-03-01', '2026-04-30',
 'https://aulavirtual.unsa.edu.pe/mod/video/privacidad_2026',
 'Manual_Practico_Ley29733_UNSA.pdf', 'https://aulavirtual.unsa.edu.pe/materiales/manual_ley29733.pdf',
 '', '', 'A', 9, NULL, NULL, '10 horas académicas')
ON CONFLICT (id) DO UPDATE SET title = EXCLUDED.title, description = EXCLUDED.description;

-- 2. ASIGNACIÓN OBLIGATORIA A USUARIOS INSTITUCIONALES (demo.core_trainingassignment)
INSERT INTO demo.core_trainingassignment (
    id, is_mandatory, video_watched, attempts_count, best_score, passed,
    completed_at, assigned_at, training_id, user_id
)
VALUES
-- Asignación a usuario 2 (rat_inventario / Custodio de BD)
(801, true, true, 1, 18.00, true, NOW() - INTERVAL '15 days', NOW() - INTERVAL '30 days', 801, 2),
-- Asignación a usuario 6 (operador_arco / Mesa de Partes)
(802, true, true, 1, 16.00, true, NOW() - INTERVAL '10 days', NOW() - INTERVAL '30 days', 801, 6)
ON CONFLICT (id) DO UPDATE SET passed = EXCLUDED.passed, best_score = EXCLUDED.best_score;

-- 3. BANCO DE PREGUNTAS DE EVALUACIÓN (demo.core_trainingquestion)
INSERT INTO demo.core_trainingquestion (id, text, "position", training_id)
VALUES
(801, '¿Cuál es el plazo legal máximo que tiene la UNSA para notificar una brecha de seguridad a la ANPD según el Art. 34 de la Ley 29733?', 1, 801),
(802, '¿Qué categoría tienen los datos médicos e historias clínicas del Hospital Docente de la UNSA según la normativa peruana?', 2, 801)
ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text;

-- 4. INTENTO Y RESULTADO DE EXAMEN (demo.core_trainingexamattempt)
INSERT INTO demo.core_trainingexamattempt (
    id, answers, score, passed, taken_at, assignment_id
)
VALUES
(801, '{"q1": "48 horas", "q2": "Datos Sensibles con reserva absoluta"}'::jsonb, 18.00, true, NOW() - INTERVAL '15 days', 801)
ON CONFLICT (id) DO UPDATE SET score = EXCLUDED.score, passed = EXCLUDED.passed;



-- 5. OPCIONES DE RESPUESTA PARA EL BANCO DE PREGUNTAS (demo.core_trainingquestionoption)
INSERT INTO demo.core_trainingquestionoption (id, text, is_correct, "position", question_id)
VALUES
(801, '48 horas hábiles siguientes a la confirmación de la vulnerabilidad.', true, 1, 801),
(802, '30 días calendario al cierre del ejercicio anual.', false, 2, 801),
(803, 'Datos Sensibles de salud bajo reserva y confidencialidad absoluta.', true, 1, 802),
(804, 'Datos ordinarios de libre acceso institucional.', false, 2, 802)
ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text;

-- 6. CERTIFICADOS DIGITALES EMITIDOS POR APROBACIÓN (demo.core_certificate)
INSERT INTO demo.core_certificate (id, code, file, issued_at, assignment_id)
VALUES
(801, 'CERT-UNSA-2026-0001', 'certificados/cert_pedro_cornejo_pims_2026.pdf', NOW() - INTERVAL '15 days', 801)
ON CONFLICT (id) DO UPDATE SET code = EXCLUDED.code;
