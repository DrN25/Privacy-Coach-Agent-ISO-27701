"""
Router del Coach de Privacidad y Remediación.
Endpoints: /api/chat, /api/remediate, /api/export-dictamen/{hallazgo_id}.
"""

import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from ...infrastructure.repository import repository
from ...knowledge_bridge import knowledge_bridge
from ...agents.graph import ejecutar_flujo_multiagente

router = APIRouter(tags=["Coach"])


class ChatRequest(BaseModel):
    hallazgo_id: int = 0
    mensaje_usuario: Optional[str] = None
    mensaje: Optional[str] = None
    historial: List[dict] = Field(default_factory=list)

    @property
    def texto_pregunta(self) -> str:
        return (self.mensaje_usuario or self.mensaje or "").strip()


class RemediacionRequest(BaseModel):
    hallazgo_id: int
    parche_sql: str


def get_dialogar_coach():
    try:
        import backend.app as app_mod
        if hasattr(app_mod, "dialogar_coach"):
            return app_mod.dialogar_coach
    except (ImportError, AttributeError):
        pass
    from ...coach_agent import dialogar_coach
    return dialogar_coach


@router.post("/api/chat")
def post_chat(req: ChatRequest):
    texto_usuario = req.texto_pregunta
    if not texto_usuario:
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")

    brecha = repository.obtener_hallazgo_por_id(req.hallazgo_id)
    if not brecha:
        # Consulta general de auditoría o normativa institucional
        brecha = {
            "id": req.hallazgo_id or 0,
            "codigo_regla": "CONSULTA_GENERAL",
            "titulo": "Consulta Institucional de Privacidad y Normativa UNSA",
            "control_iso27701": "A.5.25",
            "principio_iso29100": "P1_CONSENTIMIENTO",
            "articulo_ley29733": "Art. 13",
            "elemento_afectado": "Sistemas y Procesos UNSA",
            "origen_archivo": "Corpus Normativo Institucional UNSA",
            "directiva_seguridad": "Directiva General OTI / RCU 0103-2026",
            "multa_estimada_uit": 5.0,
            "multa_estimada_pen": 25750.0,
            "precedente_anpd": "Jurisprudencia General de Fiscalización ANPD"
        }

    # Enriquecer con contexto normativo
    brecha["contexto_normativo"] = knowledge_bridge.extraer_subgrafo_control(
        brecha.get("control_iso27701", "A.5.25")
    )

    # Cláusulas vinculadas
    conn = repository.get_conn()
    cur = conn.cursor()
    archivo_origen = brecha.get("origen_archivo", "")
    codigo_regla = brecha.get("codigo_regla", "")
    rule_pattern = f"%{codigo_regla}%"
    cur.execute("""
        SELECT documento, numero_clausula, titulo_clausula, texto_clausula, alerta_legal 
        FROM clausulas_documentales 
        WHERE titulo_clausula LIKE ? OR texto_clausula LIKE ? OR documento = ?
        ORDER BY CASE WHEN titulo_clausula LIKE ? OR texto_clausula LIKE ? THEN 0 ELSE 1 END
        LIMIT 6
    """, (rule_pattern, rule_pattern, archivo_origen, rule_pattern, rule_pattern))
    brecha["clausulas_documento"] = [dict(c) for c in cur.fetchall()]
    conn.close()

    mensajes = req.historial or []
    mensajes.append({"role": "user", "content": texto_usuario})

    # Invocación al Coach / Grafo Multi-Agente
    dialogar_fn = get_dialogar_coach()
    respuesta = dialogar_fn(mensajes, brecha)

    # Persistencia de interacción
    repository.guardar_interaccion_coach(
        hallazgo_id=req.hallazgo_id,
        rol="assistant",
        mensaje=respuesta["content"],
        reasoning=respuesta.get("reasoning"),
        parche=respuesta.get("sql_patch")
    )

    return {
        "mensaje": respuesta["content"],
        "reasoning": respuesta.get("reasoning", ""),
        "sql_patch": respuesta.get("sql_patch", ""),
        "mode": respuesta.get("mode", "openrouter"),
        "trazabilidad": respuesta.get("trazabilidad", []),
        "contexto_unsa": respuesta.get("contexto_unsa", {}),
        "error": respuesta.get("error")
    }


@router.post("/api/remediate")
def remediate_finding(req: RemediacionRequest):
    ok = repository.actualizar_estado_hallazgo(req.hallazgo_id, "REMEDIADO")
    if not ok:
        raise HTTPException(status_code=404, detail="Hallazgo no encontrado.")
    return {"mensaje": f"Hallazgo #{req.hallazgo_id} marcado como REMEDIADO con éxito."}


@router.get("/api/export-dictamen/{hallazgo_id}")
def export_dictamen(hallazgo_id: str):
    conn = repository.get_conn()
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

    ctrl_id = h_dict.get("control_iso27701", "")
    ctrl = knowledge_bridge.engine.get_control(ctrl_id) or {}

    sanciones = []
    for s in knowledge_bridge.engine.sanctions_dataset:
        if ctrl_id in s.get("iso27701_controls", []):
            sanciones.append(s)

    fecha_emision = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    monto_pen = h_dict.get("multa_estimada_pen", 0) or 0
    monto_formateado = f"{monto_pen:,.0f}" if isinstance(monto_pen, (int, float)) else str(monto_pen)

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
            rol_label = "REQUERIMIENTO DEL AUDITOR" if it.get("rol") == "user" else "DICTAMEN PERICIAL"
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
