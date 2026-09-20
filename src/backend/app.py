import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Path
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db import init_db, get_db_connection
from .ingestion import procesar_archivo_sql, procesar_archivo_documento
from .dspm_engine import ejecutar_auditoria_dspm
from .knowledge_bridge import knowledge_bridge
from .coach_agent import dialogar_coach

app = FastAPI(
    title="Privacy & DSPM Multi-Agent System",
    description="Sistema Multi-Agente de Auditoría de Privacidad (ISO 27701, ISO 29100, Ley 29733) con React y OpenRouter DeepSeek",
    version="2.1.0"
)

@app.exception_handler(OSError)
async def os_error_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Ruta inválida en sistema operativo"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

# Modelos Pydantic
class ChatRequest(BaseModel):
    hallazgo_id: int
    mensaje_usuario: str
    historial: Optional[List[dict]] = []

class RemediacionRequest(BaseModel):
    hallazgo_id: int
    parche_sql: str

# Endpoints
@app.get("/api/status")
def get_status():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM archivos_cargados")
    num_archivos = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM inventario_activos_datos")
    num_activos = cur.fetchone()["cnt"]
    cur.execute("SELECT COUNT(*) as cnt FROM hallazgos_dspm")
    num_hallazgos = cur.fetchone()["cnt"]
    conn.close()

    return {
        "status": "online",
        "llm_model": "deepseek/deepseek-v4.1-flash",
        "provider": "OpenRouter",
        "zero_cost_local_kbs": {
            "iso27701_nodes": knowledge_bridge.controls_count,
            "iso27701_edges": len(knowledge_bridge.engine.adj),
            "anpd_cases": len(knowledge_bridge.sanciones)
        },
        "empresa_database": {
            "archivos": num_archivos,
            "columnas_inventariadas": num_activos,
            "hallazgos_activos": num_hallazgos
        }
    }

@app.get("/api/mockups")
def get_mockups():
    mockups_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mockups")
    archivos = []
    if os.path.exists(mockups_dir):
        for f in os.listdir(mockups_dir):
            path = os.path.join(mockups_dir, f)
            if os.path.isfile(path):
                tipo = f.split(".")[-1].upper()
                desc = "Documento de prueba"
                if "schema" in f:
                    desc = "Esquema DDL con datos de salud planos y hashes MD5"
                elif "politica" in f:
                    desc = "Política con consentimiento tácito y trabas ARCO"
                elif "contrato" in f:
                    desc = "SLA Cloud con servidores en EE.UU. no declarados"
                elif "diccionario" in f:
                    desc = "Notas técnicas del área de desarrollo"

                archivos.append({
                    "nombre": f,
                    "tamano": os.path.getsize(path),
                    "tipo": tipo,
                    "descripcion": desc
                })
    return {"mockups": archivos}

@app.post("/api/reset")
def reset_database():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM archivos_cargados")
    cur.execute("DELETE FROM inventario_activos_datos")
    cur.execute("DELETE FROM clausulas_documentales")
    cur.execute("DELETE FROM hallazgos_dspm")
    cur.execute("DELETE FROM interacciones_coach")
    conn.commit()
    conn.close()
    return {"mensaje": "Base de datos reiniciada a cero. Espacio listo para nueva empresa."}

@app.delete("/api/documents/{archivo_id}")
def delete_document(archivo_id: int):
    conn = get_db_connection()
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

@app.post("/api/reanalyze")
def reanalyze_audit():
    ejecutar_auditoria_dspm()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as cnt FROM hallazgos_dspm")
    total = cur.fetchone()["cnt"]
    conn.close()
    return {
        "mensaje": "Reanálisis de Privacidad completado (DSPM + Router O(1)).",
        "total_brechas": total
    }

