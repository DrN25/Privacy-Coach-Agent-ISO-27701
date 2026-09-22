from datetime import datetime
from .db import get_db_connection
from .router import resolver_enrutamiento

def ejecutar_auditoria_dspm():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Limpiar hallazgos previos
    cur.execute("DELETE FROM hallazgos_dspm")
    
    # 1. Evaluar Regla R-001 (Datos de Salud sin cifrar en VARCHAR/TEXT)
    cur.execute("""
    SELECT nombre_tabla, nombre_columna, tipo_sql, categoria_sensible
    FROM inventario_activos_datos
    WHERE categoria_sensible = 'DATOS_SALUD'
      AND UPPER(tipo_sql) IN ('VARCHAR', 'TEXT', 'CHARACTER VARYING', 'STRING')
    """)
    salud_brechas = cur.fetchall()
    if salud_brechas:
        cols = ", ".join([f"{r['nombre_tabla']}.{r['nombre_columna']}" for r in salud_brechas])
        info = resolver_enrutamiento("R-001")
        cur.execute("""
        INSERT INTO hallazgos_dspm (
            codigo_regla, titulo, descripcion, nivel_riesgo, elemento_afectado, origen_archivo,
            control_iso27701, principio_iso29100, articulo_ley29733, directiva_seguridad,
            multa_estimada_uit, multa_estimada_pen, precedente_anpd, fecha_deteccion
        ) VALUES (?, ?, ?, ?, ?, 'schema_clinica_saludtotal.sql', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            info["codigo"], info["titulo"],
            f"Se detectaron campos clínicos sensibles almacenados en texto abierto sin funciones de cifrado de columna (pgcrypto/AES-256): {cols}.",
            info["nivel_riesgo"], cols, info["control_iso27701"], info["principio_iso29100"],
            info["articulo_ley29733"], info["directiva_seguridad"], info["multa_estimada_uit"],
            info["multa_estimada_pen"], info["precedente_anpd"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    # 2. Evaluar Regla R-002 (Hash MD5 en credenciales de acceso)
    cur.execute("""
    SELECT nombre_tabla, nombre_columna, tipo_sql
    FROM inventario_activos_datos
    WHERE categoria_sensible = 'CREDENCIALES_ACCESO'
      AND (tipo_sql LIKE '%32%' OR nombre_columna LIKE '%md5%')
    """)
    pwd_brechas = cur.fetchall()
    if pwd_brechas:
        cols = ", ".join([f"{r['nombre_tabla']}.{r['nombre_columna']}" for r in pwd_brechas])
        info = resolver_enrutamiento("R-002")
        cur.execute("""
        INSERT INTO hallazgos_dspm (
            codigo_regla, titulo, descripcion, nivel_riesgo, elemento_afectado, origen_archivo,
            control_iso27701, principio_iso29100, articulo_ley29733, directiva_seguridad,
            multa_estimada_uit, multa_estimada_pen, precedente_anpd, fecha_deteccion
        ) VALUES (?, ?, ?, ?, ?, 'schema_clinica_saludtotal.sql', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            info["codigo"], info["titulo"],
            f"La columna {cols} utiliza un esquema de longitud fija (VARCHAR(32)) propio de hashing MD5 obsoleto y vulnerable a tablas arcoíris.",
            info["nivel_riesgo"], cols, info["control_iso27701"], info["principio_iso29100"],
            info["articulo_ley29733"], info["directiva_seguridad"], info["multa_estimada_uit"],
            info["multa_estimada_pen"], info["precedente_anpd"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    # 3. Evaluar Regla R-003 (CVV de tarjeta almacenado en BD)
    cur.execute("""
    SELECT nombre_tabla, nombre_columna
    FROM inventario_activos_datos
    WHERE nombre_columna LIKE '%cvv%' OR nombre_columna LIKE '%cvc%'
    """)
    cvv_brechas = cur.fetchall()
    if cvv_brechas:
        cols = ", ".join([f"{r['nombre_tabla']}.{r['nombre_columna']}" for r in cvv_brechas])
        info = resolver_enrutamiento("R-003")
        cur.execute("""
        INSERT INTO hallazgos_dspm (
            codigo_regla, titulo, descripcion, nivel_riesgo, elemento_afectado, origen_archivo,
            control_iso27701, principio_iso29100, articulo_ley29733, directiva_seguridad,
            multa_estimada_uit, multa_estimada_pen, precedente_anpd, fecha_deteccion
        ) VALUES (?, ?, ?, ?, ?, 'schema_clinica_saludtotal.sql', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            info["codigo"], info["titulo"],
            f"Almacenamiento persistente de código de seguridad CVV ({cols}) en violación del principio de proporcionalidad y estándares internacionales.",
            info["nivel_riesgo"], cols, info["control_iso27701"], info["principio_iso29100"],
            info["articulo_ley29733"], info["directiva_seguridad"], info["multa_estimada_uit"],
            info["multa_estimada_pen"], info["precedente_anpd"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    # 4. Evaluar Cláusulas Documentales (R-004, R-005, R-006, R-007)
    cur.execute("SELECT id, documento, titulo_clausula, texto_clausula, tipo_clausula FROM clausulas_documentales")
    clausulas = cur.fetchall()
    
    for c in clausulas:
        txt = c["texto_clausula"].upper()
        
        # R-004: Consentimiento tácito
        if "TÁCITA" in txt or "TACITA" in txt or "AUTOMÁTICA" in txt or "AUTOMATICA" in txt:
            info = resolver_enrutamiento("R-004")
            cur.execute("""
            INSERT OR IGNORE INTO hallazgos_dspm (
                codigo_regla, titulo, descripcion, nivel_riesgo, elemento_afectado, origen_archivo,
                control_iso27701, principio_iso29100, articulo_ley29733, directiva_seguridad,
                multa_estimada_uit, multa_estimada_pen, precedente_anpd, fecha_deteccion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                info["codigo"], info["titulo"],
                f"La cláusula '{c['titulo_clausula']}' estipula un consentimiento tácito e irrevocable por mera navegación, sancionado reiteradamente por la ANPD.",
                info["nivel_riesgo"], c["titulo_clausula"], c["documento"], info["control_iso27701"], info["principio_iso29100"],
                info["articulo_ley29733"], info["directiva_seguridad"], info["multa_estimada_uit"],
                info["multa_estimada_pen"], info["precedente_anpd"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
        # R-005: Conservación indefinida
        if "INDEFINIDO" in txt or "PERPETUO" in txt:
            info = resolver_enrutamiento("R-005")
            cur.execute("""
            INSERT OR IGNORE INTO hallazgos_dspm (
                codigo_regla, titulo, descripcion, nivel_riesgo, elemento_afectado, origen_archivo,
                control_iso27701, principio_iso29100, articulo_ley29733, directiva_seguridad,
                multa_estimada_uit, multa_estimada_pen, precedente_anpd, fecha_deteccion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                info["codigo"], info["titulo"],
                f"La cláusula '{c['titulo_clausula']}' declara retención por tiempo indefinido, vulnerando la obligación de fijar plazos objetivos de expiración.",
                info["nivel_riesgo"], c["titulo_clausula"], c["documento"], info["control_iso27701"], info["principio_iso29100"],
                info["articulo_ley29733"], info["directiva_seguridad"], info["multa_estimada_uit"],
                info["multa_estimada_pen"], info["precedente_anpd"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        # R-006: Flujo transfronterizo sin garantías
        if "ESTADOS UNIDOS" in txt or "VIRGINIA" in txt or "SINGAPUR" in txt:
            if "NO SE REQUERIRÁ INSCRIPCIÓN" in txt or "RENUNCIA" in txt:
                info = resolver_enrutamiento("R-006")
                cur.execute("""
                INSERT OR IGNORE INTO hallazgos_dspm (
                    codigo_regla, titulo, descripcion, nivel_riesgo, elemento_afectado, origen_archivo,
                    control_iso27701, principio_iso29100, articulo_ley29733, directiva_seguridad,
                    multa_estimada_uit, multa_estimada_pen, precedente_anpd, fecha_deteccion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    info["codigo"], info["titulo"],
                    f"La cláusula '{c['titulo_clausula']}' exime indebidamente el registro de flujo transfronterizo ante la ANPD para servidores en EE.UU.",
                    info["nivel_riesgo"], c["titulo_clausula"], c["documento"], info["control_iso27701"], info["principio_iso29100"],
                    info["articulo_ley29733"], info["directiva_seguridad"], info["multa_estimada_uit"],
                    info["multa_estimada_pen"], info["precedente_anpd"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))

        # R-007: Trabas ARCO (costos o cartas notariales)
        if "S/ 50.00" in txt or "NOTARIAL" in txt or "PRESENCIAL" in txt:
            info = resolver_enrutamiento("R-007")
            cur.execute("""
            INSERT OR IGNORE INTO hallazgos_dspm (
                codigo_regla, titulo, descripcion, nivel_riesgo, elemento_afectado, origen_archivo,
                control_iso27701, principio_iso29100, articulo_ley29733, directiva_seguridad,
                multa_estimada_uit, multa_estimada_pen, precedente_anpd, fecha_deteccion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                info["codigo"], info["titulo"],
                f"La cláusula '{c['titulo_clausula']}' cobra S/ 50.00 y exige carta notarial presencial para derechos ARCO, vulnerando el principio de gratuidad.",
                info["nivel_riesgo"], c["titulo_clausula"], c["documento"], info["control_iso27701"], info["principio_iso29100"],
                info["articulo_ley29733"], info["directiva_seguridad"], info["multa_estimada_uit"],
                info["multa_estimada_pen"], info["precedente_anpd"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

    conn.commit()
    cur.execute("SELECT * FROM hallazgos_dspm ORDER BY multa_estimada_uit DESC")
    hallazgos = [dict(row) for row in cur.fetchall()]
    conn.close()
    return hallazgos
