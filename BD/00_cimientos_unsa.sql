-- =============================================================================
-- CIMIENTOS INSTITUCIONALES UNSA (FASE 0)
-- Script de Desacoplamiento para Trabajo Paralelo de los 8 Agentes
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- Marco Legal: RCU N° 0167-2020 / RCU N° 0103-2026 / Norma Técnica N° 001-2018-PCM/SGP
-- =============================================================================

SET search_path TO demo, public;

-- 1. GRUPOS DE ROLES FUNCIONALES PIMS (demo.auth_group)
INSERT INTO demo.auth_group (id, name)
VALUES
(1, 'Administración General SGPI'),
(2, 'Gestión de Inventario de Datos y RAT'),
(3, 'Evaluación y Tratamiento de Riesgos'),
(4, 'Gobernanza de Controles y SoA'),
(5, 'Auditoría Interna y Evidencia'),
(6, 'Atención de Derechos ARCO y DSAR'),
(7, 'Gestión de Incidentes y Brechas de PII'),
(8, 'Gestión Legal de Terceros y DPAs'),
(9, 'Formación y Concientización en Privacidad')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

-- 2. PERFILES DESCRIPTIVOS DE ROL (demo.core_roleprofile)
INSERT INTO demo.core_roleprofile (id, description, is_system, group_id)
VALUES
(1, 'Alta dirección y administración del sistema PIMS. Aprueba políticas institucionales y alcance del SGSI.', true, 1),
(2, 'Custodio del Registro de Actividades de Tratamiento (RAT). Cataloga bancos de datos y ejecuta DPIAs.', true, 2),
(3, 'Oficial de Seguridad de la Información (CISO). Evalúa riesgos de confidencialidad, integridad y disponibilidad.', true, 3),
(4, 'Especialista en Sistemas de Gestión. Administra el SoA y mide la madurez de los 142 controles de ISO 27001/27701.', true, 4),
(5, 'Auditor Líder del OCI. Ejecuta programas de auditoría de privacidad y documenta No Conformidades.', true, 5),
(6, 'Operador de Mesa de Partes. Registra y tramita solicitudes ARCO y controla plazos de respuesta legal (SLA).', true, 6),
(7, 'Oficial de Protección de Datos Personales (DPO). Investiga brechas de PII y reporta a la ANPD en 48 horas.', true, 7),
(8, 'Asesor Jurídico. Revisa contratos de encargo de tratamiento con proveedores tecnológicos y flujos transfronterizos.', true, 8),
(9, 'Coordinador de Capacitación. Diseña y evalúa programas formativos en Ley 29733 para docentes y administrativos.', true, 9)
ON CONFLICT (id) DO UPDATE SET description = EXCLUDED.description;

-- 3. USUARIOS INSTITUCIONALES BASE (demo.auth_user)
INSERT INTO demo.auth_user (id, password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)
VALUES
(1, 'pbkdf2_sha256$600000$unsa_hash_admin$abc123xyz', true,  'admin_sgpi',     'Hugo',    'Rojas Flores',       'rectorado@unsa.edu.pe',         true,  true, NOW()),
(2, 'pbkdf2_sha256$600000$unsa_hash_rat$abc123xyz',   false, 'rat_inventario', 'Pedro',   'Cornejo Quispe',     'rat.inventario@unsa.edu.pe',    false, true, NOW()),
(3, 'pbkdf2_sha256$600000$unsa_hash_ciso$abc123xyz',  false, 'ciso_riesgos',   'Marcos',  'Ruiz Benavente',     'ciso@unsa.edu.pe',              true,  true, NOW()),
(4, 'pbkdf2_sha256$600000$unsa_hash_soa$abc123xyz',   false, 'soa_calidad',    'Elena',   'Cornejo Valdivia',   'calidad.academica@unsa.edu.pe', false, true, NOW()),
(5, 'pbkdf2_sha256$600000$unsa_hash_auditor$abc123xyz',false,'auditor_oci',   'Roberto', 'Gómez Salazar',      'auditoria.oci@unsa.edu.pe',     true,  true, NOW()),
(6, 'pbkdf2_sha256$600000$unsa_hash_arco$abc123xyz',  false, 'operador_arco',  'Rosa',    'Fuentes Morales',    'mesadepartes@unsa.edu.pe',      false, true, NOW()),
(7, 'pbkdf2_sha256$600000$unsa_hash_dpo$abc123xyz',   false, 'dpo_incidentes', 'Carlos',  'Mendoza Valdivia',   'dpo@unsa.edu.pe',               true,  true, NOW()),
(8, 'pbkdf2_sha256$600000$unsa_hash_legal$abc123xyz', false, 'legal_terceros', 'Alberto', 'Carpio Pinto',       'asesoria.juridica@unsa.edu.pe', false, true, NOW()),
(9, 'pbkdf2_sha256$600000$unsa_hash_rrhh$abc123xyz',  false, 'rrhh_formacion', 'Teresa',  'Zúñiga Paredes',     'capacitacion.rrhh@unsa.edu.pe', false, true, NOW())
ON CONFLICT (id) DO UPDATE 
SET username = EXCLUDED.username, first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, email = EXCLUDED.email;

