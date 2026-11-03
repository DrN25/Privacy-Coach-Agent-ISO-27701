"""
Nodo Agente Perfilador (Data Profiler Agent).
Clasifica columnas y tipos de datos conforme a categorías de sensibilidad de la LPDP.
"""

from typing import Dict, Any, List
from .state import AuditState
from ..profiler import perfilar_columna
from ..infrastructure.repository import repository


def nodo_profiler_agent(state: AuditState) -> Dict[str, Any]:
    """Analiza y perfila las columnas asociadas al hallazgo o activos en revisión."""
    ctx = state.get("contexto_brecha", {})
    elemento = ctx.get("elemento_afectado", "")
    
    perfiles: List[Dict[str, Any]] = []
    if "." in elemento:
        partes = [p.strip() for p in elemento.split(",") if "." in p]
        for p in partes:
            if "." in p:
                tabla, col = p.split(".", 1)
                res = perfilar_columna(col.strip(), tabla.strip(), "VARCHAR")
                perfiles.append({
                    "tabla": res.nombre_tabla,
                    "columna": res.nombre_columna,
                    "categoria": res.categoria.value,
                    "sensible": res.es_sensible,
                    "candado": res.candado
                })

    # Si no vino elemento explícito con punto, recuperar activos de los hallazgos registrados
    if not perfiles:
        try:
            hallazgos = repository.obtener_todos_los_hallazgos()
            for h in hallazgos[:4]:
                elem = h.get("elemento_afectado", "")
                if "." in elem:
                    partes = [p.strip() for p in elem.split(",") if "." in p]
                    for p in partes:
                        if "." in p:
                            tabla, col = p.split(".", 1)
                            res = perfilar_columna(col.strip(), tabla.strip(), "VARCHAR")
                            perfiles.append({
                                "tabla": res.nombre_tabla,
                                "columna": res.nombre_columna,
                                "categoria": res.categoria.value,
                                "sensible": res.es_sensible,
                                "candado": res.candado
                            })
        except Exception:
            pass

    trace = list(state.get("trazabilidad") or [])
    trace.append({
        "paso": len(trace) + 1,
        "agente": "Data Profiler Agent",
        "accion": "Perfilado y categorización de sensibilidad PII",
        "detalle": f"Activos perfilados: {len(perfiles)} elementos. Sensibles: {len([p for p in perfiles if p.get('sensible')])}",
        "estado": "ok"
    })

    return {"perfil_activos": perfiles, "trazabilidad": trace}
