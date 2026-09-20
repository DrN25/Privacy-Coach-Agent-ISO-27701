-- ==============================================================================
-- SISTEMA DE GESTIÓN CLÍNICA - SALUDTOTAL S.A.C.
-- Esquema de Base de Datos Relacional (PostgreSQL / MySQL DDL)
-- Versión: 2.1.4 (Producción MYPE)
-- Nota de Auditoría: Esquema bajo revisión de cumplimiento Ley N.° 29733 e ISO/IEC 27701
-- ==============================================================================

CREATE TABLE IF NOT EXISTS usuarios_sistema (
    id_usuario SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    -- VULNERABILIDAD R-002: Hash MD5 débil sin sal (salt) y susceptible a colisiones
    password_hash VARCHAR(32) NOT NULL,
    nombre_completo VARCHAR(120) NOT NULL,
    rol VARCHAR(30) NOT NULL DEFAULT 'RECEPCIONISTA', -- MEDICO, ENFERMERO, RECEPCIONISTA, ADMIN
    correo_corporativo VARCHAR(100) NOT NULL,
    estado VARCHAR(15) DEFAULT 'ACTIVO',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pacientes (
    id_paciente SERIAL PRIMARY KEY,
    tipo_documento VARCHAR(10) DEFAULT 'DNI',
    numero_documento VARCHAR(15) NOT NULL UNIQUE,
    nombres VARCHAR(80) NOT NULL,
    apellidos VARCHAR(80) NOT NULL,
    fecha_nacimiento DATE NOT NULL,
    sexo CHAR(1) CHECK (sexo IN ('M', 'F')),
    telefono_movil VARCHAR(20),
    correo_electronico VARCHAR(100),
    direccion_domicilio VARCHAR(200),
    -- Datos sensibles de salud almacenados directamente sin cifrado de columna
    grupo_sanguineo VARCHAR(5),
    alergias_graves TEXT,
    -- VULNERABILIDAD R-003: Almacenamiento de datos financieros críticos y CVV en texto claro
    tarjeta_credito_numero VARCHAR(19),
    tarjeta_credito_cvv VARCHAR(4),
    tarjeta_credito_expiracion VARCHAR(7),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medicos (
    id_medico SERIAL PRIMARY KEY,
    colegiatura_cmp VARCHAR(10) NOT NULL UNIQUE,
    nombres VARCHAR(80) NOT NULL,
    apellidos VARCHAR(80) NOT NULL,
    especialidad VARCHAR(80) NOT NULL,
    telefono_contacto VARCHAR(20)
);

CREATE TABLE IF NOT EXISTS historias_clinicas (
    id_historia SERIAL PRIMARY KEY,
    id_paciente INT NOT NULL REFERENCES pacientes(id_paciente),
    id_medico INT NOT NULL REFERENCES medicos(id_medico),
    fecha_atencion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- VULNERABILIDAD CRÍTICA R-001: Diagnóstico médico y serología en texto plano VARCHAR/TEXT
    -- Incumple Directiva de Seguridad R.D. 019-2013-JUS (Nivel Complejo) y Control B.2.2.1 ISO 27701
    diagnostico_cie10 VARCHAR(255) NOT NULL,
    antecedentes_patologicos TEXT,
    serologia_vih VARCHAR(20), -- POSITIVO / NEGATIVO en texto abierto
    tratamiento_farmacologico TEXT,
    observaciones_confidenciales TEXT
);

CREATE TABLE IF NOT EXISTS citas_medicas (
    id_cita SERIAL PRIMARY KEY,
    id_paciente INT NOT NULL REFERENCES pacientes(id_paciente),
    id_medico INT NOT NULL REFERENCES medicos(id_medico),
    fecha_hora TIMESTAMP NOT NULL,
    motivo_consulta VARCHAR(255),
    estado_cita VARCHAR(20) DEFAULT 'PROGRAMADA'
);