-- 4. PERFILES DE USUARIO ORGÁNICOS (demo.core_userprofile)
INSERT INTO demo.core_userprofile (id, user_id, area, "position", is_platform_admin, must_change_password)
VALUES
(1, 1, 'Rectorado / Despacho Rectoral', 'Rector de la Universidad Nacional de San Agustín', true, false),
(2, 2, 'Oficina de Tecnologías de la Información (OTI)', 'Especialista en Custodia de Bases de Datos y RAT', false, false),
(3, 3, 'Unidad de Seguridad de la Información (USIRT / OTI)', 'Oficial de Seguridad de la Información (CISO)', false, false),
(4, 4, 'Dirección Universitaria de Calidad Académica', 'Coordinador del Sistema de Gestión de Privacidad', false, false),
(5, 5, 'Órgano de Control Institucional (OCI)', 'Auditor Líder de Sistemas de Gestión', false, false),
(6, 6, 'Secretaría General / Mesa de Partes', 'Responsable de Atención de Solicitudes ARCO', false, false),
(7, 7, 'Oficina de Protección de Datos Personales', 'Oficial de Protección de Datos Personales (DPO)', false, false),
(8, 8, 'Oficina Universitaria de Asesoría Jurídica (OUAJ)', 'Especialista Legal en Contratos y Convenios TI', false, false),
(9, 9, 'Subdirección de Recursos Humanos', 'Coordinadora de Capacitación y Desarrollo Institucional', false, false)
ON CONFLICT (id) DO UPDATE
SET area = EXCLUDED.area, "position" = EXCLUDED."position", is_platform_admin = EXCLUDED.is_platform_admin;

-- 5. ASOCIACIÓN USUARIO - GRUPO (demo.auth_user_groups)
INSERT INTO demo.auth_user_groups (id, user_id, group_id)
VALUES
(1, 1, 1),
(2, 2, 2),
(3, 3, 3),
(4, 4, 4),
(5, 5, 5),
(6, 6, 6),
(7, 7, 7),
(8, 8, 8),
(9, 9, 9)
ON CONFLICT (id) DO UPDATE SET group_id = EXCLUDED.group_id;

-- 6. LOS 15 MACROPROCESOS OFICIALES DE LA UNSA (demo.core_process)
-- Fuente Oficial: RCU N° 0167-2020 (12 de marzo de 2020) / Norma Técnica N° 001-2018-PCM/SGP
INSERT INTO demo.core_process (id, created_at, updated_at, is_deleted, deleted_at, code, name, type, area, responsible, objective, status, created_by_id)
VALUES
-- Procesos Estratégicos (E) - 4 Macroprocesos
(1, NOW(), NOW(), false, NULL, 'PE.01', 'Gestión del Planeamiento Estratégico y Presupuesto', 'E', 'Oficina Universitaria de Planeamiento y Desarrollo', 'Dr. Víctor Hugo Cornejo', 'Conducir el planeamiento integral de la universidad y formular el presupuesto anual para sostener la gobernanza universitaria.', 'A', 1),
(2, NOW(), NOW(), false, NULL, 'PE.02', 'Gestión de la Calidad y Acreditación Institucional', 'E', 'Dirección Universitaria de Calidad Académica', 'Mg. Elena Cornejo Valdivia', 'Garantizar el cumplimiento de estándares de calidad educativa, licenciamiento SUNEDU y acreditaciones institucionales.', 'A', 1),
(3, NOW(), NOW(), false, NULL, 'PE.03', 'Gestión de la Internacionalización y Convenios', 'E', 'Dirección de Cooperación y Relaciones Internacionales', 'Dra. María Elena Rivera', 'Promover la movilidad académica y convenios con universidades e instituciones del exterior garantizando flujos transfronterizos seguros.', 'A', 1),
(4, NOW(), NOW(), false, NULL, 'PE.04', 'Gestión de Riesgos y Control Institucional', 'E', 'Órgano de Control Institucional (OCI)', 'Ing. Roberto Gómez Salazar', 'Supervisar el control interno, la legalidad de los actos administrativos y la mitigación de riesgos institucionales.', 'A', 1),

