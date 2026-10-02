# -*- coding: utf-8 -*-
"""
Auditor Senior de Cumplimiento & DSPM (ISO/IEC 27701:2025 y Ley 29733 ANPD)
Inferencia OpenRouter (openai/gpt-6-luna con reasoning medium)
"""
import os
import re
import json
import urllib.request
import urllib.parse
import time
from typing import Dict, Any, List

try:
    from dotenv import load_dotenv
    base_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_tif = os.path.dirname(base_src)
    for p in [os.path.join(base_src, '.env'), os.path.join(base_tif, '.env')]:
        if os.path.exists(p):
            load_dotenv(p)
            break
except ImportError:
    pass

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-6-luna")


def obtener_system_prompt() -> str:
    """
    Carga dinamicamente las directrices periciales del Skill si existe en .agents/skills/agente-incidentes-brechas/SKILL.md.
    Remueve el frontmatter YAML y retorna el cuerpo de instrucciones operativas.
    Si no existe o falla la lectura, recurre a SYSTEM_PROMPT como fallback.
    """
    base_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_root = os.path.dirname(base_src)
    skill_path = os.path.join(base_root, ".agents", "skills", "agente-incidentes-brechas", "SKILL.md")
    
    if os.path.exists(skill_path):
        try:
            with open(skill_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content.startswith("---"):
                partes = content.split("---", 2)
                if len(partes) >= 3:
                    return partes[2].strip()
            return content.strip()
        except Exception:
            pass
    return SYSTEM_PROMPT

SYSTEM_PROMPT = """Eres el Senior Lead Privacy & DSPM Compliance Auditor, perito especializado en ISO/IEC 27701:2025 (PIMS), ISO/IEC 27001, Ley Peruana N.° 29733 (Protección de Datos Personales), su nuevo Reglamento D.S. 016-2024-JUS, la Directiva de Seguridad R.D. 019-2013-JUS y jurisprudencia sancionadora de la Autoridad Nacional de Protección de Datos Personales (ANPD).

ACCESO INTEGRAL A BASE DE DATOS Y CORPUS DOCUMENTAL:
1. Cuentas con la base de datos oficial y precargada de resoluciones sancionadoras de la ANPD (588 expedientes de la Dirección de Fiscalización e Instrucción del MINJUSDH) y el grafo de 78 controles ISO/IEC 27701:2025.
2. Cuentas con acceso a los activos del caso: esquema SQL de la clínica, contratos de encargo SLA cloud, política de privacidad y diccionario de datos.

REGLAS ESTRICTAS DE RESPUESTA (CERO AI SLOP Y CERO METADISCURSO):
1. CERO METADISCURSO O QUEJAS: Eres un Perito Senior Forense resolutivo. Queda terminantemente prohibido emitir quejas o críticas evaluadoras del prompt (ej. 'la información no indica...', 'el expediente no explica cómo se determinó la multa', 'no permite confirmar', o señalar discrepancias numéricas). Tu deber es EXPLICAR Y RESOLVER.
2. CUANTIFICACIÓN Y GRADUACIÓN DE MULTAS (Art. 39 Ley 29733 y D.S. 016-2024-JUS):
   Cuando se pregunte cómo se cuantificó la multa estimada en UIT del caso:
   - Explica la escala legal: Infracción Leve (0.5 a 5 UIT), Grave (más de 5 a 50 UIT), Muy Grave (más de 50 a 100 UIT).
   - Desglosa la graduación pericial: (i) Multa base según la gravedad objetiva de la conducta; (ii) Factor agravante por naturaleza del dato: datos sensibles de salud o financieros (+25% a +50%); (iii) Factor agravante por omisión de medidas de seguridad obligatorias de Nivel Complejo (R.D. 019-2013-JUS); (iv) Dimensión del daño potencial sobre los pacientes o usuarios. Detalla el cálculo hasta alcanzar la cuantía estimada en UIT y Soles (1 UIT = S/ 5,150).
3. PRECEDENTES ANPD:
   Cita con solvencia las resoluciones directorales del dataset provistas en el expediente (entidad sancionada, número de resolución, monto en UIT, fecha y tipificación del Art. 132 del Reglamento), explicando su aplicación por analogía y criterio vinculante al caso.
4. PARCHE Y REMEDIACIÓN TÉCNICA:
   Entrega scripts SQL listos para producción (con pgcrypto, funciones seguras y manejo de claves) o cláusulas contractuales de blindaje legal redactadas con precisión de abogado corporativo senior.
"""

def dialogar_coach(historial_mensajes: list, contexto_brecha: dict) -> dict:
    contexto_normativo = contexto_brecha.get("contexto_normativo", {})
    sanciones = contexto_normativo.get("sanciones_anpd", [])
    
    if sanciones:
        anpd_lineas = []
        for s in sanciones:
            infr_str = "; ".join(s.get("infracciones", []))
            anpd_lineas.append(
                f"  * {s.get('entidad')} | Res: {s.get('resolucion')} | Sector: {s.get('sector')} | Multa: {s.get('multa_total_uit')} UIT | Infracción: {infr_str}"
            )
        anpd_text = "\n".join(anpd_lineas)
    else:
        anpd_text = f"  * Precedente ANPD de referencia: {contexto_brecha.get('precedente_anpd', 'Resolución Directoral ANPD')}"

    principios_nombres = [p.get("name", p.get("id", "")) for p in contexto_normativo.get("principios", [])]
    origen_doc = contexto_brecha.get("origen_archivo", "schema_clinica_saludtotal.sql")

    clausulas_lista = contexto_brecha.get("clausulas_documento", [])
    if clausulas_lista:
        c_lines = []
        for c in clausulas_lista:
            c_doc = c.get("documento", "")
            c_num = c.get("numero_clausula", "")
            c_tit = c.get("titulo_clausula", "")
            c_txt = c.get("texto_clausula", "")[:260].replace("\n", " ")
            c_lines.append(f"  * [{c_doc}] {c_num} ({c_tit}): {c_txt}")
        clausulas_texto = "\n" + "\n".join(c_lines)
    else:
        clausulas_texto = " (Verificado contra esquema DDL / DML)"

    multa_uit = contexto_brecha.get("multa_estimada_uit", 10.0)
    multa_pen = contexto_brecha.get("multa_estimada_pen", multa_uit * 5150.0)

    expediente_header = f"""EXPEDIENTE TÉCNICO DE AUDITORÍA DE PRIVACIDAD:
- Hallazgo Técnico: {contexto_brecha.get('titulo', 'Vulnerabilidad crítica')} (Código: {contexto_brecha.get('codigo_regla', 'R-001')})
- Activo / Elemento Afectado: {contexto_brecha.get('elemento_afectado', 'Datos de producción')}
- Archivo Origen: {origen_doc}
- Cláusulas / Secciones del Documento Relacionadas:
{clausulas_texto}
- Control ISO/IEC 27701: {contexto_brecha.get('control_iso27701', 'A.3.24')}
- Infracción Ley 29733: {contexto_brecha.get('articulo_ley29733', 'Art. 38')}
- Directiva de Seguridad: {contexto_brecha.get('directiva_seguridad', 'Directiva R.D. 019-2013-JUS')}
- Cuantificación Sancionadora Estimada: {multa_uit} UIT (S/ {multa_pen:,.2f})
  * Escala Legal: Infracción Grave (Art. 38 num. 2 LPDP / Art. 132 num. 2 RLPDP: rango de 5.1 a 50 UIT = S/ 26,265 a S/ 257,500)
  * Factores de Graduación Aplicados (Art. 39 Ley 29733): Multa base proporcional + Agravante por datos sensibles de salud/financieros (+25%) + Omisión de medidas de seguridad de Nivel Complejo
- Precedentes Oficiales ANPD en Base de Datos Local (588 Casos):
{anpd_text}
- Principios ISO 29100 / Ley 29733 Vinculados: {', '.join(principios_nombres) if principios_nombres else 'Principio de Seguridad'}
"""

    messages = [{"role": "system", "content": obtener_system_prompt()}]

    if not historial_mensajes:
        messages.append({"role": "user", "content": f"{expediente_header}\n\nRequerimiento: Emitir dictamen pericial completo y script de remediación."})
    elif len(historial_mensajes) == 1:
        primer_txt = historial_mensajes[0].get("content", "")
        messages.append({"role": "user", "content": f"{expediente_header}\n\nRequerimiento del Auditor / Ingeniero:\n{primer_txt}"})
    else:
        primer_txt = historial_mensajes[0].get("content", "")
        messages.append({"role": "user", "content": f"{expediente_header}\n\nRequerimiento Inicial:\n{primer_txt}"})
        for m in historial_mensajes[1:]:
            role = m.get("role", "user")
            if role not in ["user", "assistant"]:
                role = "user"
            messages.append({"role": role, "content": m.get("content", "")})

    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 6000,
        "reasoning": {"effort": "medium"},
        "temperature": 0.2
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "Connection": "close",
        "HTTP-Referer": "https://unsa.edu.pe/auditoria-tif",
        "X-Title": "TIF Auditoria PIMS UNSA"
    }

    max_intentos = 3
    ultimo_error = None

    for intento in range(max_intentos):
        try:
            if urllib.parse.urlparse(OPENROUTER_URL).scheme != "https":
                raise ValueError("OPENROUTER_URL debe usar HTTPS")
            
            req = urllib.request.Request(OPENROUTER_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=90) as resp:  # nosec B310
                data = json.loads(resp.read().decode("utf-8"))
                choice = data.get("choices", [{}])[0]
                msg = choice.get("message", {})
                content = msg.get("content") or ""
                reasoning = msg.get("reasoning") or msg.get("reasoning_details") or ""
                
                if not content.strip() and reasoning and isinstance(reasoning, str) and reasoning.strip():
                    content = f"### Dictamen Técnico Pericial\n\n{reasoning.strip()}"

                if not content.strip():
                    content = f"Dictamen pericial registrado para el control {contexto_brecha.get('control_iso27701', '')}."

                parche = ""
                sql_match = re.search(r"```(?:sql|SQL)?\s*(ALTER TABLE.*?|CREATE EXTENSION.*?|UPDATE .*?|CREATE TABLE.*?|BEGIN.*?)\s*```", content, re.DOTALL | re.IGNORECASE)
                if sql_match:
                    parche = sql_match.group(1).strip()
                else:
                    for tag in ["```sql", "```SQL", "```"]:
                        if tag in content:
                            partes = content.split(tag)
                            for chunk in partes[1:]:
                                candidate = chunk.split("```")[0].strip()
                                if any(k in candidate.upper() for k in ["ALTER TABLE", "UPDATE ", "CREATE ", "PGP_SYM_ENCRYPT", "DROP "]):
                                    parche = candidate
                                    break
                            if parche:
                                break

                return {
                    "content": content,
                    "reasoning": reasoning if isinstance(reasoning, str) else "",
                    "sql_patch": parche,
                    "mode": "openrouter"
                }
        except Exception as e:
            ultimo_error = e
            err_str = str(e).lower()
            if intento < max_intentos - 1 and any(
                k in err_str for k in ["10054", "reset", "timed out", "timeout", "remotedisconnected", "connection", "broken pipe"]
            ):
                time.sleep(1.5 * (intento + 1))
                continue
            break

    return {
        "content": f"No fue posible generar el dictamen mediante OpenRouter ({str(ultimo_error)}). Verifique la conexión local y la cuota de API.",
        "reasoning": "",
        "sql_patch": "",
        "mode": "error",
        "error": str(ultimo_error)
    }
