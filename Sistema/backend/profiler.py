import re
from enum import Enum
from typing import Dict, Any, Tuple
from pydantic import BaseModel, Field

class CategoriaDatoLPDP(str, Enum):
    DATOS_SALUD = "DATOS_SALUD"
    DATOS_BIOMETRICOS = "DATOS_BIOMETRICOS"
    DATOS_ECONOMICOS = "DATOS_ECONOMICOS"
    DATOS_IDEOLOGIA_RELIGION = "DATOS_IDEOLOGIA_RELIGION"
    DATOS_VIDA_SEXUAL = "DATOS_VIDA_SEXUAL"
    DATOS_ORIGEN_RACIAL = "DATOS_ORIGEN_RACIAL"
    CREDENCIALES_ACCESO = "CREDENCIALES_ACCESO"
    DATOS_IDENTIFICACION = "DATOS_IDENTIFICACION"
    DATOS_COMUNES = "DATOS_COMUNES"

class PerfiladoColumna(BaseModel):
    nombre_columna: str
    nombre_tabla: str
    tipo_sql: str
    categoria: CategoriaDatoLPDP
    es_sensible: bool
    nivel_confianza: float = Field(ge=0.0, le=1.0)
    candado: str
    recomendacion: str

# Diccionario canónico de patrones de concordancia (Candado 1)
PATRONES_CANONICOS = {
    CategoriaDatoLPDP.DATOS_SALUD: [
        r"diagnostico", r"cie10", r"cie_10", r"vih", r"enfermedad", r"patolog",
        r"alergia", r"historia_clinica", r"tratamiento", r"serologia", r"grupo_sanguineo",
        r"receta", r"farmaco", r"examen_medico"
    ],
    CategoriaDatoLPDP.DATOS_BIOMETRICOS: [
        r"huella", r"facial", r"iris", r"biometr", r"voz", r"adn"
    ],
    CategoriaDatoLPDP.DATOS_ECONOMICOS: [
        r"tarjeta", r"cvv", r"tarjeta_credito", r"cuenta_bancaria", r"cci",
        r"salario", r"sueldo", r"ingreso", r"monto"
    ],
    CategoriaDatoLPDP.CREDENCIALES_ACCESO: [
        r"password", r"passwd", r"pwd", r"token", r"secret", r"hash", r"clave", r"pin"
    ],
    CategoriaDatoLPDP.DATOS_IDENTIFICACION: [
        r"dni", r"documento", r"numero_documento", r"nombres", r"apellidos",
        r"telefono", r"correo", r"email", r"direccion", r"fecha_nacimiento", r"sexo"
    ]
}

def perfilar_columna(columna: str, tabla: str, tipo_sql: str) -> PerfiladoColumna:
    col_lower = columna.lower()
    
    # Evaluación contra Candado 1 (Taxonomía Canónica Cerrada)
    for cat, regex_list in PATRONES_CANONICOS.items():
        for reg in regex_list:
            if re.search(reg, col_lower):
                es_sensible = cat in [
                    CategoriaDatoLPDP.DATOS_SALUD,
                    CategoriaDatoLPDP.DATOS_BIOMETRICOS,
                    CategoriaDatoLPDP.DATOS_IDEOLOGIA_RELIGION,
                    CategoriaDatoLPDP.DATOS_VIDA_SEXUAL,
                    CategoriaDatoLPDP.DATOS_ORIGEN_RACIAL,
                    CategoriaDatoLPDP.CREDENCIALES_ACCESO,
                    CategoriaDatoLPDP.DATOS_ECONOMICOS
                ]
                
                recom = "Dato conforme."
                if cat == CategoriaDatoLPDP.DATOS_SALUD:
                    recom = "Exige cifrado en reposo obligatorio (Directiva de Seguridad Nivel Complejo) y control B.2.2.1 ISO 27701."
                elif cat == CategoriaDatoLPDP.CREDENCIALES_ACCESO:
                    recom = "Requiere función hash robusta con sal única (Argon2id o bcrypt); prohibido MD5/SHA1."
                elif cat == CategoriaDatoLPDP.DATOS_ECONOMICOS:
                    recom = "Prohibido almacenar CVV de tarjeta tras procesar autorización (PCI-DSS y LPDP)."
                
                return PerfiladoColumna(
                    nombre_columna=columna,
                    nombre_tabla=tabla,
                    tipo_sql=tipo_sql,
                    categoria=cat,
                    es_sensible=es_sensible,
                    nivel_confianza=0.98,
                    candado="Candado 1: Taxonomía Canónica + Regex Cerrada",
                    recomendacion=recom
                )
    
    return PerfiladoColumna(
        nombre_columna=columna,
        nombre_tabla=tabla,
        tipo_sql=tipo_sql,
        categoria=CategoriaDatoLPDP.DATOS_COMUNES,
        es_sensible=False,
        nivel_confianza=0.85,
        candado="Candado 1: Regla General",
        recomendacion="Tratamiento estándar conforme a finalidad informada."
    )