-- Procesos Misionales / Operativos (O) - 3 Macroprocesos
(5, NOW(), NOW(), false, NULL, 'PM.01', 'Formación Académica Integral', 'O', 'Vicerrectorado Académico / DUFA', 'Dr. Fredy Zegarra Black', 'Planificar, ejecutar y evaluar la formación universitaria de pregrado y posgrado (admisión, matrícula, carga lectiva, plataformas LMS y graduación).', 'A', 1),
(6, NOW(), NOW(), false, NULL, 'PM.02', 'Investigación, Innovación y Emprendedurismo', 'O', 'Vicerrectorado de Investigación (VRI)', 'Dr. Henry Polanco Cornejo', 'Fomentar y gestionar proyectos de investigación científica, innovación tecnológica y asignación de fondos del canon minero.', 'A', 1),
(7, NOW(), NOW(), false, NULL, 'PM.03', 'Responsabilidad Social Universitaria y Extensión Cultural', 'O', 'Dirección Universitaria de Responsabilidad Social (DURS)', 'Dr. Roberto Huamaní Almirón', 'Vincular la universidad con la sociedad mediante extensión cultural, proyectos comunitarios y servicios asistenciales de salud en el Hospital Docente.', 'A', 1),

-- Procesos de Apoyo / Soporte (A) - 8 Macroprocesos
(8,  NOW(), NOW(), false, NULL, 'PA.01', 'Gestión Financiera y Contable', 'A', 'Dirección General de Administración / Unidad de Tesorería', 'C.P.C. Marilú Chara Rodríguez', 'Recaudar tasas universitarias mediante plataformas web y pasarelas de pago, administrar tesorería y conciliar estados financieros.', 'A', 1),
(9,  NOW(), NOW(), false, NULL, 'PA.02', 'Gestión del Talento Humano', 'A', 'Subdirección de Recursos Humanos', 'Lic. Teresa Zúñiga Paredes', 'Gestionar legajos del personal docente y administrativo, control de asistencia biométrica y planillas de haberes.', 'A', 1),
(10, NOW(), NOW(), false, NULL, 'PA.03', 'Gestión de Logística, Abastecimiento e Infraestructura', 'A', 'Subdirección de Logística', 'Lic. Carlos Valdivia Romero', 'Abastecer bienes, servicios y ejecución de infraestructura institucional conforme a la normativa de contrataciones del Estado.', 'A', 1),
(11, NOW(), NOW(), false, NULL, 'PA.04', 'Gestión Legal y Asesoría Jurídica', 'A', 'Oficina Universitaria de Asesoría Jurídica (OUAJ)', 'Dr. Alberto Carpio Pinto', 'Emitir dictámenes legales, defensa jurídica y velar por el cumplimiento de cláusulas contractuales tipo en convenios y contrataciones TI.', 'A', 1),
(12, NOW(), NOW(), false, NULL, 'PA.05', 'Gestión de Tecnologías de la Información y Comunicación (TIC)', 'A', 'Oficina de Tecnologías de la Información (OTI)', 'Ing. Marcos Ruiz Benavente', 'Administrar el Data Center Central, cluster de virtualización, redes de comunicaciones y seguridad de la información institucional.', 'A', 3),
(13, NOW(), NOW(), false, NULL, 'PA.06', 'Gestión del Bienestar Universitario', 'A', 'Dirección Universitaria de Desarrollo Estudiantil (DUDE)', 'Lic. David Cárdenas Gómez', 'Brindar bienestar social, comedores universitarios, orientación psicopedagógica y salud integral al estudiante agustino.', 'A', 1),
(14, NOW(), NOW(), false, NULL, 'PA.07', 'Gestión de la Comunicación e Imagen Institucional', 'A', 'Oficina de Comunicación e Imagen Institucional', 'Lic. Milagros Pacheco Morales', 'Gestionar las comunicaciones oficiales, publicaciones en redes institucionales y relaciones públicas de la universidad.', 'A', 1),
(15, NOW(), NOW(), false, NULL, 'PA.08', 'Gestión Documentaria y Archivo Institucional', 'A', 'Secretaría General / Mesa de Partes / Archivo Central', 'Lic. Rosa Fuentes Morales', 'Centralizar el trámite de expedientes CUT presenciales y digitales en TRAMITED, y custodiar el acervo documental histórico en San Agustín 115.', 'A', 1)
ON CONFLICT (id) DO UPDATE
SET code = EXCLUDED.code, name = EXCLUDED.name, area = EXCLUDED.area, responsible = EXCLUDED.responsible, objective = EXCLUDED.objective;

