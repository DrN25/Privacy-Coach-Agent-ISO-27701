"""
Router de Gestión de Archivos y Carga Documental.
Endpoints: /api/upload, /api/mockups, /api/documents/{archivo_id}.
"""

import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException

from ...infrastructure.repository import repository
from ...services.ingestion_service import ingestion_service

router = APIRouter(tags=["Files"])


@router.get("/api/mockups")
def get_mockups():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    mockups_dir = os.path.join(base_dir, "mockups")
    if not os.path.exists(mockups_dir):
        mockups_dir = os.path.join(base_dir, "src", "mockups")

    archivos = []
    if os.path.exists(mockups_dir):
        for f in os.listdir(mockups_dir):
            path = os.path.join(mockups_dir, f)
            if os.path.isfile(path):
                tipo = f.split(".")[-1].upper()
                if tipo == "SQL":
                    desc = "Esquema de base de datos relacional (DDL)"
                elif "politica" in f.lower():
                    desc = "Política de privacidad y protección de datos personales"
                elif "contrato" in f.lower() or "sla" in f.lower():
                    desc = "Contrato de encargo y prestación de servicios"
                elif "diccionario" in f.lower():
                    desc = "Diccionario y notas técnicas de activos de datos"
                else:
                    desc = f"Documento de auditoría ({tipo})"

                archivos.append({
                    "nombre": f,
                    "tamano": os.path.getsize(path),
                    "tipo": tipo,
                    "descripcion": desc
                })
    return {"mockups": archivos}


@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    temp_dir = os.path.join(base_dir, "data", "uploads")
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

    if fname.endswith(".sql"):
        ingestion_service.procesar_sql(temp_path, safe_filename)
    else:
        ingestion_service.procesar_documento(temp_path, safe_filename)

    return {
        "mensaje": f"Archivo '{safe_filename}' parseado e incorporado a la base de datos de la empresa.",
        "necesita_reanalisis": True
    }


@router.delete("/api/documents/{archivo_id}")
def delete_document(archivo_id: int):
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
        "mensaje": f"Documento '{nombre}' eliminado del repositorio de la empresa.",
        "necesita_reanalisis": True
    }
