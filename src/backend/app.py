import os
import shutil
import base64
import binascii
import secrets
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Path
from fastapi.responses import JSONResponse, Response
import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .db import init_db, get_db_connection
from .ingestion import procesar_archivo_sql, procesar_archivo_documento
from .dspm_engine import ejecutar_auditoria_dspm
from .knowledge_bridge import knowledge_bridge
from .coach_agent import dialogar_coach


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if os.getenv("ENVIRONMENT", "development") == "production":
        if not os.getenv("APP_USERNAME") or not os.getenv("APP_PASSWORD"):
            raise RuntimeError("APP_USERNAME y APP_PASSWORD son obligatorios en producción")
    init_db()
    yield

app = FastAPI(
    title="Privacy & DSPM Multi-Agent System",
    description="Sistema Multi-Agente de Auditoría de Privacidad (ISO 27701, ISO 29100, Ley 29733) con React y OpenRouter DeepSeek",
    version="2.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def production_basic_auth(request, call_next):
    if os.getenv("ENVIRONMENT", "development") != "production" or request.url.path == "/api/status":
        return await call_next(request)

    authorization = request.headers.get("Authorization", "")
    try:
        scheme, encoded = authorization.split(" ", 1)
        username, password = base64.b64decode(encoded).decode("utf-8").split(":", 1)
    except (ValueError, UnicodeDecodeError, binascii.Error):
        scheme, username, password = "", "", ""

    valid_user = secrets.compare_digest(username, os.getenv("APP_USERNAME", ""))
    valid_password = secrets.compare_digest(password, os.getenv("APP_PASSWORD", ""))
    if scheme.lower() != "basic" or not (valid_user and valid_password):
        return JSONResponse(
            status_code=401,
            content={"detail": "Autenticación requerida"},
            headers={"WWW-Authenticate": 'Basic realm="Privacy Coach"'},
        )
    return await call_next(request)

@app.exception_handler(OSError)
async def os_error_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Ruta inválida en sistema operativo"})

cors_origins = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class ChatRequest(BaseModel):
    hallazgo_id: int
    mensaje_usuario: str
    historial: List[dict] = Field(default_factory=list)

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
        "llm_model": os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash"),
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
    if filename != os.path.basename(filename):
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido.")
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
        procesar_archivo_sql(temp_path, safe_filename)
    else:
        procesar_archivo_documento(temp_path, safe_filename)

    return {
        "mensaje": f"Archivo '{safe_filename}' parseado e incorporado a la base de datos de la empresa.",
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

@app.get("/api/legal-reference/{tipo}/{ref_id}")
def get_legal_reference(tipo: str, ref_id: str):
    """
    Devuelve contenido original de controles ISO 27701, artículos de Ley 29733 o sanciones ANPD.
    tipo: "control" | "articulo" | "sancion"
    ref_id: "A.1.4.5" | "Art_13" | "42" (id numérico de sanción)
    """
    import json as _json
    datasets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "knowledge_base", "datasets")
    datasets_dir = os.path.normpath(datasets_dir)

    if tipo == "control":
        ctrl = knowledge_bridge.engine.get_control(ref_id)
        if not ctrl:
            raise HTTPException(status_code=404, detail=f"Control {ref_id} no encontrado.")
        principios = []
        for p_str in ctrl.get("iso29100_principles", []):
            p_id = p_str.split(":")[0].strip()
            princ = knowledge_bridge.engine.get_principle(p_id)
            if princ:
                principios.append(princ)
        return {
            "tipo": "control",
            "data": ctrl,
            "principios_vinculados": principios
        }

    elif tipo == "articulo":
        ley_path = os.path.join(datasets_dir, "ley_29733_articulos.json")
        if not os.path.exists(ley_path):
            raise HTTPException(status_code=404, detail="Dataset de Ley 29733 no encontrado.")
        with open(ley_path, "r", encoding="utf-8") as f:
            ley_data = _json.load(f)
        articulo = ley_data.get("articulos", {}).get(ref_id)
        if not articulo:
            for k, v in ley_data.get("articulos", {}).items():
                if ref_id.replace("Art. ", "Art_").replace("Art ", "Art_") == k or str(v.get("articulo")) == ref_id:
                    articulo = v
                    ref_id = k
                    break
        if not articulo:
            raise HTTPException(status_code=404, detail=f"Artículo {ref_id} no encontrado.")
        return {
            "tipo": "articulo",
            "id": ref_id,
            "data": articulo
        }

    elif tipo == "sancion":
        try:
            sid = int(ref_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="ID de sanción debe ser numérico.")
        for s in knowledge_bridge.engine.sanctions_dataset:
            if s.get("id") == sid:
                return {
                    "tipo": "sancion",
                    "data": s
                }
        raise HTTPException(status_code=404, detail=f"Sanción {ref_id} no encontrada.")

    else:
        raise HTTPException(status_code=400, detail="Tipo debe ser 'control', 'articulo' o 'sancion'.")


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
    brecha_dict["contexto_normativo"] = knowledge_bridge.extraer_subgrafo_control(
        brecha_dict["control_iso27701"]
    )

    archivo_origen = brecha_dict.get("origen_archivo", "")
    codigo_regla = brecha_dict.get("codigo_regla", "")
    rule_pattern = f"%{codigo_regla}%"
    cur.execute("""
        SELECT documento, numero_clausula, titulo_clausula, texto_clausula, alerta_legal 
        FROM clausulas_documentales 
        WHERE titulo_clausula LIKE ? OR texto_clausula LIKE ? OR documento = ?
        ORDER BY CASE WHEN titulo_clausula LIKE ? OR texto_clausula LIKE ? THEN 0 ELSE 1 END
        LIMIT 6
    """, (rule_pattern, rule_pattern, archivo_origen, rule_pattern, rule_pattern))
    brecha_dict["clausulas_documento"] = [dict(c) for c in cur.fetchall()]

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
        "sql_patch": respuesta.get("sql_patch", ""),
        "mode": respuesta.get("mode", "openrouter"),
        "error": respuesta.get("error")
    }

