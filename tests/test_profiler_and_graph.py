from backend.graph_engine import PIMSGraphEngine
from backend.profiler import CategoriaDatoLPDP, perfilar_columna


def test_profiler_classifies_sensitive_columns():
    health = perfilar_columna("diagnostico_cie10", "historias_clinicas", "VARCHAR(255)")
    password = perfilar_columna("password_hash", "usuarios", "VARCHAR(32)")

    assert health.categoria == CategoriaDatoLPDP.DATOS_SALUD
    assert health.es_sensible is True
    assert password.categoria == CategoriaDatoLPDP.CREDENCIALES_ACCESO


def test_normative_datasets_load_expected_coverage():
    engine = PIMSGraphEngine()

    assert len(engine.controls_map) == 78
    assert len(engine.principles_map) == 11
    assert len(engine.sanctions_dataset) == 588
    assert engine.get_control("A.3.24")["title"] == "Use of cryptography"