-- 7. ACTIVOS DE INFORMACIÓN ANCLA Y BANCOS DE DATOS REALES (demo.core_asset)
-- Fuente Oficial: Directorio OTI UNSA / Portal de Transparencia / Registro Nacional de Bancos de Datos Personales
INSERT INTO demo.core_asset (
    id, created_at, updated_at, is_deleted, deleted_at, code, name, description, owner, custodians, location,
    is_data_asset, category, classification, usage_frequency, confidentiality, integrity, availability,
    weight_confidentiality, weight_integrity, weight_availability, purpose, data_categories, role, pii_controls,
    legal_basis, purpose_detail, collection_origin, collection_procedure, data_usage, retention_period, disposal_method,
    third_party_transfer, national_transfers, cross_border_flow, international_flows, times_compromised, processes_affected,
    loss_range, relevance, created_by_id, process_id, asset_value, cid_method, legacy_code
)
VALUES
-- ACT-101: SISUNSA Central -> Vinculado a PM.01 (Formación Académica Integral, id=5)
(101, NOW(), NOW(), false, NULL, 'SYS-SISUNSA', 'Servidor de Base de Datos SISUNSA (PostgreSQL)',
 'Base de datos relacional central que almacena expedientes académicos, actas de notas y matrículas de pregrado y posgrado.',
 'OTI UNSA / DUAA', 'Ing. Pedro Cornejo (DBA OTI)', 'Data Center Pabellón Central OTI - Área de Ingenierías',
 true, 'DATABASE', 'CONFIDENCIAL', 'CONTINUA', 'ALTA', 'ALTA', 'ALTA',
 1.00, 1.00, 1.00, 'Gestión de expedientes de matrícula, actas de notas y emisión de grados universitarios.',
 '["IDENTIFICACION", "ACADEMICO", "CALIFICACIONES", "CORREO_INSTITUCIONAL"]'::jsonb, 'CONTROLLER',
 '["CIFRADO_REPOSO", "MFA_ADMIN", "BACKUP_INMUTABLE", "CONTROL_ACCESO_RBAC"]'::jsonb,
 'Ley Universitaria 30220 / Contrato de Matrícula', 'Tratamiento curricular para obtención de grados académicos.',
 'Portal web matricula.unsa.edu.pe y extranet.unsa.edu.pe/sisacad', 'Registro directo por el estudiante y carga lectiva docente',
 'Gestión académica interna y fiscalización SUNEDU', 'Permanente durante condición de alumno + 10 años egresado',
 'Sobreescritura segura certificada DoD 5220.22-M', false, '[]'::jsonb, false, '[]'::jsonb, 0, 'PM.01', 'ALTO', 'CRITICO', 2, 5, 5.00, 'P', 'SRV-DB-SISUNSA'),

-- ACT-102: Hospital Docente Zamácola -> Vinculado a PM.03 (Responsabilidad Social Universitaria, id=7)
(102, NOW(), NOW(), false, NULL, 'SYS-HOSPITAL', 'Servidor de Historias Clínicas - Hospital Docente UNSA',
 'Base de datos del Hospital Docente que contiene historias clínicas, diagnósticos médicos CIE-10 y análisis de laboratorio.',
 'Dirección Hospital Docente', 'Ing. Manuel Soto (Sistemas Hospital)', 'Av. Aeropuerto N° 504, Zamácola, Cerro Colorado, Arequipa',
 true, 'DATABASE', 'SECRETO', 'DIARIA', 'ALTA', 'ALTA', 'ALTA',
 1.00, 1.00, 1.00, 'Atención clínica, triaje, prescripciones médicas y seguimiento asistencial de pacientes.',
 '["IDENTIFICACION", "SALUD", "HISTORIA_CLINICA", "DIAGNOSTICOS_CIE10", "DATOS_SENSIBLES"]'::jsonb, 'CONTROLLER',
 '["CONTROL_ACCESO_RBAC", "REGISTRO_TRAZABILIDAD"]'::jsonb,
 'Ley General de Salud 26842 / Ley 29733 Art. 13', 'Prestación de servicios de salud y archivo clínico asistencial.',
 'Ficha de triaje médico y consulta en consultorio', 'Registro directo por médicos tratantes',
 'Atención médica y farmacológica', '20 años según Norma Técnica de Historias Clínicas del MINSA',
 'Borrado criptográfico y destrucción física de fichas caducadas', false, '[]'::jsonb, false, '[]'::jsonb, 1, 'PM.03', 'ALTO', 'CRITICO', 7, 7, 5.00, 'P', 'SRV-DB-HOSPITAL'),

