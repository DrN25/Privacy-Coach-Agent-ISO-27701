-- =============================================================================
-- SCRIPT MAESTRO DE CARGA: BASE DE DATOS PIMS UNSA
-- Orquestador de Ejecución Secuencial para los 8 Agentes de Privacidad
-- Universidad Nacional de San Agustín de Arequipa (UNSA)
-- =============================================================================

\echo '---------------------------------------------------------'
\echo '1. Cargando Cimientos Institucionales (Fase 0: Usuarios, Macroprocesos, Activos Ancla)...'
\i BD/00_cimientos_unsa.sql

\echo '---------------------------------------------------------'
\echo '2. Cargando Agente 1 (Inventario de Datos y RAT)...'
\i BD/equipos/01_inventario_datos.sql

\echo '---------------------------------------------------------'
\echo '3. Cargando Agente 2 (Evaluación y Tratamiento de Riesgos)...'
\i BD/equipos/02_evaluacion_riesgos.sql

\echo '---------------------------------------------------------'
\echo '4. Cargando Agente 3 (Controles y Declaración de Aplicabilidad SoA)...'
\i BD/equipos/03_controles_soa.sql

\echo '---------------------------------------------------------'
\echo '5. Cargando Agente 4 (Evidencia y Auditoría Interna OCI)...'
\i BD/equipos/04_evidencia_auditoria.sql

\echo '---------------------------------------------------------'
\echo '6. Cargando Agente 5 (Atención de Derechos ARCO y Consentimientos)...'
\i BD/equipos/05_derechos_dsar.sql

\echo '---------------------------------------------------------'
\echo '7. Cargando Agente 6 (Gestión de Incidentes y Brechas de PII)...'
\i BD/equipos/06_incidentes_brechas.sql

\echo '---------------------------------------------------------'
\echo '8. Cargando Agente 7 (Gestión Legal de Terceros y Contratos DPA)...'
\i BD/equipos/07_terceros_dpas.sql

\echo '---------------------------------------------------------'
\echo '9. Cargando Agente 8 (Formación y Concientización en Privacidad)...'
\i BD/equipos/08_formacion_conciencia.sql

\echo '---------------------------------------------------------'
\echo '¡PROCESO COMPLETADO! Toda la base de datos PIMS de la UNSA ha sido poblada con éxito.'

