"""
Servicio de Auditoría DSPM y Cumplimiento Normativo (Application Service).
Orquesta la evaluación determinista de las reglas canónicas R-001 a R-007
sobre el inventario de datos y las cláusulas contractuales.
"""

from datetime import datetime
from typing import List, Dict, Any

from ..infrastructure.repository import repository
from ..core.rules_catalog import resolver_regla_con_fallback


class AuditService:
    def __init__(self, repo=repository):
        self.repo = repo

    def ejecutar_auditoria_completa(self) -> List[Dict[str, Any]]:
        """Ejecuta la auditoría DSPM completa y persiste los hallazgos."""
        # Limpiar hallazgos previos
        self.repo.limpiar_hallazgos()

        conn = self.repo.get_conn()
        cur = conn.cursor()

        # 1. Regla R-001 (Datos Sensibles sin cifrar en reposo)
        cur.execute("""
        SELECT i.nombre_tabla, i.nombre_columna, i.tipo_sql, i.categoria_sensible,
               COALESCE(a.nombre_archivo, 'esquema_datos.sql') as origen_archivo
        FROM inventario_activos_datos i
        LEFT JOIN archivos_cargados a ON i.archivo_id = a.id
        WHERE i.categoria_sensible IN ('DATOS_SALUD', 'DATOS_BIOMETRICOS', 'DATOS_SENSIBLES')
          AND UPPER(i.tipo_sql) IN ('VARCHAR', 'TEXT', 'CHARACTER VARYING', 'STRING')
        """)
        salud_brechas = cur.fetchall()
        if salud_brechas:
            cols = ", ".join([f"{r['nombre_tabla']}.{r['nombre_columna']}" for r in salud_brechas])
            archivo = salud_brechas[0]["origen_archivo"]
            info = resolver_regla_con_fallback("R-001")
            self.repo.insertar_hallazgo({
                "codigo_regla": info["codigo"],
                "titulo": info["titulo"],
                "descripcion": f"Se detectaron campos sensibles de la organización almacenados en texto abierto sin funciones de cifrado de columna (pgcrypto/AES-256): {cols}.",
                "nivel_riesgo": info["nivel_riesgo"],
                "elemento_afectado": cols,
                "origen_archivo": archivo,
                "control_iso27701": info["control_iso27701"],
                "principio_iso29100": info["principio_iso29100"],
                "articulo_ley29733": info["articulo_ley29733"],
                "directiva_seguridad": info["directiva_seguridad"],
                "multa_estimada_uit": info["multa_estimada_uit"],
                "multa_estimada_pen": info["multa_estimada_pen"],
                "precedente_anpd": info["precedente_anpd"],
                "fecha_deteccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # 2. Regla R-002 (Hash MD5 o credenciales sin sal)
        cur.execute("""
        SELECT i.nombre_tabla, i.nombre_columna, i.tipo_sql,
               COALESCE(a.nombre_archivo, 'esquema_datos.sql') as origen_archivo
        FROM inventario_activos_datos i
        LEFT JOIN archivos_cargados a ON i.archivo_id = a.id
        WHERE i.categoria_sensible = 'CREDENCIALES_ACCESO'
          AND (i.tipo_sql LIKE '%32%' OR i.nombre_columna LIKE '%md5%' OR i.nombre_columna LIKE '%sha1%')
        """)
        pwd_brechas = cur.fetchall()
        if pwd_brechas:
            cols = ", ".join([f"{r['nombre_tabla']}.{r['nombre_columna']}" for r in pwd_brechas])
            archivo = pwd_brechas[0]["origen_archivo"]
            info = resolver_regla_con_fallback("R-002")
            self.repo.insertar_hallazgo({
                "codigo_regla": info["codigo"],
                "titulo": info["titulo"],
                "descripcion": f"La columna {cols} utiliza un esquema de longitud o algoritmo obsoleto (MD5/SHA1 sin sal) vulnerable a tablas arcoíris y ataques de fuerza bruta.",
                "nivel_riesgo": info["nivel_riesgo"],
                "elemento_afectado": cols,
                "origen_archivo": archivo,
                "control_iso27701": info["control_iso27701"],
                "principio_iso29100": info["principio_iso29100"],
                "articulo_ley29733": info["articulo_ley29733"],
                "directiva_seguridad": info["directiva_seguridad"],
                "multa_estimada_uit": info["multa_estimada_uit"],
                "multa_estimada_pen": info["multa_estimada_pen"],
                "precedente_anpd": info["precedente_anpd"],
                "fecha_deteccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # 3. Regla R-003 (CVV de tarjeta almacenado post-transacción)
        cur.execute("""
        SELECT i.nombre_tabla, i.nombre_columna,
               COALESCE(a.nombre_archivo, 'esquema_datos.sql') as origen_archivo
        FROM inventario_activos_datos i
        LEFT JOIN archivos_cargados a ON i.archivo_id = a.id
        WHERE i.nombre_columna LIKE '%cvv%' OR i.nombre_columna LIKE '%cvc%' OR i.nombre_columna LIKE '%cod_seguridad%'
        """)
        cvv_brechas = cur.fetchall()
        if cvv_brechas:
            cols = ", ".join([f"{r['nombre_tabla']}.{r['nombre_columna']}" for r in cvv_brechas])
            archivo = cvv_brechas[0]["origen_archivo"]
            info = resolver_regla_con_fallback("R-003")
            self.repo.insertar_hallazgo({
                "codigo_regla": info["codigo"],
                "titulo": info["titulo"],
                "descripcion": f"Almacenamiento persistente de código de seguridad de pago CVV/CVC ({cols}) en violación del principio de proporcionalidad y estándares internacionales de pago.",
                "nivel_riesgo": info["nivel_riesgo"],
                "elemento_afectado": cols,
                "origen_archivo": archivo,
                "control_iso27701": info["control_iso27701"],
                "principio_iso29100": info["principio_iso29100"],
                "articulo_ley29733": info["articulo_ley29733"],
                "directiva_seguridad": info["directiva_seguridad"],
                "multa_estimada_uit": info["multa_estimada_uit"],
                "multa_estimada_pen": info["multa_estimada_pen"],
                "precedente_anpd": info["precedente_anpd"],
                "fecha_deteccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # 4. Reglas Documentales (R-004 a R-007)
        cur.execute("SELECT id, documento, titulo_clausula, texto_clausula, tipo_clausula FROM clausulas_documentales")
        clausulas = cur.fetchall()
        conn.close()

        # R-004: Consentimiento tácito o presunto
        r004 = [c for c in clausulas if any(k in c["texto_clausula"].upper() for k in ["TÁCITA", "TACITA", "AUTOMÁTICA", "AUTOMATICA", "MERA NAVEGACIÓN", "MERA NAVEGACION", "SE PRESUME"])]
        if r004:
            info = resolver_regla_con_fallback("R-004")
            titulos = ", ".join(dict.fromkeys([m["titulo_clausula"] for m in r004]))
            self.repo.insertar_hallazgo({
                "codigo_regla": info["codigo"],
                "titulo": info["titulo"],
                "descripcion": f"La cláusula '{r004[0]['titulo_clausula']}' estipula un consentimiento tácito o automático, vulnerando el requisito legal de manifestación libre, previa, expresa e inequívoca.",
                "nivel_riesgo": info["nivel_riesgo"],
                "elemento_afectado": titulos,
                "origen_archivo": r004[0]["documento"],
                "control_iso27701": info["control_iso27701"],
                "principio_iso29100": info["principio_iso29100"],
                "articulo_ley29733": info["articulo_ley29733"],
                "directiva_seguridad": info["directiva_seguridad"],
                "multa_estimada_uit": info["multa_estimada_uit"],
                "multa_estimada_pen": info["multa_estimada_pen"],
                "precedente_anpd": info["precedente_anpd"],
                "fecha_deteccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # R-005: Conservación indefinida de datos
        r005 = [
            c for c in clausulas
            if any(k in c["texto_clausula"].upper() for k in [
                "INDEFINID", "PERPETU", "TIEMPO ILIMITADO", "SIN PLAZO DE PURGA", "DE FORMA INDEFINIDA", "SIN CADUCIDAD"
            ])
        ]
        if r005:
            info = resolver_regla_con_fallback("R-005")
            titulos = ", ".join(dict.fromkeys([m["titulo_clausula"] for m in r005]))
            self.repo.insertar_hallazgo({
                "codigo_regla": info["codigo"],
                "titulo": info["titulo"],
                "descripcion": f"La cláusula '{r005[0]['titulo_clausula']}' declara retención por tiempo indefinido o ilimitado, vulnerando la obligación legal de fijar plazos objetivos de expiración y supresión.",
                "nivel_riesgo": info["nivel_riesgo"],
                "elemento_afectado": titulos,
                "origen_archivo": r005[0]["documento"],
                "control_iso27701": info["control_iso27701"],
                "principio_iso29100": info["principio_iso29100"],
                "articulo_ley29733": info["articulo_ley29733"],
                "directiva_seguridad": info["directiva_seguridad"],
                "multa_estimada_uit": info["multa_estimada_uit"],
                "multa_estimada_pen": info["multa_estimada_pen"],
                "precedente_anpd": info["precedente_anpd"],
                "fecha_deteccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # R-006: Flujo transfronterizo sin garantías ni registro
        r006 = [
            c for c in clausulas
            if any(k in c["texto_clausula"].upper() for k in [
                "EXTRANJERO", "FUERA DEL PERÚ", "FUERA DEL PAIS", "FUERA DEL PAÍS",
                "TRANSFRONTERIZ", "EXTERIOR", "OTRO PAÍS", "INTERNACIONAL", "JURISDICCIÓN EXTERNA"
            ]) and any(k in c["texto_clausula"].upper() for k in [
                "NO SE REQUERIRÁ", "NO REQUERIRÁ", "SIN REGISTRO", "RENUNCIA",
                "EXIME", "EXENCIÓN", "NO SERÁ NECESARIA LA INSCRIPCIÓN", "DISPENSA", "PRESCINDE"
            ])
        ]
        if r006:
            info = resolver_regla_con_fallback("R-006")
            titulos = ", ".join(dict.fromkeys([m["titulo_clausula"] for m in r006]))
            self.repo.insertar_hallazgo({
                "codigo_regla": info["codigo"],
                "titulo": info["titulo"],
                "descripcion": f"La cláusula '{r006[0]['titulo_clausula']}' contempla transferencias internacionales de datos hacia servidores fuera del país eximiendo o prescindiendo del registro formal ante el Registro Nacional de Protección de Datos Personales.",
                "nivel_riesgo": info["nivel_riesgo"],
                "elemento_afectado": titulos,
                "origen_archivo": r006[0]["documento"],
                "control_iso27701": info["control_iso27701"],
                "principio_iso29100": info["principio_iso29100"],
                "articulo_ley29733": info["articulo_ley29733"],
                "directiva_seguridad": info["directiva_seguridad"],
                "multa_estimada_uit": info["multa_estimada_uit"],
                "multa_estimada_pen": info["multa_estimada_pen"],
                "precedente_anpd": info["precedente_anpd"],
                "fecha_deteccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # R-007: Trabas u obstáculos al ejercicio de derechos ARCO
        r007 = [
            c for c in clausulas
            if any(k in c["texto_clausula"].upper() for k in [
                "NOTARIAL", "PRESENCIAL", "TASA", "COSTO", "ARANCEL", "PAGO PREVIO", "COBRO", "TARIFA", "COMISIÓN", "PRECIO"
            ]) and any(k in c["texto_clausula"].upper() for k in [
                "ARCO", "ACCESO", "RECTIFICACI", "CANCELACI", "OPOSICI", "REVOCATORIA", "DERECHO"
            ])
        ]
        if r007:
            info = resolver_regla_con_fallback("R-007")
            titulos = ", ".join(dict.fromkeys([m["titulo_clausula"] for m in r007]))
            self.repo.insertar_hallazgo({
                "codigo_regla": info["codigo"],
                "titulo": info["titulo"],
                "descripcion": f"La cláusula '{r007[0]['titulo_clausula']}' impone requisitos gravosos (tasas administrativas o comparecencia/carta notarial obligatoria) para ejercer derechos ARCO, vulnerando el principio de gratuidad.",
                "nivel_riesgo": info["nivel_riesgo"],
                "elemento_afectado": titulos,
                "origen_archivo": r007[0]["documento"],
                "control_iso27701": info["control_iso27701"],
                "principio_iso29100": info["principio_iso29100"],
                "articulo_ley29733": info["articulo_ley29733"],
                "directiva_seguridad": info["directiva_seguridad"],
                "multa_estimada_uit": info["multa_estimada_uit"],
                "multa_estimada_pen": info["multa_estimada_pen"],
                "precedente_anpd": info["precedente_anpd"],
                "fecha_deteccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        return self.repo.obtener_todos_los_hallazgos()


audit_service = AuditService()


# Compatibilidad
def ejecutar_auditoria_dspm() -> List[Dict[str, Any]]:
    return audit_service.ejecutar_auditoria_completa()