@app.post("/api/remediate")
def remediate_finding(req: RemediacionRequest):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE hallazgos_dspm SET estado = 'REMEDIADO' WHERE id = ?", (req.hallazgo_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado.")
    conn.commit()
    conn.close()
    return {"mensaje": f"Hallazgo #{req.hallazgo_id} marcado como REMEDIADO con éxito."}

@app.get("/api/export-dictamen/{hallazgo_id}")
def export_dictamen(hallazgo_id: str):
    """
    Genera y descarga un dictamen pericial estructurado en formato Markdown (.md)
    para el hallazgo especificado, integrando metadatos, subgrafo normativo,
    precedentes ANPD y el historial pericial completo de deliberación.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    if hallazgo_id.isdigit():
        cur.execute("SELECT * FROM hallazgos_dspm WHERE id = ?", (int(hallazgo_id),))
    else:
        cur.execute("SELECT * FROM hallazgos_dspm WHERE codigo_regla = ?", (hallazgo_id,))
    h = cur.fetchone()
    if not h:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Hallazgo {hallazgo_id} no encontrado")
    
    h_dict = dict(h)
    
    cur.execute("SELECT * FROM interacciones_coach WHERE hallazgo_id = ? ORDER BY id ASC", (h_dict["id"],))
    interacciones = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    # Subgrafo normativo y control
    ctrl_id = h_dict.get("control_iso27701", "")
    ctrl = knowledge_bridge.engine.get_control(ctrl_id) or {}
    
    # Precedentes vinculados
    sanciones = []
    for s in knowledge_bridge.engine.sanctions_dataset:
        if ctrl_id in s.get("iso27701_controls", []):
            sanciones.append(s)

    fecha_emision = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    monto_pen = h_dict.get("multa_estimada_pen", 0) or 0
    monto_formateado = f"{monto_pen:,.0f}" if isinstance(monto_pen, (int, float)) else str(monto_pen)
    
    # Construcción del dictamen estructurado en Markdown
    md_lines = [
        "# DICTAMEN PERICIAL DE AUDITORÍA Y CUMPLIMIENTO DSPM",
        f"**Expediente de No Conformidad:** `{h_dict.get('codigo_regla', 'R-XXX')}`",
        f"**Título:** {h_dict.get('titulo', 'Sin título')}",
        f"**Fecha de Emisión:** `{fecha_emision}`",
        "**Estándares de Referencia:** ISO/IEC 27701:2025, ISO/IEC 29100:2024, Ley 29733 (ANPD Perú)",
        f"**Estado de Remediación:** `{h_dict.get('estado', 'PENDIENTE')}`",
        "",
        "---",
        "",
        "## 1. RESUMEN EJECUTIVO Y FICHA TÉCNICA DEL HALLAZGO",
        f"- **Activo / Elemento Afectado:** `{h_dict.get('elemento_afectado', 'N/A')}`",
        f"- **Nivel de Riesgo:** `{h_dict.get('nivel_riesgo', 'ALTO')}`",
        f"- **Origen Documental/Código:** `{h_dict.get('origen_archivo', 'N/A')}`",
        f"- **Control ISO/IEC 27701:2025:** `{ctrl_id}` - *{ctrl.get('title', 'Control de Privacidad')}*",
        f"- **Tipificación Ley 29733:** {h_dict.get('articulo_ley29733', 'N/A')}",
        f"- **Directiva de Seguridad:** {h_dict.get('directiva_seguridad', 'N/A')}",
        f"- **Exposición Sancionadora Estimada:** **{h_dict.get('multa_estimada_uit', 0)} UIT** (S/ {monto_formateado})",
        "",
        "### Descripción Pericial",
        f"> {h_dict.get('descripcion', 'Sin descripción')}",
        "",
        "---",
        "",
        "## 2. FUNDAMENTACIÓN NORMATIVA Y CONTROL ISO/IEC 27701:2025",
        f"- **Categoría:** {ctrl.get('category', 'Controles Operacionales de Privacidad')}",
        f"- **Rol Organizacional:** {ctrl.get('role', 'Shared (Controller & Processor)')}",
        f"- **Tabla Normativa:** {ctrl.get('table', 'A.1 / A.3')}",
        "",
        "### Principios ISO/IEC 29100 Vinculados:",
    ]
    
    for p in ctrl.get("iso29100_principles", []):
        md_lines.append(f"- **{p}**")
        
    peru_bridge = ctrl.get("peru_legal_bridge", {})
    if peru_bridge:
        md_lines.extend([
            "",
            "### Puente Legal Perú (Ley 29733 & D.S. 003-2013-JUS):",
            f"- **Ley 29733:** {peru_bridge.get('ley_29733', 'N/A')}",
            f"- **Reglamento D.S. 003-2013-JUS:** {peru_bridge.get('ds_003_2013_jus', 'N/A')}",
            f"- **Directiva de Seguridad:** {peru_bridge.get('directiva_seguridad', 'N/A')}",
        ])

    md_lines.extend([
        "",
        "---",
        "",
        "## 3. PRECEDENTES SANCIONADORES ANPD Y ANÁLISIS DE CASOS HISTÓRICOS",
    ])
    
    if sanciones:
        for idx, s in enumerate(sanciones[:3], 1):
            md_lines.extend([
                f"### Caso {idx}: {s.get('entidad', 'Entidad')} ({s.get('resolucion', 'R.D.')})",
                f"- **Sector:** {s.get('sector', 'General')}",
                f"- **Sanción Impuesta:** **{s.get('multa_uit', 0)} UIT** ({s.get('monto_pen', 'S/ 0')})",
                f"- **Infracción Tipificada:** {s.get('infraccion', 'N/A')}",
                f"- **Criterio de Graduación:** {s.get('criterio_graduacion', 'N/A')}",
                f"- **Medida Correctiva:** {s.get('medida_correctiva', 'N/A')}",
                "",
            ])
    else:
        md_lines.append(f"- Precedente registrado: {h_dict.get('precedente_anpd', 'Resolución Directoral ANPD')}")
        md_lines.append("")

    md_lines.extend([
        "---",
        "",
        "## 4. HISTORIAL DE DELIBERACIÓN Y DICTÁMENES PERICIALES (AUDITOR IA)",
    ])
    
    if interacciones:
        for it in interacciones:
            rol_label = "👤 REQUERIMIENTO DEL AUDITOR" if it.get("rol") == "user" else "🤖 DICTAMEN PERICIAL (IA)"
            md_lines.append(f"### {rol_label} [{it.get('timestamp', '')}]")
            if it.get("pensamiento_reasoning"):
                md_lines.append(f"> **Cadena de Razonamiento:**\n> {it.get('pensamiento_reasoning')}\n")
            md_lines.append(it.get("mensaje", ""))
            if it.get("parche_sql"):
                md_lines.append(f"\n```sql\n{it.get('parche_sql')}\n```")
            md_lines.append("")
    else:
        md_lines.append("*Sin deliberaciones registradas en la consola pericial para este expediente.*")
        md_lines.append("")

    md_lines.extend([
        "---",
        "",
        "## 5. RECOMENDACIONES DE REMEDIACIÓN DEFENSIVA",
        "1. **Implementación Técnica / Documental Inmediata:** Proceder según las pautas correctivas generadas por el auditor de cumplimiento.",
        "2. **Actualización del Registro de Actividades de Tratamiento (RAT):** Modificar el inventario de datos y flujos de información en cumplimiento de la Directiva de Seguridad.",
        "3. **Verificación de Eficacia:** Ejecutar re-análisis de DSPM para constatar el paso del estado a `REMEDIADO` y mitigar la exposición ante la ANPD.",
        "",
        "---",
        "*Dictamen pericial generado automáticamente por el Sistema Multi-Agente DSPM & Privacy Compliance (UNSA TIF).*",
        ""
    ])
    
    report_content = "\n".join(md_lines)
    codigo = h_dict.get("codigo_regla", "EXP").replace(" ", "_")
    
    return Response(
        content=report_content,
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="Dictamen_Pericial_{codigo}.md"'
        }
    )

frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
