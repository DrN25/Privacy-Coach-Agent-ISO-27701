# -*- coding: utf-8 -*-
"""
Auditor Senior de Cumplimiento & DSPM (ISO/IEC 27701:2025 y Ley 29733 ANPD)
Privacy & DSPM Multi-Agent System — Inferencia OpenRouter (deepseek/deepseek-v4.1-flash)
"""
import json
import urllib.request
import urllib.parse
import re
from typing import Dict, Any

import os
try:
    from dotenv import load_dotenv
    # Buscar .env en src/ o en raíz del proyecto TIF
    base_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_tif = os.path.dirname(base_src)
    for p in [os.path.join(base_src, ".env"), os.path.join(base_tif, ".env")]:
        if os.path.exists(p):
            load_dotenv(p)
            break
except ImportError:
    pass

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_URL = os.getenv("OPENROUTER_URL", "https://openrouter.ai/api/v1/chat/completions")
MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4.1-flash")

SYSTEM_PROMPT = """Eres el Senior Lead Privacy & DSPM Compliance Auditor, perito especializado en ISO/IEC 27701:2025 (PIMS), ISO/IEC 27001, Ley Peruana N.° 29733 (Protección de Datos Personales), su nuevo Reglamento D.S. 016-2024-JUS, la Directiva de Seguridad R.D. 019-2013-JUS y precedentes sancionadores de la Autoridad Nacional de Protección de Datos Personales (ANPD).

REGLAS ESTRICTAS DE RESPUESTA (CERO AI SLOP):
1. PROHIBIDO AI SLOP: Cero saludos ('Hola', 'Estimado equipo'), cero preámbulos diplomáticos, cero condescendencia, cero preguntas retóricas y cero conclusiones genéricas. Comienza DIRECTAMENTE con los encabezados Markdown.
2. RIGOR PERICIAL: Sé asertivo, ultra-técnico, exhaustivo en fundamentos legales y quirúrgico en ingeniería de bases de datos.
3. ESTRUCTURA OBLIGATORIA EN FORMATO MARKDOWN:
   ### 1. Diagnóstico Pericial de No Conformidad
   - **Activo / Elemento Afectado:** Identifica con precisión la tabla, columna, API o cláusula contractual.
   - **Vulnerabilidad Técnica:** Explica el vector de riesgo exacto (ej. datos sensibles de salud almacenados en texto claro, ausencia de hashing salado, retención indefinida, omisión de deber de confidencialidad en SLA).

   ### 2. Fundamentación Normativa & Tipificación ANPD
   - **Control ISO/IEC 27701:2025:** Cita el control exacto (ej. A.3.24 Cifrado en reposo, A.2.1 Políticas PIMS, A.5.15 Minimización) y su exigencia técnica.
   - **Tipificación Ley 29733 & D.S. 016-2024-JUS:** Artículo legal vulnerado y calificación de la falta (Infracción Leve, Grave o Muy Grave).
   - **Exposición Sancionadora:** Rango de multa en UIT y cálculo exacto en Soles (1 UIT = S/ 5,150).
   - **Precedente Vinculante ANPD:** Cita precedente de la Dirección de Fiscalización e Instrucción del Ministerio de Justicia y Derechos Humanos (MINJUSDH / ANPD) aplicable.

   ### 3. Remediación Técnica Inmediata
   Entrega el script de remediación definitivo en un bloque ```sql listo para producción (utilizando pgcrypto, cifrado asimétrico/simétrico, triggers de purga o hashing) o la cláusula de blindaje contractual exacta.

   ### 4. Criterio de Verificación de Auditoría
   Query SQL o procedimiento pericial concreto que certifica el cierre definitivo de la brecha.
"""

def dialogar_coach(historial_mensajes: list, contexto_brecha: dict) -> dict:
    contexto_normativo = contexto_brecha.get("contexto_normativo", {})
    prompt_usuario = f"""EXPEDIENTE TÉCNICO DE AUDITORÍA DE PRIVACIDAD:
- Hallazgo Técnico: {contexto_brecha.get('titulo', 'Vulnerabilidad crítica')} (Código: {contexto_brecha.get('codigo_regla', 'R-001')})
- Activo Afectado: {contexto_brecha.get('elemento_afectado', 'Datos de producción')}
- Control ISO/IEC 27701: {contexto_brecha.get('control_iso27701', 'A.3.24')}
- Infracción Ley 29733: {contexto_brecha.get('articulo_ley29733', 'Art. 38')}
- Directiva de Seguridad: {contexto_brecha.get('directiva_seguridad', 'Directiva R.D. 019-2013-JUS')}
- Multa Estimada ANPD: {contexto_brecha.get('multa_estimada_uit', 10.0)} UIT (S/ {contexto_brecha.get('multa_estimada_pen', 51500.0):,.2f})
- Precedente ANPD: {contexto_brecha.get('precedente_anpd', 'Resolución Directoral ANPD')}
- Subgrafo normativo verificado: {json.dumps(contexto_normativo, ensure_ascii=False)}

Requerimiento del Auditor / Ingeniero:
{historial_mensajes[-1]['content']}
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt_usuario}
    ]

    # max_tokens = 5500: DeepSeek Flash genera tokens de CoT (reasoning)
    # antes del contenido final. 5500 asegura dictamen técnico completo.
    payload = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": 5500,
        "temperature": 0.2
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://unsa.edu.pe/auditoria-tif",
        "X-Title": "TIF Auditoria PIMS UNSA"
    }

    req = urllib.request.Request(OPENROUTER_URL, data=json.dumps(payload).encode("utf-8"), headers=headers)
    
    try:
        if urllib.parse.urlparse(OPENROUTER_URL).scheme != "https":
            raise ValueError("OPENROUTER_URL debe usar HTTPS")
        # URL schemes other than HTTPS are rejected immediately above.
        with urllib.request.urlopen(req, timeout=90) as resp:  # nosec B310
            data = json.loads(resp.read().decode("utf-8"))
            choice = data.get("choices", [{}])[0]
            msg = choice.get("message", {})
            content = msg.get("content")
            reasoning = msg.get("reasoning") or msg.get("reasoning_details") or ""
            
            # Si content estuviera vacío por corte prematuro, usar reasoning como contenido
            if not content or not content.strip():
                if reasoning and reasoning.strip():
                    content = f"### Dictamen Técnico Pericial (Recuperado de Razonamiento Interno)\n\n{reasoning.strip()}"
                else:
                    content = f"Dictamen de Auditoría generado para el control {contexto_brecha.get('codigo_regla', '')}."

            # Extraer parche SQL si viene en bloque de código
            parche = ""
            for tag in ["```sql", "```SQL", "```"]:
                if tag in content:
                    partes = content.split(tag)
                    if len(partes) > 1:
                        candidate = partes[1].split("```")[0].strip()
                        if any(k in candidate.upper() for k in ["ALTER TABLE", "UPDATE ", "CREATE ", "DROP ", "INSERT "]):
                            parche = candidate
                            break
            
            # Si no se encontró en content, buscar en reasoning
            if not parche and "```sql" in reasoning:
                partes = reasoning.split("```sql")
                if len(partes) > 1:
                    parche = partes[1].split("```")[0].strip()
            
            return {
                "content": content,
                "reasoning": reasoning,
                "sql_patch": parche,
                "mode": "openrouter"
            }
    except Exception as e:
        return {
            "content": "No fue posible generar el dictamen mediante OpenRouter. Verifique credenciales, modelo y conectividad.",
            "reasoning": "",
            "sql_patch": "",
            "mode": "error",
            "error": str(e)
        }