-- ACT-103: Portal SISADMISION -> Vinculado a PM.01 (Formación Académica Integral, id=5)
(103, NOW(), NOW(), false, NULL, 'SYS-SISADMIS', 'Portal Web SISADMISION y Banco de Postulantes',
 'Plataforma web donde los postulantes ingresan datos personales, fotos y huellas dactilares para exámenes de admisión.',
 'Dirección Universitaria de Admisión (DUA)', 'Área de Desarrollo OTI', 'Servidores DMZ OTI (admision.unsa.edu.pe)',
 true, 'APPLICATION', 'CONFIDENCIAL', 'PERIODICA', 'ALTA', 'ALTA', 'ALTA',
 1.00, 1.00, 1.00, 'Inscripción, asignación de aulas y verificación de identidad anti-suplantación en admisión.',
 '["IDENTIFICACION", "BIOMETRICO_HUELLA", "FOTOGRAFIA", "COLEGIO_ORIGEN", "CONTACTO"]'::jsonb, 'CONTROLLER',
 '["WAF_FORTINET", "HTTPS_TLS_1_3", "HASH_ARGON2ID"]'::jsonb,
 'Consentimiento del Postulante / Reglamento de Admisión', 'Inscripción y evaluación de postulantes a la UNSA.',
 'Portal web admision.unsa.edu.pe', 'Registro directo en línea por el postulante',
 'Validación de identidad y publicación de resultados', '1 año para no ingresantes / Permanente para ingresantes',
 'Eliminación y purga periódica en base de datos', false, '[]'::jsonb, false, '[]'::jsonb, 0, 'PM.01', 'MEDIO', 'ALTO', 1, 5, 4.50, 'P', 'APP-ADMISION-01'),

-- ACT-104: Google Workspace for Education -> Vinculado a PA.05 (Gestión de TIC, id=12)
(104, NOW(), NOW(), false, NULL, 'CLOUD-GSUITE', 'Google Workspace for Education Fundamentals (@unsa.edu.pe)',
 'Servicio en la nube de Google LLC para correo electrónico institucional, Google Drive, Classroom y Meet.',
 'OTI UNSA', 'Google LLC (Encargado) / OTI', 'Centros de Datos Google Cloud (EE.UU. e Irlanda)',
 true, 'CLOUD_SERVICE', 'CONFIDENCIAL', 'CONTINUA', 'ALTA', 'ALTA', 'ALTA',
 1.00, 1.00, 1.00, 'Comunicación universitaria oficial, almacenamiento de archivos colaborativos y clases virtuales.',
 '["IDENTIFICACION", "CORREO_ELECTRONICO", "ARCHIVOS_DRIVE", "MENSAJERIA"]'::jsonb, 'PROCESSOR',
 '["CONTRATO_DPA", "CIFRADO_TRANSITO_TLS", "MFA_OBLIGATORIO"]'::jsonb,
 'Contrato de Servicios Cloud / Ley 29733 Art. 15 y 17', 'Comunicaciones institucionales y almacenamiento educativo.',
 'Aprovisionamiento automatizado desde SISUNSA', 'Sincronización de cuentas por OTI',
 'Gestión de clases y mensajería oficial', 'Durante la vinculación académica o laboral con la UNSA',
 'Eliminación lógica de cuenta y purga definitiva a los 6 meses de inactividad', true, '[]'::jsonb, true,
 '{"recipient": "Google LLC", "country": "EE.UU.", "international_framework": "Cláusulas Contractuales Tipo (SCC)"}'::jsonb,
 0, 'PA.05', 'ALTO', 'ALTO', 3, 12, 4.80, 'P', 'CLOUD-WORKSPACE'),

