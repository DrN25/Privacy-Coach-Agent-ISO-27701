from typing import Dict, Any

ROUTER_MAP: Dict[str, Dict[str, Any]] = {
    "R-001": {
        "codigo": "R-001",
        "titulo": "Datos de Salud Sensibles sin Cifrado en Reposo",
        "nivel_riesgo": "CRÍTICO",
        "control_iso27701": "A.3.24",
        "control_nombre": "Use of cryptography",
        "principio_iso29100": "Principle 7: Information security",
        "articulo_ley29733": "Art. 38 (Medidas de seguridad en bancos de datos)",
        "directiva_seguridad": "R.D. 019-2013-JUS/DGPDP - Nivel Complejo (Art. 12: Cifrado obligatorio)",
        "multa_estimada_uit": 12.5,
        "multa_estimada_pen": 64375.00,
        "precedente_anpd": "Resolución Directoral N.° 042-2023-JUS/DGPDP (Sanción a clínica por almacenar diagnósticos médicos en texto plano sin cifrado)"
    },
    "R-002": {
        "codigo": "R-002",
        "titulo": "Almacenamiento de Contraseñas con Algoritmo Hash Débil (MD5)",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.3.13",
        "control_nombre": "Access control",
        "principio_iso29100": "Principle 7: Information security",
        "articulo_ley29733": "Art. 38 (Seguridad técnica de credenciales)",
        "directiva_seguridad": "R.D. 019-2013-JUS/DGPDP - Nivel Medio (Autenticación robusta)",
        "multa_estimada_uit": 8.0,
        "multa_estimada_pen": 41200.00,
        "precedente_anpd": "Resolución Directoral N.° 118-2022-JUS/DGPDP (Multa por custodia negligente de credenciales con hashing inseguro sin salting)"
    },
    "R-003": {
        "codigo": "R-003",
        "titulo": "Almacenamiento Ilegal de Código de Seguridad CVV de Tarjetas",
        "nivel_riesgo": "CRÍTICO",
        "control_iso27701": "A.1.4.5",
        "control_nombre": "PII minimization objectives",
        "principio_iso29100": "Principle 5: Collection and retention limitation",
        "articulo_ley29733": "Art. 13 (Principio de Proporcionalidad y Licitud)",
        "directiva_seguridad": "Directiva de Seguridad R.D. 019-2013-JUS (Protección de datos financieros)",
        "multa_estimada_uit": 15.0,
        "multa_estimada_pen": 77250.00,
        "precedente_anpd": "Resolución Directoral N.° 089-2021-JUS/DGPDP (Retención indebida de datos de pago tras la transacción)"
    },
    "R-004": {
        "codigo": "R-004",
        "titulo": "Consentimiento Tácito o Automático por Mera Navegación Web",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.1.2.4",
        "control_nombre": "Determine when and how consent is to be obtained",
        "principio_iso29100": "Principle 1: Consent and choice",
        "articulo_ley29733": "Art. 18 (Consentimiento previo, libre, expreso e inequívoco)",
        "directiva_seguridad": "D.S. 003-2013-JUS Art. 12 (Condiciones del consentimiento)",
        "multa_estimada_uit": 10.0,
        "multa_estimada_pen": 51500.00,
        "precedente_anpd": "Resolución Directoral N.° 205-2023-JUS/DGPDP (Sanción por utilizar cláusulas de aceptación tácita o premarcada)"
    },
    "R-005": {
        "codigo": "R-005",
        "titulo": "Plazo de Conservación Indefinido o Discrecional",
        "nivel_riesgo": "MEDIO",
        "control_iso27701": "A.1.4.8",
        "control_nombre": "Retention",
        "principio_iso29100": "Principle 5: Collection and retention limitation",
        "articulo_ley29733": "Art. 6 (Principio de Calidad y Plazo Proporcional)",
        "directiva_seguridad": "D.S. 003-2013-JUS Art. 28 (Cancelación y bloqueo por expiración)",
        "multa_estimada_uit": 5.0,
        "multa_estimada_pen": 25750.00,
        "precedente_anpd": "Resolución Directoral N.° 031-2022-JUS/DGPDP (Conservación perpetua de datos sin justificación legal)"
    },
    "R-006": {
        "codigo": "R-006",
        "titulo": "Flujo Transfronterizo a Nube Extranjera sin Registro ante ANPD",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.1.5.2",
        "control_nombre": "Identifying basis for PII transfer between jurisdictions",
        "principio_iso29100": "Principle 6: Openness, transparency and notice",
        "articulo_ley29733": "Art. 15 (Transferencia de datos personales a servidores en el exterior)",
        "directiva_seguridad": "D.S. 003-2013-JUS Art. 66 (Inscripción obligatoria de flujo transfronterizo)",
        "multa_estimada_uit": 11.0,
        "multa_estimada_pen": 56650.00,
        "precedente_anpd": "Resolución Directoral N.° 174-2023-JUS/DGPDP (Hosting en AWS/GCP en EE.UU. sin registro formal ante la ANPD)"
    },
    "R-007": {
        "codigo": "R-007",
        "titulo": "Trabas Ilegales y Cobro de Tasas para Ejercicio de Derechos ARCO",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.1.3.7",
        "control_nombre": "Access, correction and erasure",
        "principio_iso29100": "Principle 9: Accuracy and quality",
        "articulo_ley29733": "Arts. 19 al 24 (Gratuidad y sencillez en atención de derechos ARCO)",
        "directiva_seguridad": "D.S. 003-2013-JUS Arts. 47 al 58 (Procedimiento gratuito)",
        "multa_estimada_uit": 9.0,
        "multa_estimada_pen": 46350.00,
        "precedente_anpd": "Resolución Directoral N.° 092-2022-JUS/DGPDP (Exigir trámites notariales presenciales o cobrar por atender solicitudes ARCO)"
    }
}

def resolver_enrutamiento(codigo_regla: str) -> Dict[str, Any]:
    return ROUTER_MAP.get(codigo_regla, {
        "codigo": codigo_regla,
        "titulo": "Brecha de Privacidad General",
        "nivel_riesgo": "MEDIO",
        "control_iso27701": "A.1.2.2",
        "control_nombre": "Identify and document purpose",
        "principio_iso29100": "Principle 1",
        "articulo_ley29733": "Art. 4",
        "directiva_seguridad": "Directiva General",
        "multa_estimada_uit": 3.0,
        "multa_estimada_pen": 15450.00,
        "precedente_anpd": "Resolución General ANPD"
    })
