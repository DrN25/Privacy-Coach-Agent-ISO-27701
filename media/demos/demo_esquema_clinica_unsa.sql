-- ============================================================================
-- Archivo de Demostración DSPM - UNSA PIMS Agente 6
-- Subir en: Módulo 3 "Inspector SQL / PDF" -> "+ Subir SQL / PDF / TXT"
-- Dispara reglas R-001 (Salud sin cifrar), R-002 (Hash MD5) y R-003 (CVV)
-- ============================================================================

CREATE TABLE pacientes_laboratorio (
    id INTEGER PRIMARY KEY,
    dni_paciente VARCHAR(12) NOT NULL,
    diagnostico_cie10 VARCHAR(255) NOT NULL,
    historia_clinica TEXT NOT NULL,
    fecha_atencion DATE NOT NULL
);

CREATE TABLE cuentas_portal_medico (
    id INTEGER PRIMARY KEY,
    correo_usuario VARCHAR(120) NOT NULL,
    password_md5 CHAR(32) NOT NULL,
    rol_acceso VARCHAR(40) NOT NULL
);

CREATE TABLE pagos_consulta_externa (
    id INTEGER PRIMARY KEY,
    referencia_orden VARCHAR(40) NOT NULL,
    tarjeta_pan VARCHAR(19) NOT NULL,
    codigo_cvv VARCHAR(4) NOT NULL,
    monto_pen NUMERIC(10, 2) NOT NULL
);