@app.post("/api/load-mockups")
def load_mockups():
    mockups_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mockups")
    if not os.path.exists(mockups_dir):
        raise HTTPException(status_code=404, detail="Directorio de mockups no encontrado.")

    sql_path = os.path.join(mockups_dir, "schema_clinica_saludtotal.sql")
    if os.path.exists(sql_path):
        procesar_archivo_sql(sql_path, "schema_clinica_saludtotal.sql")

    pdf_path = os.path.join(mockups_dir, "politica_privacidad_saludtotal.pdf")
    if os.path.exists(pdf_path):
        procesar_archivo_documento(pdf_path, "politica_privacidad_saludtotal.pdf")

    sla_path = os.path.join(mockups_dir, "contrato_encargo_sla_cloud.pdf")
    if os.path.exists(sla_path):
        procesar_archivo_documento(sla_path, "contrato_encargo_sla_cloud.pdf")

    txt_path = os.path.join(mockups_dir, "diccionario_datos_negocio.txt")
    if os.path.exists(txt_path):
        procesar_archivo_documento(txt_path, "diccionario_datos_negocio.txt")

    ejecutar_auditoria_dspm()
    return {"mensaje": "Caso completo de SaludTotal S.A.C. cargado y auditado con éxito."}

@app.post("/api/load-single-mockup/{filename}")
def load_single_mockup(filename: str):
    mockups_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "mockups")
    file_path = os.path.join(mockups_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Mockup {filename} no encontrado.")

    if filename.endswith(".sql"):
        procesar_archivo_sql(file_path, filename)
    else:
        procesar_archivo_documento(file_path, filename)

    return {
        "mensaje": f"Archivo '{filename}' ingresado a la base de datos de la empresa.",
        "necesita_reanalisis": True
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    fname = file.filename.lower()
    if fname.endswith(".sql"):
        procesar_archivo_sql(temp_path, file.filename)
    elif fname.endswith((".pdf", ".md", ".txt")):
        procesar_archivo_documento(temp_path, file.filename)
    else:
        raise HTTPException(status_code=400, detail="Formato no soportado. Suba archivos SQL, PDF, MD o TXT.")

    return {
        "mensaje": f"Archivo '{file.filename}' parseado e incorporado a la base de datos de la empresa.",
        "necesita_reanalisis": True
    }

@app.get("/api/database-view")
def get_database_view():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM archivos_cargados ORDER BY id DESC")
    archivos = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM inventario_activos_datos ORDER BY id ASC")
    inventario = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM clausulas_documentales ORDER BY id ASC")
    clausulas = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM hallazgos_dspm ORDER BY multa_estimada_uit DESC")
    hallazgos = [dict(r) for r in cur.fetchall()]

    conn.close()

    total_uit = sum(h["multa_estimada_uit"] for h in hallazgos if h["estado"] == "PENDIENTE")
    total_pen = sum(h["multa_estimada_pen"] for h in hallazgos if h["estado"] == "PENDIENTE")

    return {
        "archivos": archivos,
        "inventario": inventario,
        "clausulas": clausulas,
        "hallazgos": hallazgos,
        "resumen_impacto": {
            "total_brechas": len(hallazgos),
            "brechas_criticas": len([h for h in hallazgos if h["nivel_riesgo"] == "CRÍTICO"]),
            "multa_total_uit": round(total_uit, 1),
            "multa_total_pen": round(total_pen, 2)
        }
    }

@app.get("/api/subgraph/{control_id}")
def get_subgraph(control_id: str):
    return knowledge_bridge.extraer_subgrafo_control(control_id)

@app.post("/api/chat")
def post_chat(req: ChatRequest):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM hallazgos_dspm WHERE id = ?", (req.hallazgo_id,))
    brecha = cur.fetchone()
    if not brecha:
        conn.close()
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado.")
    
    brecha_dict = dict(brecha)

    mensajes = req.historial or []
    mensajes.append({"role": "user", "content": req.mensaje_usuario})

    respuesta = dialogar_coach(mensajes, brecha_dict)

    cur.execute("""
    INSERT INTO interacciones_coach (hallazgo_id, timestamp, rol, mensaje, pensamiento_reasoning, parche_sql)
    VALUES (?, datetime('now'), 'assistant', ?, ?, ?)
    """, (req.hallazgo_id, respuesta["content"], respuesta.get("reasoning", ""), respuesta.get("sql_patch", "")))
    conn.commit()
    conn.close()

    return {
        "mensaje": respuesta["content"],
        "reasoning": respuesta.get("reasoning", ""),
        "sql_patch": respuesta.get("sql_patch", "")
    }

@app.post("/api/remediate")
def remediate_finding(req: RemediacionRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE hallazgos_dspm SET estado = 'REMEDIADO' WHERE id = ?", (req.hallazgo_id,))
    conn.commit()
    conn.close()
    return {"mensaje": f"Hallazgo #{req.hallazgo_id} marcado como REMEDIADO con éxito."}

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
