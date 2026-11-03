"""
Enumeraciones de Dominio (Domain Enums).
Sin dependencias externas ni de infraestructura.
"""

from enum import Enum


class CategoriaDatoLPDP(str, Enum):
    DATOS_SALUD = "DATOS_SALUD"
    CREDENCIALES_ACCESO = "CREDENCIALES_ACCESO"
    DATOS_FINANCIEROS = "DATOS_FINANCIEROS"
    DATOS_IDENTIFICACION = "DATOS_IDENTIFICACION"
    DATOS_GENERALES = "DATOS_GENERALES"
    NO_SENSIBLE = "NO_SENSIBLE"


class NivelRiesgo(str, Enum):
    CRITICO = "CRÍTICO"
    ALTO = "ALTO"
    MEDIO = "MEDIO"
    LEVE = "LEVE"


class EstadoHallazgo(str, Enum):
    PENDIENTE = "PENDIENTE"
    REMEDIADO = "REMEDIADO"
    MITIGADO = "MITIGADO"
    EN_OBSERVACION = "EN_OBSERVACION"


class TipoHallazgo(str, Enum):
    TECNICO = "TECNICO"
    DOCUMENTAL = "DOCUMENTAL"


class TipoArchivo(str, Enum):
    SQL = "SQL"
    PDF = "PDF"
    MARKDOWN = "MARKDOWN"
    TEXTO = "TEXTO"
    OTRO = "OTRO"
