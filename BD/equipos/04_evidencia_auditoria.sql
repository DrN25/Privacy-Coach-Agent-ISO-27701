-- =============================================================================
-- [PLANTILLA / GUÍA DE EJEMPLO DE POBLACIÓN - GRUPO 4: EVIDENCIA Y AUDITORÍA]
-- Módulo: Programas de Auditoría Interna, Checklists y No Conformidades OCI
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- Marco Normativo: ISO/IEC 27001:2022 Cláusula 9.2 / ISO/IEC 27701:2025 Cláusula 5.8.2
-- =============================================================================
-- Rango de IDs Primarios Reservado para Grupo 4: 401 al 499
-- Creador por defecto: created_by_id = 5 (auditor_oci / Auditor Líder OCI UNSA)
-- =============================================================================

SET search_path TO demo, public;

-- 1. PROGRAMA Y ACTA DE AUDITORÍA INTERNA PIMS (demo.core_audit)
INSERT INTO demo.core_audit (
    id, created_at, updated_at, is_deleted, deleted_at, audit_code, audit_type, name, scope,
    objective, start_date, end_date, lead_auditor, audit_team, involved_areas, status, progress,
    created_by_id, deleted_by_id, updated_by_id
)
VALUES
(401, NOW(), NOW(), false, NULL, 'AUD-2026-PIMS-01', 'I',
 'Auditoría Interna de Privacidad y Bancos de Datos Personales UNSA 2026',
 'Sistemas SISUNSA (Matrícula), SISADMISION (Admisión) y Servidor de Historias Clínicas de Hospital Zamácola.',
 'Verificar la conformidad de los controles técnicos y organizativos con ISO/IEC 27701:2025 y la Ley 29733.',
 '2026-06-01', '2026-06-15', 'Ing. Roberto Gómez Salazar (Auditor Líder OCI)',
 'Lic. Carmen Torres (OCI), Ing. Luis Morales (Especialista TI)',
 'Oficina de Tecnologías de la Información (OTI), DUAA, Admisión y Hospital Docente',
 'C', 100, 5, NULL, NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, scope = EXCLUDED.scope;

-- 2. LISTA DE VERIFICACIÓN / CHECKLIST DE AUDITORÍA (demo.core_auditchecklistitem)
INSERT INTO demo.core_auditchecklistitem (
    id, source_requirement_code, process, standard, requirement, textual_evidence,
    "position", audit_id, gap_requirement_id
)
VALUES
(401, 'ISO 27701 - 7.2.2', 'PM.01 (Formación Académica / Matrícula)', 'ISO/IEC 27701:2025',
 'El responsable debe determinar y documentar los propósitos específicos del tratamiento de PII.',
 'Se verificó el Reglamento de Matrícula y la ficha de consentimiento informada en el portal matricula.unsa.edu.pe.',
 1, 401, 1),
(402, 'ISO 27701 - 7.4.1', 'PA.05 (Infraestructura TIC / OTI)', 'ISO/IEC 27701:2025',
 'La información confidencial y sensible debe almacenarse utilizando algoritmos de cifrado robustos.',
 'Al inspeccionar la base de datos PostgreSQL de SISUNSA se encontró que los historiales no contaban con cifrado en reposo habilitado.',
 2, 401, 1)
ON CONFLICT (id) DO UPDATE SET requirement = EXCLUDED.requirement, textual_evidence = EXCLUDED.textual_evidence;

-- 3. HALLAZGO / NO CONFORMIDAD REGISTRADA (demo.core_auditfinding)
INSERT INTO demo.core_auditfinding (
    id, classification, description, evidence, "position", audit_id
)
VALUES
(401, 'NC_MAYOR',
 'Ausencia de cifrado criptográfico en reposo sobre tablas que contienen datos personales de 25,000 alumnos en SISUNSA.',
 'Reporte de configuración pg_dump y parámetros de storage PostgreSQL sin tablespace cifrado.',
 1, 401)
ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description;

-- 4. PLAN DE ACCIÓN CORRECTIVA PARA EL LEVANTAMIENTO (demo.core_auditactionplan)
INSERT INTO demo.core_auditactionplan (
    id, action_plan, responsible, due_date, status, progress, closed_at, "position", finding_id
)
VALUES
(401,
 'Habilitar cifrado a nivel de volumen y tablespace con módulo pgcrypto / dm-crypt en los servidores del Data Center Central.',
 'Ing. Pedro Cornejo Quispe (DBA OTI)',
 '2026-08-30', 'E', 75, NULL, 1, 401)
ON CONFLICT (id) DO UPDATE SET action_plan = EXCLUDED.action_plan, progress = EXCLUDED.progress;

