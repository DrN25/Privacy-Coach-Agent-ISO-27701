import os
import re
from datetime import datetime
import pymupdf as fitz
import sqlglot
from sqlglot import exp

from .db import get_db_connection
from .profiler import perfilar_columna

def procesar_archivo_sql(ruta_archivo: str, nombre_archivo: str) -> int:
    with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
        contenido = f.read()
    
    tamano = len(contenido.encode("utf-8"))
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO archivos_cargados (nombre_archivo, tipo_archivo, fecha_carga, tamano_bytes, resumen_analisis)
    VALUES (?, 'SQL', ?, ?, 'Esquema SQL DDL analizado mediante AST sqlglot')
    """, (nombre_archivo, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tamano))
    archivo_id = cur.lastrowid
    
    # Parsear AST con sqlglot
    columnas_detectadas = []
    try:
        parsed = sqlglot.parse(contenido)
        for statement in parsed:
            if isinstance(statement, exp.Create):
                # Extraer nombre de tabla
                tabla_expr = statement.find(exp.Table)
                nombre_tabla = tabla_expr.name if tabla_expr else "tabla_desconocida"
                
                # Extraer definiciones de columnas
                for col_def in statement.find_all(exp.ColumnDef):
                    nombre_col = col_def.name
                    tipo_col = col_def.kind.sql() if col_def.kind else "VARCHAR"
                    columnas_detectadas.append((nombre_tabla, nombre_col, tipo_col))
    except Exception as e:
        # Fallback a regex robusta si sqlglot encuentra sentencias complejas
        tables = re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)\s*\((.*?)\);", contenido, re.DOTALL | re.IGNORECASE)
        for tname, body in tables:
            for line in body.split(",\n"):
                line = line.strip()
                if line and not line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "CONSTRAINT", "CHECK", "UNIQUE")):
                    parts = line.split()
                    if len(parts) >= 2:
                        columnas_detectadas.append((tname, parts[0], parts[1]))
    
    # Guardar cada columna analizada con el profiler en SQLite
    for tname, cname, ctype in columnas_detectadas:
        perfil = perfilar_columna(cname, tname, ctype)
        cur.execute("""
        INSERT INTO inventario_activos_datos (
            archivo_id, nombre_tabla, nombre_columna, tipo_sql,
            categoria_sensible, es_dato_sensible, nivel_confianza, candado_deteccion, recomendacion_seguridad
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            archivo_id, perfil.nombre_tabla, perfil.nombre_columna, perfil.tipo_sql,
            perfil.categoria.value, 1 if perfil.es_sensible else 0, perfil.nivel_confianza,
            perfil.candado, perfil.recomendacion
        ))
    
    conn.commit()
    conn.close()
    return archivo_id

def procesar_archivo_documento(ruta_archivo: str, nombre_archivo: str) -> int:
    tipo = "PDF" if nombre_archivo.lower().endswith(".pdf") else "MARKDOWN"
    contenido = ""
    
    if tipo == "PDF":
        doc = fitz.open(ruta_archivo)
        for page in doc:
            contenido += page.get_text() + "\n"
        doc.close()
    else:
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()
    
    tamano = len(contenido.encode("utf-8"))
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO archivos_cargados (nombre_archivo, tipo_archivo, fecha_carga, tamano_bytes, resumen_analisis)
    VALUES (?, ?, ?, ?, 'Documento normativo/contractual analizado y segmentado en cláusulas')
    """, (nombre_archivo, tipo, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tamano))
    archivo_id = cur.lastrowid
    
    # Segmentación en cláusulas / secciones
    lineas = contenido.split("\n")
    clausula_actual = None
    texto_acumulado = []
    
    for line in lineas:
        match = re.match(r"^(?:##|###)?\s*(?:CLÁUSULA|SECCIÓN|[0-9]+\.)\s*([0-9A-Za-z\s]+)[:\-]?(.*)", line.strip(), re.IGNORECASE)
        if match:
            if clausula_actual and texto_acumulado:
                cur.execute("""
                INSERT INTO clausulas_documentales (
                    archivo_id, documento, numero_clausula, titulo_clausula, texto_clausula, tipo_clausula
                ) VALUES (?, ?, ?, ?, ?, ?)
                """, (archivo_id, nombre_archivo, clausula_actual["num"], clausula_actual["titulo"], "\n".join(texto_acumulado), clausula_actual["tipo"]))
            
            num = match.group(1).strip()
            titulo = match.group(2).strip() or num
            
            # Clasificar tipo de cláusula
            tipo_c = "GENERAL"
            if "CONSENTIMIENTO" in line.upper():
                tipo_c = "CONSENTIMIENTO"
            elif "CONSERVACI" in line.upper() or "PLAZO" in line.upper():
                tipo_c = "CONSERVACION"
            elif "ARCO" in line.upper() or "DERECHO" in line.upper():
                tipo_c = "DERECHOS_ARCO"
            elif "TRANSFERENCIA" in line.upper() or "TRANSFRONTERIZO" in line.upper() or "NUBE" in line.upper():
                tipo_c = "FLUJO_TRANSFRONTERIZO"
            elif "SEGURIDAD" in line.upper() or "MEDIDAS" in line.upper():
                tipo_c = "SEGURIDAD"
            
            clausula_actual = {"num": num, "titulo": titulo, "tipo": tipo_c}
            texto_acumulado = [line]
        else:
            texto_acumulado.append(line)
            
    if clausula_actual and texto_acumulado:
        cur.execute("""
        INSERT INTO clausulas_documentales (
            archivo_id, documento, numero_clausula, titulo_clausula, texto_clausula, tipo_clausula
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, (archivo_id, nombre_archivo, clausula_actual["num"], clausula_actual["titulo"], "\n".join(texto_acumulado), clausula_actual["tipo"]))
    
    conn.commit()
    conn.close()
    return archivo_id
