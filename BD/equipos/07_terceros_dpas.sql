-- =============================================================================
-- [PLANTILLA / GUÍA DE EJEMPLO DE POBLACIÓN - GRUPO 7: TERCEROS Y CONTRATOS DPA]
-- Módulo: Gestión Legal de Terceros Encargados del Tratamiento y Contratos DPA
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- Marco Normativo: ISO/IEC 27701:2025 Cláusula 8.2 / Ley 29733 Arts. 15, 16 y 17
-- =============================================================================
-- Rango de IDs Primarios Reservado para Grupo 7: 701 al 799
-- Creador por defecto: created_by_id = 8 (legal_terceros / Asesor Jurídico OUAJ)
-- Aprobador por defecto: approved_by_id = 1 (admin_sgpi / Rectorado UNSA)
-- =============================================================================

SET search_path TO demo, public;

-- 1. CONTRATOS DE ENCARGO Y POLÍTICAS DE PROVEEDORES (demo.core_document)
INSERT INTO demo.core_document (
    id, created_at, updated_at, is_deleted, deleted_at, code, current_version,
    name, category, status, responsible, created_by_id, deleted_by_id, updated_by_id,
    approved_at, approved_by_id
)
VALUES
-- Documento 701: Contrato de Encargo DPA con Google LLC para Google Workspace
(701, NOW(), NOW(), false, NULL, 'DPA-GOOGLE-2026', 1.00,
 'Acuerdo de Tratamiento de Datos (DPA) y Cláusulas Contractuales Tipo - Google Workspace for Education',
 'CONTRATO_ENCARGO', 'A', 'Dr. Alberto Carpio Pinto (OUAJ)',
 8, NULL, NULL, NOW() - INTERVAL '60 days', 1),

-- Documento 702: Política de Homologación de Proveedores Tecnológicos y Seguridad Cloud
(702, NOW(), NOW(), false, NULL, 'POL-TERCEROS-001', 1.50,
 'Política Institucional de Evaluación y Debida Diligencia para Proveedores de Servicios TI y Nube',
 'POLITICA_INSTITUCIONAL', 'A', 'Dr. Alberto Carpio Pinto (OUAJ)',
 8, NULL, NULL, NOW() - INTERVAL '30 days', 1)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status;

-- 2. VERSIONES Y ARCHIVOS DE DOCUMENTOS LEGALES (demo.core_documentversion)
INSERT INTO demo.core_documentversion (
    id, created_at, updated_at, is_deleted, deleted_at, version, file,
    change_summary, created_by_id, updated_by_id, deleted_by_id, document_id
)
VALUES
(701, NOW(), NOW(), false, NULL, 1.00, 'contratos/dpa_google_workspace_unsa_firmado.pdf',
 'Suscripción del anexo de privacidad y adecuación al Art. 15 del Reglamento de la Ley 29733 con cláusulas SCC.',
 8, NULL, NULL, 701),
(702, NOW(), NOW(), false, NULL, 1.50, 'politicas/politica_homologacion_proveedores_pims.pdf',
 'Inclusión de checklist obligatorio de cumplimiento ISO 27001 para contrataciones superiores a 8 UITs.',
 8, NULL, NULL, 702)
ON CONFLICT (id) DO UPDATE SET change_summary = EXCLUDED.change_summary;



-- 3. VINCULACIÓN CON REQUISITOS NORMATIVOS ISO (demo.core_document_gap_requirements)
INSERT INTO demo.core_document_gap_requirements (id, document_id, gaprequirement_id)
VALUES
(701, 701, 1) -- DPA Google vinculado al Requisito 1 de ISO/IEC 27701
ON CONFLICT (id) DO NOTHING;

-- 4. VINCULACIÓN ENTRE DOCUMENTOS RELACIONADOS (demo.core_document_related_documents)
INSERT INTO demo.core_document_related_documents (id, from_document_id, to_document_id)
VALUES
(701, 701, 702) -- Contrato DPA vinculado a la Política Institucional de Homologación de Proveedores
ON CONFLICT (id) DO NOTHING;
