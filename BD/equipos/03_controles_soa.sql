-- =============================================================================
-- [PLANTILLA / GUÍA DE EJEMPLO DE POBLACIÓN - GRUPO 3: CONTROLES Y SoA]
-- Módulo: Declaración de Aplicabilidad (SoA) y Madurez de Controles Anexo A
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- Marco Normativo: ISO/IEC 27001:2022 Control 6.1.3 / ISO/IEC 27701:2025 Cláusula 5.4.1
-- =============================================================================
-- Los 142 controles normativos ya están precatalogados (IDs 1 al 142 en gestitel_base_de_datos.sql).
-- Este grupo ACTUALIZA (UPDATE) la aplicabilidad, madurez, brecha y evidencias.
-- Creador/Actualizador por defecto: updated_by_id = 4 (soa_calidad / Dirección de Calidad)
-- =============================================================================

SET search_path TO demo, public;

-- 1. ACTUALIZACIÓN DE EVALUACIÓN DE CONTROLES DEL ANEXO A (demo.core_gapannexaassessment)
-- Ejemplo 1: Control A.5.1 (Políticas para la Seguridad de la Información)
UPDATE demo.core_gapannexaassessment
SET is_applicable = true,
    applicability_justification = 'Aplicable obligatoriamente. La UNSA requiere un marco formal de políticas de seguridad y privacidad aprobado por Consejo Universitario.',
    current_level = 3,
    target_level = 5,
    gap = 2,
    compliance = 60.00,
    evidence = 'Resolución de Consejo Universitario RCU N° 0167-2020 y Política de Privacidad publicada en portal web institucional.',
    improvement_action = 'Actualizar la política institucional incorporando formalmente los requisitos de ISO 27701:2025.',
    responsible = 'Mg. Elena Cornejo Valdivia (Calidad Académica)',
    priority = 'A',
    due_date = '2026-08-30',
    status = 'P',
    updated_at = NOW(),
    updated_by_id = 4
WHERE id = 1;

-- Ejemplo 2: Control A.8.24 (Uso de Criptografía)
UPDATE demo.core_gapannexaassessment
SET is_applicable = true,
    applicability_justification = 'Aplicable para proteger bases de datos relacionales con datos de estudiantes, postulantes e historias clínicas en reposo y en tránsito.',
    current_level = 2,
    target_level = 5,
    gap = 3,
    compliance = 40.00,
    evidence = 'Certificados SSL/TLS activos en portales web públicos. Pendiente habilitar cifrado a nivel de tablespace en PostgreSQL central.',
    improvement_action = 'Configurar pgcrypto y TDE en cluster de base de datos de producción SISUNSA.',
    responsible = 'Ing. Pedro Cornejo Quispe (DBA OTI)',
    priority = 'A',
    due_date = '2026-07-15',
    status = 'P',
    updated_at = NOW(),
    updated_by_id = 4
WHERE id = 24;

-- 2. SNAPSHOTS MENSUALES DE KPIS DE PRIVACIDAD (demo.core_dashboardsnapshot)
-- KPIs históricos para el panel de control ejecutivo de la Alta Dirección
INSERT INTO demo.core_dashboardsnapshot (
    id, month, kpi_key, value, has_data, captured_at
)
VALUES
(301, '2026-01-01', 'CUMPLIMIENTO_GLOBAL_SOA_PERCENT', 54.20, true, NOW()),
(302, '2026-02-01', 'CUMPLIMIENTO_GLOBAL_SOA_PERCENT', 58.70, true, NOW()),
(303, '2026-03-01', 'CUMPLIMIENTO_GLOBAL_SOA_PERCENT', 63.50, true, NOW())
ON CONFLICT (id) DO UPDATE
SET value = EXCLUDED.value, captured_at = EXCLUDED.captured_at;