-- ACT-105: Aula Virtual Moodle -> Vinculado a PM.01 (Formación Académica Integral, id=5)
(105, NOW(), NOW(), false, NULL, 'APP-MOODLE', 'Plataforma Aula Virtual Moodle UNSA',
 'Sistema de gestión de aprendizaje (LMS) donde se evalúa a los alumnos y se registran tareas de pregrado y posgrado.',
 'Dirección Universitaria de Tecnologías Educativas (DUTE)', 'Área de Servidores OTI', 'Cluster Virtualizado OTI (aulavirtual.unsa.edu.pe)',
 true, 'APPLICATION', 'CONFIDENCIAL', 'CONTINUA', 'MEDIA', 'ALTA', 'ALTA',
 1.00, 1.00, 1.00, 'Desarrollo de cursos virtuales, entrega de tareas y evaluaciones académicas en línea.',
 '["IDENTIFICACION", "EVALUACIONES", "TAREAS", "FOROS", "DIRECCIONES_IP"]'::jsonb, 'CONTROLLER',
 '["AUTENTICACION_GOOGLE_OAUTH", "HTTPS", "BACKUP_DIARIO"]'::jsonb,
 'Contrato de Matrícula Universitaria', 'Impartición de sesiones de clase virtuales.',
 'Sincronización semestral de listas de alumnos desde SISUNSA', 'Integración por API',
 'Evaluación del aprendizaje universitario', '5 años tras la conclusión del semestre lectivo',
 'Backup histórico inmutable y compactación de cursos antiguos', false, '[]'::jsonb, false, '[]'::jsonb, 0, 'PM.01', 'MEDIO', 'ALTO', 4, 5, 4.00, 'P', 'LMS-MOODLE-01'),

-- ACT-106: Archivo Central Documental -> Vinculado a PA.08 (Gestión Documentaria y Archivo, id=15)
(106, NOW(), NOW(), false, NULL, 'ARCH-SANAGUSTIN', 'Archivo Central Físico de Grados, Títulos y Actas Históricas',
 'Repositorio documental físico que custodia actas de notas originales, resoluciones rectorales y legajos de títulos.',
 'Secretaría General UNSA', 'Jefatura de Archivo Central', 'Calle San Agustín N° 115, Cercado de Arequipa',
 true, 'PHYSICAL_ARCHIVE', 'CONFIDENCIAL', 'DIARIA', 'ALTA', 'ALTA', 'MEDIA',
 1.00, 1.00, 1.00, 'Custodia probatoria de grados académicos, títulos profesionales y actas históricas.',
 '["IDENTIFICACION", "TITULOS_PROFESIONALES", "ACTAS_NOTAS_ORIGINALES", "RESOLUCIONES"]'::jsonb, 'CONTROLLER',
 '["CONTROL_ACCESO_BIOMETRICO", "EXTINTORES_GAS_LIMPIO", "CCTV_24_7"]'::jsonb,
 'Ley Nacional de Archivos / Ley Universitaria 30220', 'Custodia de documentos con valor legal probatorio permanente.',
 'Mesa de partes presencial y convalidaciones', 'Ingreso físico de expedientes en papel',
 'Verificación de autenticidad de grados y títulos', 'Permanente / Histórico',
 'Conservación permanente según tabla de retención documental del Archivo General de la Nación', false, '[]'::jsonb, false, '[]'::jsonb, 0, 'PA.08', 'ALTO', 'ALTO', 6, 15, 4.50, 'P', 'ARCH-CENTRAL-01'),

-- ACT-107: TRAMITED (Mesa de Partes Virtual) -> Vinculado a PA.08 (Gestión Documentaria y Archivo, id=15)
(107, NOW(), NOW(), false, NULL, 'APP-TRAMITED', 'Sistema de Trámite Documentario Electrónico (TRAMITED)',
 'Sistema web para la recepción y seguimiento de expedientes con Código Único de Trámite (CUT) y solicitudes ARCO.',
 'Secretaría General / Mesa de Partes', 'Área de Sistemas OTI', 'Servidores Web OTI (ouis.unsa.edu.pe/tramited/)',
 true, 'APPLICATION', 'CONFIDENCIAL', 'CONTINUA', 'ALTA', 'ALTA', 'ALTA',
 1.00, 1.00, 1.00, 'Recepción de trámites universitarios, solicitudes de acceso a la información y ejercicio de derechos ARCO.',
 '["IDENTIFICACION", "DNI", "DOMICILIO", "CORREO", "TELEFONO", "SOLICITUDES_ARCO"]'::jsonb, 'CONTROLLER',
 '["FIRMA_DIGITAL_RENIEC", "HTTPS", "FOLIO_ELECTRONICO_INALTERABLE"]'::jsonb,
 'Ley 27444 del Procedimiento Administrativo General / Ley 29733', 'Gestión de expedientes y solicitudes de ciudadanos y alumnos.',
 'Portal web ouis.unsa.edu.pe/tramited/ y ventanilla presencial', 'Ingreso directo por el interesado',
 'Trámite administrativo y respuesta a solicitudes formales', '10 años según normativa de trámite documentario',
 'Microarchivo digital y purga de expedientes concluidos', false, '[]'::jsonb, false, '[]'::jsonb, 0, 'PA.08', 'ALTO', 'ALTO', 6, 15, 4.20, 'P', 'APP-TRAMITED-01'),

