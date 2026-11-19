from backend.domain.enums import CategoriaDatoLPDP, NivelRiesgo, EstadoHallazgo, TipoHallazgo
from backend.domain.models import HallazgoAudit, ActivoColumna, DictamenPericial


def test_domain_enums_values():
    assert CategoriaDatoLPDP.DATOS_SALUD.value == "DATOS_SALUD"
    assert NivelRiesgo.CRITICO.value == "CRÍTICO"
    assert EstadoHallazgo.PENDIENTE.value == "PENDIENTE"
    assert TipoHallazgo.TECNICO.value == "TECNICO"


def test_domain_models_creation():
    hallazgo = HallazgoAudit(
        codigo_regla="R-001",
        titulo="Datos de Salud sin Cifrado",
        descripcion="Prueba",
        elemento_afectado="pacientes.diagnostico",
        origen_archivo="schema.sql",
        control_iso27701="A.3.24",
        principio_iso29100="Principle 7",
        articulo_ley29733="Art. 38",
        directiva_seguridad="R.D. 019-2013-JUS",
        multa_estimada_uit=12.5,
        multa_estimada_pen=64375.0,
        precedente_anpd="Res. 042-2023",
    )
    assert hallazgo.codigo_regla == "R-001"
    assert hallazgo.multa_estimada_uit == 12.5
    assert hallazgo.estado == EstadoHallazgo.PENDIENTE.value

    col = ActivoColumna(
        nombre_tabla="pacientes",
        nombre_columna="diagnostico",
        tipo_sql="VARCHAR(255)",
        es_dato_sensible=True,
        categoria_sensible=CategoriaDatoLPDP.DATOS_SALUD.value,
    )
    assert col.nombre_tabla == "pacientes"
    assert col.es_dato_sensible is True
