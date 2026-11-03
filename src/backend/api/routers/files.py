"""
Router de Gestión de Archivos y Carga Documental Institucional UNSA.
Maneja carga documental, OCR para PDFs, parseo AST de SQL y sincronización de corpus institucional.
Endpoints: /api/upload, /api/mockups, /api/documents/{archivo_id}.
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from ...infrastructure.repository import repository
from ...services.document_processor import document_processor

router = APIRouter(tags=["Files"])


def obtener_base_dir() -> str:
    """Retorna la raíz del proyecto (directorio de trabajo TIF)."""
    p = os.path.abspath(__file__)
    for _ in range(5):
        p = os.path.dirname(p)
    return p


def obtener_directorio_documentos() -> str:
    """Retorna la ruta al directorio de documentos institucionales de la UNSA."""
    base_dir = obtener_base_dir()
    media_docs = os.path.join(base_dir, "media", "documents")
    if os.path.exists(media_docs) and os.listdir(media_docs):
        return media_docs
    mockups_dir = os.path.join(base_dir, "src", "mockups")
    if os.path.exists(mockups_dir):
        return mockups_dir
    return media_docs


def buscar_ruta_archivo_fisico(nombre_archivo: str) -> str:
    """Localiza la ruta real en disco del archivo buscado."""
    base_dir = obtener_base_dir()
    rutas_candidatas = [
        os.path.join(base_dir, "media", "documents", "originales_unsa", nombre_archivo),
        os.path.join(base_dir, "media", "documents", nombre_archivo),
        os.path.join(base_dir, "media", "uploads", nombre_archivo),
        os.path.join(base_dir, "src", "mockups", nombre_archivo),
    ]
    for r in rutas_candidatas:
        if os.path.exists(r) and os.path.isfile(r):
            return r
    return ""


@router.get("/api/mockups")
def get_mockups():
    """Lista los documentos institucionales disponibles en el repositorio oficial UNSA."""
    base_dir = obtener_base_dir()
    docs_dir = os.path.join(base_dir, "media", "documents")
    real_dir = os.path.join(docs_dir, "originales_unsa")
    archivos = []
    vistos = set()

    conn = repository.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, nombre_archivo FROM archivos_cargados")
    mapa_db = {row["nombre_archivo"]: row["id"] for row in cur.fetchall()}
    conn.close()

    descripciones_unsa = {
        # Documentos Originales Oficiales de la UNSA
        "RR_0503_2026_Creacion_CSIRT_UNSA.pdf": "Resolución Rectoral conformación del CSIRT-UNSA (Equipo de Respuesta a Incidentes)",
        "RR_0987_2025_Designacion_Oficial_Proteccion_Datos_UNSA.pdf": "Resolución Rectoral designación oficial del Oficial de Datos Personales (DPO UNSA)",
        "RR_1234_2026_Designacion_Oficial_Gobierno_Datos_UNSA.pdf": "Resolución Rectoral designación de la Oficial de Gobierno de Datos (OGD UNSA)",
        "RR_1244_2025_Designacion_Oficial_Seguridad_Confianza_Digital_UNSA.pdf": "Resolución Rectoral designación del Oficial de Seguridad y Confianza Digital (CISO)",
        "RCU_0085_2026_Reglamento_Admision_Pregrado_UNSA_v5.pdf": "Reglamento Oficial Proceso de Admisión Pregrado versión 5 vigente (32 páginas)",
        "RR_1130_2026_TUPA_Procedimiento_Grados_Titulos_UNSA.pdf": "TUPA Oficial Procedimiento N° 73 Grados Académicos y Títulos (12 páginas)",
        "Convenios_Oficiales_Suscritos_UNSA_2009_2026.pdf": "Padrón Oficial de Convenios Suscritos por la UNSA 2009-2026 (82 páginas)",
        "Reglamento_Proteccion_Datos_Estudiantes_UNSA.pdf": "Reglamento Institucional de Protección y Transparencia de Datos Estudiantes",
        "Padron_Miembros_Mesa_Elecciones_Pregrado_UNSA.pdf": "Padrón Electoral Oficial con datos de estudiantes y mesas (27 páginas)",
        "Resultados_Ingresantes_Posgrado_IIFase_UNSA.pdf": "Resultados Oficiales del Concurso de Admisión Posgrado con postulantes (22 páginas)",
        # Esquemas SQL y fixtures canónicos
        "schema_unsa_servicios_centrales.sql": "Esquema DDL de Servicios Centrales UNSA (SISUNSA, Hospital, Admisión, Pagos)",
        "Reglamento_Admision_Pregrado_UNSA_2026.pdf": "Reglamento General de Admisión Pregrado (Biometría, Huella, RCU N° 0103-2026)",
        "TUPA_UNSA_Procedimientos_Administrativos_2026.pdf": "TUPA Institucional UNSA (Procedimientos de Derechos ARCO y Tasas - R.R. 0214-2026)",
        "Directiva_Seguridad_Informacion_RR_0503_2026_UNSA.pdf": "Directiva de Seguridad TI y Notificación de Brechas PII (R.R. 0503-2026)",
        "Reglamento_Comedor_Universitario_SISCOM_UNSA.pdf": "Reglamento de Bienestar Estudiantil y Comedores SISCOM (DUDE / RCU N° 0340-2025)",
        "Manual_Procedimientos_Hospital_Docente_Zamacola_UNSA.pdf": "Manual de Procedimientos y Custodia de Historias Clínicas (Hospital Docente Zamácola)",
        "Contrato_DPA_Google_Workspace_Education_UNSA_2026.pdf": "Acuerdo de Tratamiento de Datos (DPA) Google Workspace for Education (R.R. 0089-2026)",
        "Directiva_Correo_Institucional_Nube_OTI_UNSA.pdf": "Directiva de Correo Institucional, MFA y Servicios Nube (OTI / R.R. 0412-2024)",
        "Reglamento_Etica_Investigacion_Ensayos_Clinicos_VRI_UNSA.pdf": "Reglamento de Ética y Protección de Datos en Ensayos Clínicos (VRI / RCU N° 0285-2025)",
        "Convenio_Pasarela_Pagos_Tesoreria_BancoNacion_UNSA.pdf": "Convenio de Recaudación Electrónica Págalo.pe y No Almacenamiento de CVV (R.R. 0178-2025)",
        "Reglamento_Grados_Titulos_Archivo_SanAgustin_UNSA.pdf": "Reglamento de Grados y Custodia Histórica Documental en San Agustín 115 (RCU N° 0055-2024)"
    }

    carpetas_a_escanear = []
    if os.path.exists(real_dir):
        carpetas_a_escanear.append(real_dir)
    if os.path.exists(docs_dir):
        carpetas_a_escanear.append(docs_dir)

    for c in carpetas_a_escanear:
        for f in sorted(os.listdir(c)):
            path = os.path.join(c, f)
            if os.path.isfile(path) and f not in vistos:
                vistos.add(f)
                tipo = f.split(".")[-1].upper()
                desc = descripciones_unsa.get(f)
                if not desc:
                    if tipo == "SQL":
                        desc = "Esquema de base de datos relacional (DDL)"
                    elif "politica" in f.lower() or "reglamento" in f.lower():
                        desc = "Reglamento / Política de protección de datos personales"
                    elif "contrato" in f.lower() or "dpa" in f.lower():
                        desc = "Contrato de encargo y tratamiento de datos personales"
                    elif "tupa" in f.lower() or "directiva" in f.lower():
                        desc = "Normativa y procedimientos administrativos institucionales"
                    else:
                        desc = f"Documento institucional ({tipo})"

                aid = mapa_db.get(f)
                archivos.append({
                    "id": aid,
                    "nombre": f,
                    "nombre_archivo": f,
                    "tamano": os.path.getsize(path),
                    "tipo": tipo,
                    "descripcion": desc,
                    "es_original_unsa": "originales_unsa" in c,
                    "cargado_en_db": aid is not None,
                    "raw_url": f"/api/documents/raw?filename={f}"
                })
    return {"mockups": archivos}


@router.get("/api/documents/raw")
def get_raw_document_by_name(filename: str):
    """Sirve directamente cualquier archivo del repositorio institucional por nombre para visualización inline en pestaña."""
    ruta = buscar_ruta_archivo_fisico(filename)
    if not ruta or not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail=f"El archivo físico '{filename}' no está disponible.")
    media_type = "application/pdf" if filename.lower().endswith(".pdf") else "text/plain; charset=utf-8"
    return FileResponse(
        ruta,
        media_type=media_type,
        content_disposition_type="inline",
        filename=filename,
        headers={"Content-Disposition": f'inline; filename="{filename}"'}
    )


@router.get("/api/documents/{archivo_id}/preview")
def preview_document(archivo_id: str):
    """Retorna la vista previa estructurada del documento: cláusulas, columnas y metadatos."""
    conn = repository.get_conn()
    cur = conn.cursor()
    
    archivo = None
    if str(archivo_id).isdigit():
        cur.execute("SELECT * FROM archivos_cargados WHERE id = ?", (int(archivo_id),))
        archivo = cur.fetchone()
    
    if not archivo:
        cur.execute("SELECT * FROM archivos_cargados WHERE nombre_archivo = ?", (str(archivo_id),))
        archivo = cur.fetchone()

    # Si no está en DB pero existe en disco, se ingesta dinámicamente
    if not archivo:
        conn.close()
        ruta_fisica = buscar_ruta_archivo_fisico(str(archivo_id))
        if ruta_fisica and os.path.exists(ruta_fisica):
            proc_res = document_processor.procesar_archivo(ruta_fisica, nombre_original=os.path.basename(ruta_fisica))
            new_id = proc_res.get("archivo_id")
            if new_id:
                return preview_document(str(new_id))
        raise HTTPException(status_code=404, detail="Documento no encontrado en base de datos ni en disco.")

    archivo_dict = dict(archivo)
    actual_id = archivo_dict["id"]

    # Cláusulas extraídas
    cur.execute("""
        SELECT numero_clausula, titulo_clausula, texto_clausula, tipo_clausula, estado_cumplimiento, alerta_legal
        FROM clausulas_documentales WHERE archivo_id = ? ORDER BY id ASC
    """, (actual_id,))
    clausulas = [dict(r) for r in cur.fetchall()]

    # Columnas sensibles (si es SQL)
    cur.execute("""
        SELECT nombre_tabla, nombre_columna, tipo_sql, es_clave_primaria, categoria_sensible, es_dato_sensible, candado_deteccion, recomendacion_seguridad
        FROM inventario_activos_datos WHERE archivo_id = ? ORDER BY id ASC
    """, (actual_id,))
    columnas = [dict(r) for r in cur.fetchall()]
    conn.close()

    ruta_fisica = buscar_ruta_archivo_fisico(archivo_dict["nombre_archivo"])
    tiene_archivo_fisico = bool(ruta_fisica and os.path.exists(ruta_fisica))

    return {
        "archivo": archivo_dict,
        "clausulas": clausulas,
        "total_clausulas": len(clausulas),
        "columnas_sensibles": columnas,
        "total_columnas": len(columnas),
        "tiene_archivo_fisico": tiene_archivo_fisico,
        "raw_url": f"/api/documents/raw?filename={archivo_dict['nombre_archivo']}" if tiene_archivo_fisico else None
    }


@router.get("/api/documents/{archivo_id}/raw")
def get_raw_document(archivo_id: str):
    """Sirve el archivo físico original para visualización nativa en el navegador."""
    nombre = None
    if str(archivo_id).isdigit():
        conn = repository.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT nombre_archivo, tipo_archivo FROM archivos_cargados WHERE id = ?", (int(archivo_id),))
        row = cur.fetchone()
        conn.close()
        if row:
            nombre = row["nombre_archivo"]
    
    if not nombre:
        nombre = str(archivo_id)

    ruta = buscar_ruta_archivo_fisico(nombre)
    if not ruta or not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail=f"El archivo físico '{nombre}' no está disponible en disco.")

    media_type = "application/pdf" if nombre.lower().endswith(".pdf") else "text/plain; charset=utf-8"
    return FileResponse(
        ruta,
        media_type=media_type,
        content_disposition_type="inline",
        filename=nombre,
        headers={"Content-Disposition": f'inline; filename="{nombre}"'}
    )


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Carga y procesa un nuevo documento (.pdf, .sql, .md, .txt) extrayendo texto, OCR y AST."""
    base_dir = obtener_base_dir()
    temp_dir = os.path.join(base_dir, "media", "uploads")
    os.makedirs(temp_dir, exist_ok=True)

    safe_filename = os.path.basename(file.filename or "")
    if not safe_filename or safe_filename != file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")

    fname = safe_filename.lower()
    if not fname.endswith((".sql", ".pdf", ".md", ".txt")):
        raise HTTPException(status_code=400, detail="Formato no soportado. Suba archivos SQL, PDF, MD o TXT.")

    temp_path = os.path.join(temp_dir, safe_filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        resultado = document_processor.procesar_archivo(temp_path, safe_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar archivo: {str(e)}")

    return {
        "mensaje": f"Archivo '{safe_filename}' procesado e integrado al repositorio institucional.",
        "archivo_id": resultado.get("archivo_id"),
        "tipo": resultado.get("tipo"),
        "tamano": resultado.get("tamano"),
        "necesita_reanalisis": True
    }


@router.delete("/api/documents/{archivo_id}")
def delete_document(archivo_id: int):
    """Elimina un documento del repositorio institucional y su inventario asociado."""
    conn = repository.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT nombre_archivo FROM archivos_cargados WHERE id = ?", (archivo_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Archivo no encontrado.")

    nombre = row["nombre_archivo"]
    cur.execute("DELETE FROM inventario_activos_datos WHERE archivo_id = ?", (archivo_id,))
    cur.execute("DELETE FROM clausulas_documentales WHERE archivo_id = ?", (archivo_id,))
    cur.execute("DELETE FROM archivos_cargados WHERE id = ?", (archivo_id,))
    conn.commit()
    conn.close()

    return {
        "mensaje": f"Documento '{nombre}' eliminado del repositorio institucional.",
        "necesita_reanalisis": True
    }
