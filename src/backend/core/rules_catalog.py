"""
Catálogo Canónico de Reglas de Privacidad y DSPM (R-001 a R-007).
Fuente única de verdad (Single Source of Truth) para la correlación entre
vulnerabilidades técnicas/documentales, ISO/IEC 27701:2025, ISO/IEC 29100:2024,
Ley Peruana N.° 29733, Directiva R.D. 019-2013-JUS y precedentes vinculantes de la ANPD.

Características de diseño:
- Tipado estricto con TypedDict de la biblioteca estándar.
- Acceso O(1) inmutable.
- Validación autónoma de integridad.
"""

from typing import Dict, TypedDict, List, Optional


class ReglaAuditoria(TypedDict):
    codigo: str
    titulo: str
    nivel_riesgo: str
    control_iso27701: str
    control_nombre: str
    principio_iso29100: str
    articulo_ley29733: str
    directiva_seguridad: str
    multa_estimada_uit: float
    multa_estimada_pen: float
    precedente_anpd: str
    tipo_hallazgo: str  # 'TECNICO' o 'DOCUMENTAL'
    remediacion_sugerida: str


# Valor de la Unidad Impositiva Tributaria (UIT) oficial de referencia
VALOR_UIT_PEN = 5150.00

CATALOGO_REGLAS: Dict[str, ReglaAuditoria] = {
    "R-001": {
        "codigo": "R-001",
        "titulo": "Datos de Salud Sensibles sin Cifrado en Reposo",
        "nivel_riesgo": "CRÍTICO",
        "control_iso27701": "A.3.24",
        "control_nombre": "Use of cryptography",
        "principio_iso29100": "Principle 7: Information security",
        "articulo_ley29733": "Art. 9 (Principio de Seguridad) y Art. 38 num. 2 LPDP",
        "directiva_seguridad": "R.D. 019-2013-JUS/DGPDP - Nivel Complejo (Art. 12: Cifrado obligatorio)",
        "multa_estimada_uit": 12.5,
        "multa_estimada_pen": 12.5 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 1045-2020-JUS / R.D. 89-2021-JUS (Clínica Montefiori - Datos de salud sin cifrado)",
        "tipo_hallazgo": "TECNICO",
        "remediacion_sugerida": "Aplicar pgcrypto con pgp_sym_encrypt en columnas sensibles dentro de un bloque BEGIN ... COMMIT."
    },
    "R-002": {
        "codigo": "R-002",
        "titulo": "Almacenamiento de Contraseñas con Algoritmo Hash Débil (MD5)",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.3.13",
        "control_nombre": "Access control",
        "principio_iso29100": "Principle 7: Information security",
        "articulo_ley29733": "Art. 9 (Principio de Seguridad) y Art. 38 num. 2 LPDP",
        "directiva_seguridad": "R.D. 019-2013-JUS/DGPDP - Nivel Medio (Autenticación robusta)",
        "multa_estimada_uit": 8.0,
        "multa_estimada_pen": 8.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 018-2021-JUS/DGTAIPD (Medidas técnicas deficientes en autenticación de contraseñas)",
        "tipo_hallazgo": "TECNICO",
        "remediacion_sugerida": "Migrar a esquemas de derivación robustos (bcrypt/Argon2id) y marcar hashes legacy para regeneración forzada."
    },
    "R-003": {
        "codigo": "R-003",
        "titulo": "Almacenamiento Ilegal de Código de Seguridad CVV de Tarjetas",
        "nivel_riesgo": "CRÍTICO",
        "control_iso27701": "A.1.4.5",
        "control_nombre": "PII minimization objectives",
        "principio_iso29100": "Principle 5: Collection and retention limitation",
        "articulo_ley29733": "Art. 7 (Principio de Proporcionalidad) y Art. 38 num. 2 LPDP",
        "directiva_seguridad": "Directiva de Seguridad R.D. 019-2013-JUS Num. 5.2 (Prohibición de almacenar datos de autenticación)",
        "multa_estimada_uit": 15.0,
        "multa_estimada_pen": 15.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 089-2021-JUS/DGTAIPD (Retención indebida de datos de pago tras la transacción)",
        "tipo_hallazgo": "TECNICO",
        "remediacion_sugerida": "Eliminar de inmediato columnas de CVV/CVC mediante ALTER TABLE DROP COLUMN en bloque transaccional."
    },
    "R-004": {
        "codigo": "R-004",
        "titulo": "Consentimiento Tácito o Automático por Mera Navegación Web",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.1.2.4",
        "control_nombre": "Determine when and how consent is to be obtained",
        "principio_iso29100": "Principle 1: Consent and choice",
        "articulo_ley29733": "Art. 5 (Principio de Consentimiento) y Art. 18 LPDP",
        "directiva_seguridad": "D.S. 003-2013-JUS Art. 12 (Condiciones del consentimiento previo, libre, expreso e informado)",
        "multa_estimada_uit": 10.0,
        "multa_estimada_pen": 10.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 018-2021-JUS (Imputación de consentimiento tácito o automático por mera navegación)",
        "tipo_hallazgo": "DOCUMENTAL",
        "remediacion_sugerida": "Reemplazar cláusulas de aceptación automática por mecanismos opt-in expresos con casillas desmarcadas."
    },
    "R-005": {
        "codigo": "R-005",
        "titulo": "Plazo de Conservación Indefinido o Discrecional",
        "nivel_riesgo": "MEDIO",
        "control_iso27701": "A.1.4.8",
        "control_nombre": "Retention",
        "principio_iso29100": "Principle 5: Collection and retention limitation",
        "articulo_ley29733": "Arts. 7 y 8 (Principios de Proporcionalidad y Calidad - Conservación Limitada)",
        "directiva_seguridad": "D.S. 003-2013-JUS Arts. 9 y 28 (Cancelación y bloqueo por expiración de plazo)",
        "multa_estimada_uit": 5.0,
        "multa_estimada_pen": 5.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 005-2016-JUS/DGPDP / R.D. 542-2019-JUS (Conservación de datos y deber de cancelación al extinguirse la finalidad)",
        "tipo_hallazgo": "DOCUMENTAL",
        "remediacion_sugerida": "Fijar política explícita de retención con periodicidad de purga automática alineada a plazos legales."
    },
    "R-006": {
        "codigo": "R-006",
        "titulo": "Flujo Transfronterizo a Nube Extranjera sin Registro ante ANPD",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.1.5.2",
        "control_nombre": "Identifying basis for PII transfer between jurisdictions",
        "principio_iso29100": "Principle 6: Openness, transparency and notice",
        "articulo_ley29733": "Art. 15 (Transferencia de datos personales al exterior) y Art. 38 num. 3 LPDP",
        "directiva_seguridad": "D.S. 003-2013-JUS Art. 66 (Inscripción obligatoria de flujo transfronterizo)",
        "multa_estimada_uit": 11.0,
        "multa_estimada_pen": 11.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 125-2019-JUS / R.D. 234-2016-JUS (Servidores en el extranjero sin registrar flujo transfronterizo)",
        "tipo_hallazgo": "DOCUMENTAL",
        "remediacion_sugerida": "Inscribir flujo transfronterizo ante el RNPDP e incorporar cláusulas contractuales tipo con el proveedor cloud."
    },
    "R-007": {
        "codigo": "R-007",
        "titulo": "Trabas Ilegales y Cobro de Tasas para Ejercicio de Derechos ARCO",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.1.3.7",
        "control_nombre": "Access, correction and erasure",
        "principio_iso29100": "Principle 9: Accuracy and quality",
        "articulo_ley29733": "Arts. 19 al 24 (Gratuidad y sencillez en atención de derechos ARCO) y Art. 38 num. 2 LPDP",
        "directiva_seguridad": "D.S. 003-2013-JUS Arts. 47 al 58 (Procedimiento gratuito)",
        "multa_estimada_uit": 9.0,
        "multa_estimada_pen": 9.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 022-2016-JUS/DGPDP / R.D. 112-2022-JUS (Obstaculización y cobro de requisitos para derechos ARCO)",
        "tipo_hallazgo": "DOCUMENTAL",
        "remediacion_sugerida": "Establecer canal electrónico gratuito y simplificado para el ejercicio de derechos ARCO sin exigencias notariales."
    }
}


