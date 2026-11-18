-- =============================================================================
-- ESQUEMA REPRESENTATIVO DE SERVICIOS CENTRALES DE LA UNSA
-- Activos Auditados: SISADMISION, Hospital Zamácola, UNSApay y Matrícula
-- =============================================================================

CREATE TABLE hospital_historias_clinicas (
    id SERIAL PRIMARY KEY,
    paciente_dni VARCHAR(8) NOT NULL,
    paciente_nombres VARCHAR(150) NOT NULL,
    diagnostico_cie10 VARCHAR(10) NOT NULL,
    descripcion_diagnostico TEXT NOT NULL,
    tratamiento_prescrito TEXT NOT NULL,
    datos_sensibles_salud VARCHAR(500) NOT NULL,
    fecha_atencion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE admision_postulantes (
    id SERIAL PRIMARY KEY,
    dni VARCHAR(8) UNIQUE NOT NULL,
    nombres_completos VARCHAR(200) NOT NULL,
    correo_personal VARCHAR(100) NOT NULL,
    password_hash VARCHAR(32) NOT NULL,
    huella_dactilar_template TEXT,
    foto_biometrica BYTEA,
    proceso_admision VARCHAR(20) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tesoreria_pagos_online (
    id SERIAL PRIMARY KEY,
    codigo_estudiante VARCHAR(10) NOT NULL,
    numero_transaccion VARCHAR(30) UNIQUE NOT NULL,
    monto_abonado NUMERIC(10, 2) NOT NULL,
    tarjeta_pan VARCHAR(19) NOT NULL,
    tarjeta_cvv VARCHAR(4) NOT NULL,
    tarjeta_expira VARCHAR(5) NOT NULL,
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE matricula_alumnos (
    id SERIAL PRIMARY KEY,
    cui VARCHAR(8) UNIQUE NOT NULL,
    nombres_alumno VARCHAR(150) NOT NULL,
    semestre_academico VARCHAR(10) NOT NULL,
    acepta_cesion_publicidad BOOLEAN DEFAULT TRUE NOT NULL,
    fecha_matricula TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE servicios_cloud_transfronterizo (
    id SERIAL PRIMARY KEY,
    nombre_servicio VARCHAR(100) NOT NULL,
    region_cloud_aws VARCHAR(50) NOT NULL,
    url_bucket_s3 VARCHAR(255) NOT NULL,
    tipo_datos_transferidos VARCHAR(100) NOT NULL,
    fecha_sincronizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
