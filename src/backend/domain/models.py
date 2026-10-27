"""
Modelos de Entidad del Dominio (Pure Domain Models).
Modelos estructurados con Pydantic para tipado, validación y serialización.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from .enums import CategoriaDatoLPDP, NivelRiesgo, EstadoHallazgo, TipoArchivo


class ArchivoCargado(BaseModel):
    id: Optional[int] = None
    nombre_archivo: str
    tipo_archivo: str
    fecha_carga: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    tamano_bytes: Optional[int] = 0
    resumen_analisis: Optional[str] = None


class ActivoColumna(BaseModel):
    id: Optional[int] = None
    archivo_id: Optional[int] = None
    nombre_tabla: str
    nombre_columna: str
    tipo_sql: str
    es_clave_primaria: bool = False
    es_clave_foranea: bool = False
    categoria_sensible: str = CategoriaDatoLPDP.NO_SENSIBLE.value
    es_dato_sensible: bool = False
    nivel_confianza: float = 1.0
    candado_deteccion: Optional[str] = None
    recomendacion_seguridad: Optional[str] = None


class ClausulaDocumento(BaseModel):
    id: Optional[int] = None
    archivo_id: Optional[int] = None
    documento: str
    numero_clausula: Optional[str] = None
    titulo_clausula: Optional[str] = None
    texto_clausula: str
    tipo_clausula: Optional[str] = None
    estado_cumplimiento: str = "OBSERVADO"
    alerta_legal: Optional[str] = None


class HallazgoAudit(BaseModel):
    id: Optional[int] = None
    codigo_regla: str
    titulo: str
    descripcion: str
    nivel_riesgo: str = NivelRiesgo.MEDIO.value
    elemento_afectado: str
    origen_archivo: str
    control_iso27701: str
    principio_iso29100: str
    articulo_ley29733: str
    directiva_seguridad: str
    multa_estimada_uit: float
    multa_estimada_pen: float
    precedente_anpd: str
    estado: str = EstadoHallazgo.PENDIENTE.value
    fecha_deteccion: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class InteraccionCoach(BaseModel):
    id: Optional[int] = None
    hallazgo_id: int
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    rol: str
    mensaje: str
    pensamiento_reasoning: Optional[str] = None
    parche_sql: Optional[str] = None


class DictamenPericial(BaseModel):
    content: str
    reasoning: Optional[str] = ""
    sql_patch: Optional[str] = ""
    mode: str = "openrouter"
    regla_canonica: Optional[Dict[str, Any]] = None
    evaluacion_critica: Optional[Dict[str, Any]] = None