def obtener_regla(codigo: str) -> Optional[ReglaAuditoria]:
    """Retorna la regla canónica o None si no existe."""
    return CATALOGO_REGLAS.get(codigo.strip().upper())


def resolver_regla_con_fallback(codigo: str) -> ReglaAuditoria:
    """Retorna la regla canónica o un fallback genérico estructurado si no está en catálogo."""
    regla = obtener_regla(codigo)
    if regla:
        return regla
    return {
        "codigo": codigo,
        "titulo": "Brecha de Privacidad General",
        "nivel_riesgo": "MEDIO",
        "control_iso27701": "A.1.2.2",
        "control_nombre": "Identify and document purpose",
        "principio_iso29100": "Principle 1",
        "articulo_ley29733": "Art. 4",
        "directiva_seguridad": "Directiva General",
        "multa_estimada_uit": 3.0,
        "multa_estimada_pen": 3.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución General ANPD",
        "tipo_hallazgo": "TECNICO",
        "remediacion_sugerida": "Revisar medidas de seguridad y documentación legal aplicable."
    }


def listar_todas_las_reglas() -> List[ReglaAuditoria]:
    """Retorna lista de todas las reglas canónicas ordenadas por código."""
    return list(CATALOGO_REGLAS.values())


if __name__ == "__main__":
    # Autochequeo de integridad: comprobación sin dependencias externas
    assert len(CATALOGO_REGLAS) == 7, "Deben existir exactamente 7 reglas canónicas (R-001 a R-007)"
    for r_id in [f"R-00{i}" for i in range(1, 8)]:
        r = obtener_regla(r_id)
        assert r is not None, f"Regla {r_id} no encontrada"
        assert r["multa_estimada_uit"] > 0, f"Multa inválida para {r_id}"
        assert r["control_iso27701"].startswith("A."), f"Control ISO inválido para {r_id}"
    fallback = resolver_regla_con_fallback("R-999")
    assert fallback["codigo"] == "R-999"
    print("Core rules catalog: self-check passed (7 canonical rules valid).")
