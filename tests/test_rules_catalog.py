import pytest
from backend.core.rules_catalog import (
    CATALOGO_REGLAS,
    obtener_regla,
    resolver_regla_con_fallback,
    listar_todas_las_reglas,
    VALOR_UIT_PEN,
)
from backend.router import resolver_enrutamiento, ROUTER_MAP


def test_catalogo_contiene_siete_reglas_canonicas():
    assert len(CATALOGO_REGLAS) == 7
    reglas_esperadas = {"R-001", "R-002", "R-003", "R-004", "R-005", "R-006", "R-007"}
    assert set(CATALOGO_REGLAS.keys()) == reglas_esperadas


@pytest.mark.parametrize("codigo", ["R-001", "R-002", "R-003", "R-004", "R-005", "R-006", "R-007"])
def test_estructura_regla_valida(codigo):
    regla = obtener_regla(codigo)
    assert regla is not None
    assert regla["codigo"] == codigo
    assert regla["nivel_riesgo"] in {"CRÍTICO", "ALTO", "MEDIO", "LEVE"}
    assert regla["control_iso27701"].startswith("A.")
    assert regla["multa_estimada_uit"] > 0
    assert regla["multa_estimada_pen"] == pytest.approx(regla["multa_estimada_uit"] * VALOR_UIT_PEN)
    assert regla["precedente_anpd"]
    assert regla["tipo_hallazgo"] in {"TECNICO", "DOCUMENTAL"}


def test_fallback_regla_desconocida():
    regla = resolver_regla_con_fallback("R-999")
    assert regla["codigo"] == "R-999"
    assert regla["nivel_riesgo"] == "MEDIO"
    assert regla["multa_estimada_uit"] == 3.0


def test_compatibilidad_router_antiguo():
    assert ROUTER_MAP == CATALOGO_REGLAS
    res = resolver_enrutamiento("R-001")
    assert res["codigo"] == "R-001"
    assert res["control_iso27701"] == "A.3.26"
    assert obtener_regla("R-002")["control_iso27701"] == "A.3.23"