-- ACT-108: UNSApay / Recaudo -> Vinculado a PA.01 (Gestión Financiera y Contable, id=8)
(108, NOW(), NOW(), false, NULL, 'APP-UNSAPAY', 'Pasarela de Recaudación de Tasas (Convenio Banco de la Nación)',
 'Módulo de recaudación de tasas de matrícula, certificados y trámites mediante convenio Págalo.pe y Caja Central.',
 'Unidad de Tesorería / OTI', 'Área de Desarrollo OTI', 'Plataforma estatal pagalo.pe y ventanillas de Tesorería',
 true, 'APPLICATION', 'CONFIDENCIAL', 'CONTINUA', 'ALTA', 'ALTA', 'ALTA',
 1.00, 1.00, 1.00, 'Recaudación de ingresos por tasas universitarias y validación bancaria con Págalo.pe.',
 '["IDENTIFICACION", "NUMERO_OPERACION", "MONTO", "CODIGO_PAGO_BN"]'::jsonb, 'CONTROLLER',
 '["TOKENIZACION_PASARELA", "HTTPS_TLS_1_3", "POLITICA_NO_STORAGE_CVV"]'::jsonb,
 'Ley General del Sistema Nacional de Tesorería', 'Control de recaudación de recursos directamente recaudados (RDR).',
 'Portal pagalo.pe (tasa 01540) o ventanilla Banco de la Nación', 'Pago en línea con tarjeta o ventanilla bancaria',
 'Conciliación bancaria y emisión de boleta electrónica', '10 años por normativa contable y tributaria SUNAT',
 'Destrucción segura y archivo tributario electrónico', false, '[]'::jsonb, false, '[]'::jsonb, 0, 'PA.01', 'ALTO', 'CRITICO', 1, 8, 4.30, 'P', 'APP-UNSAPAY-01'),

-- ACT-109: SISTUTORIA -> Vinculado a PM.01 (Formación Académica Integral, id=5)
(109, NOW(), NOW(), false, NULL, 'APP-SISTUTORIA', 'Sistema de Tutoría y Acompañamiento Psicopedagógico',
 'Módulo de seguimiento y entrevistas de tutoría académica y psicopedagógica para estudiantes.',
 'Dirección Universitaria de Tutoría', 'Área de Sistemas OTI', 'Módulo interno en extranet.unsa.edu.pe/sisacad y VRA',
 true, 'APPLICATION', 'SECRETO', 'PERIODICA', 'ALTA', 'ALTA', 'MEDIA',
 1.00, 1.00, 1.00, 'Registro de fichas psicopedagógicas, problemas familiares y seguimiento del rendimiento estudiantil.',
 '["IDENTIFICACION", "SALUD_MENTAL", "SITUACION_FAMILIAR", "RENDIMIENTO_RIESGO", "DATOS_SENSIBLES"]'::jsonb, 'CONTROLLER',
 '["CONTROL_ACCESO_ESTRICTO", "ACCESO_SOLO_TUTOR_ASIGNADO"]'::jsonb,
 'Ley Universitaria 30220 Art. 69 / Ley 29733 Art. 13', 'Acompañamiento psicopedagógico y prevención de deserción estudiantil.',
 'Entrevistas de tutoría presencial o virtual', 'Llenado por el docente tutor asignado',
 'Orientación psicológica y soporte académico', 'Durante la permanencia del estudiante en la facultad',
 'Anonimización y borrado seguro de fichas socio-afectivas', false, '[]'::jsonb, false, '[]'::jsonb, 0, 'PM.01', 'MEDIO', 'ALTO', 4, 5, 3.90, 'P', 'APP-TUTORIA-01'),

