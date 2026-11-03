"""
Definición del Estado Tipado (State) compartido para LangGraph.
"""

from typing import TypedDict, List, Dict, Any, Optional


class AuditState(TypedDict, total=False):
    # Enrutamiento e intención
    intencion: str  # 'dictamen', 'normativo', 'remediacion', 'contexto', 'general'
    
    # Entradas de usuario y contexto
    historial_mensajes: List[Dict[str, str]]
    contexto_brecha: Dict[str, Any]
    
    # Datos recuperados por agentes especialistas
    contexto_empresa: Dict[str, Any]
    perfil_activos: List[Dict[str, Any]]
    hallazgos_detectados: List[Dict[str, Any]]
    regla_canonica: Dict[str, Any]
    subgrafo_normativo: Dict[str, Any]
    precedentes_anpd: List[Dict[str, Any]]
    contexto_unsa: Dict[str, Any]
    expediente_texto: str
    
    # Salidas periciales y código
    dictamen: str
    razonamiento: str
    parche_sql: str
    
    # Trazabilidad y auditoría de ejecución multi-agente
    trazabilidad: List[Dict[str, Any]]
    
    # Control de calidad y bucle de reflexión
    evaluacion_critica: Dict[str, Any]
    iteracion: int
    aprobado: bool
    modo: str