-- ACT-110: SISCOM -> Vinculado a PA.06 (Gestión del Bienestar Universitario, id=13)
(110, NOW(), NOW(), false, NULL, 'APP-SISCOM', 'Sistema de Control de Comedor Universitario (DUDE)',
 'Sistema interno para la asignación de becas de comedor y control de entrega de raciones con carnet/biometría.',
 'Dirección Universitaria de Desarrollo Estudiantil (DUDE)', 'Área de Sistemas OTI', 'Red interna de comedores universitarios DUDE (Campus Ingenierías, Sociales, Biomédicas)',
 true, 'APPLICATION', 'CONFIDENCIAL', 'DIARIA', 'MEDIA', 'ALTA', 'ALTA',
 1.00, 1.00, 1.00, 'Asignación de becas alimentarias y registro de raciones diarias en comedores universitarios.',
 '["IDENTIFICACION", "EVALUACION_SOCIOECONOMICA", "NIVEL_POBREZA_SISFOH", "REGISTRO_ASISTENCIA"]'::jsonb, 'CONTROLLER',
 '["CONTROL_ACCESO_RBAC", "HTTPS"]'::jsonb,
 'Estatuto UNSA / Ley Universitaria 30220', 'Otorgamiento de bienestar estudiantil y becas alimentarias.',
 'Ficha socioeconómica del postulante al comedor', 'Evaluación por trabajadora social',
 'Control diario de comensales en comedores de campus', '3 años tras finalizar la beca',
 'Purga periódica de registros de asistencia diaria', false, '[]'::jsonb, false, '[]'::jsonb, 0, 'PA.06', 'MEDIO', 'MEDIO', 2, 13, 3.50, 'P', 'APP-SISCOM-01')
ON CONFLICT (id) DO UPDATE
SET code = EXCLUDED.code, name = EXCLUDED.name, description = EXCLUDED.description, location = EXCLUDED.location,
    purpose = EXCLUDED.purpose, data_categories = EXCLUDED.data_categories, legal_basis = EXCLUDED.legal_basis;


-- 8. PERMISOS FUNCIONALES DE GRUPOS Y USUARIOS (demo.auth_group_permissions y demo.auth_user_user_permissions)
INSERT INTO demo.auth_group_permissions (id, group_id, permission_id)
VALUES
(1, 1, 1),
(2, 2, 2),
(3, 3, 3),
(4, 4, 4),
(5, 5, 5),
(6, 6, 6),
(7, 7, 7),
(8, 8, 8),
(9, 9, 9)
ON CONFLICT (id) DO NOTHING;

INSERT INTO demo.auth_user_user_permissions (id, user_id, permission_id)
VALUES
(1, 1, 1)
ON CONFLICT (id) DO NOTHING;

-- 9. CONFIGURACIÓN DE PLATAFORMA Y LICENCIA GLOBAL (Esquema public)
INSERT INTO public.auth_group (id, name)
VALUES (1, 'Superadministradores de Plataforma')
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.auth_user (id, password, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined)
VALUES (1, 'pbkdf2_sha256$600000$unsa_hash_superadmin$xyz987', true, 'superadmin', 'Administrador', 'Plataforma PIMS', 'soporte.pims@unsa.edu.pe', true, true, NOW())
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.auth_user_groups (id, user_id, group_id)
VALUES (1, 1, 1)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.auth_group_permissions (id, group_id, permission_id)
VALUES (1, 1, 1)
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.auth_user_user_permissions (id, user_id, permission_id)
VALUES (1, 1, 1)
ON CONFLICT (id) DO NOTHING;

-- Licencia de la plataforma asignada a la UNSA (client_id=2, Empresa Demo / UNSA)
INSERT INTO public.customer_license (id, start_date, end_date, status, notes, created_at, updated_at, client_id, created_by_id)
VALUES (1, '2026-01-01', '2026-12-31', 'A', 'Licencia Institucional PIMS Enterprise - Universidad Nacional de San Agustín de Arequipa', NOW(), NOW(), 2, 1)
ON CONFLICT (id) DO UPDATE SET notes = EXCLUDED.notes, status = EXCLUDED.status;

-- Log de aprovisionamiento de plataforma y tenant
INSERT INTO public.customer_platformlog (id, action, detail, created_at, target_client_id, user_id)
VALUES (1, 'APROVISIONAMIENTO_TENANT', '{"tenant": "UNSA", "esquema": "demo", "modulos": ["RAT", "RIESGOS", "SOA", "AUDITORIA", "ARCO", "INCIDENTES", "TERCEROS", "CAPACITACION"]}'::jsonb, NOW(), 2, 1)
ON CONFLICT (id) DO NOTHING;

-- Registro de auditoría administrativa web inicial
INSERT INTO public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id)
VALUES (1, NOW(), '2', 'Empresa Demo (UNSA)', 1, '[{"added": {}}]', 1, 1)
ON CONFLICT (id) DO NOTHING;

-- Registro de sesión inicial
INSERT INTO public.django_session (session_key, session_data, expire_date)
VALUES ('unsa_pims_session_admin_0001', 'e30:1tbXYZ:initial_seed_session_data', NOW() + INTERVAL '30 days')
ON CONFLICT (session_key) DO NOTHING;
