# -*- coding: utf-8 -*-
"""
Test Comparativo A/B: CON SKILL vs SIN SKILL
Evalúa el comportamiento de OpenRouter (openai/gpt-6-luna) bajo:
- Versión A: SIN SKILL (SYSTEM_PROMPT antiguo hardcodeado en coach_agent.py)
- Versión B: CON SKILL (.agents/skills/agente-incidentes-brechas/SKILL.md)

Compara las 3 consultas críticas solicitadas por el usuario:
1. Consulta 1: Explicar el hallazgo técnico y riesgo (Explicación)
2. Consulta 2: Precedente ANPD y caso más relacionado (Precedente / Caso ANPD)
3. Consulta 3: Cuantificación de multa y graduación (Graduación)
"""
import sys
import os
import json
import time

sys.path.insert(0, ".")
from src.backend.coach_agent import SYSTEM_PROMPT, obtener_system_prompt, dialogar_coach
from src.backend.knowledge_bridge import KnowledgeBridge
from src.backend.dspm_engine import get_db_connection

kb = KnowledgeBridge()
conn = get_db_connection()
cur = conn.cursor()
cur.execute("SELECT * FROM hallazgos_dspm WHERE codigo_regla = 'R-003' LIMIT 1")
row = cur.fetchone()
brecha = dict(row)
brecha["contexto_normativo"] = kb.extraer_subgrafo_control(brecha["control_iso27701"])

PROMPTS_TEST = [
    {
        "id": "Q1_EXPLICAR",
        "pregunta": "Explicame en detalle que implica este hallazgo de CVV y que riesgo concreto representa."
    },
    {
        "id": "Q2_CASO_ANPD",
        "pregunta": "y caso anpd mas relacionado o algo"
    },
    {
        "id": "Q3_MULTA",
        "pregunta": "Como se cuantifico exactamente la multa de 15 UIT y bajo que escala legal?"
    }
]

def ejecutar_consulta(system_prompt_str, historial):
    # Sobrescribimos temporalmente obtener_system_prompt para el test
    import src.backend.coach_agent as ca
    ca_original = ca.obtener_system_prompt
    ca.obtener_system_prompt = lambda: system_prompt_str
    
    try:
        t0 = time.time()
        res = ca.dialogar_coach(historial, brecha)
        duracion = time.time() - t0
        return {
            "content": res.get("content", ""),
            "reasoning": res.get("reasoning", ""),
            "duracion": round(duracion, 2)
        }
    finally:
        ca.obtener_system_prompt = ca_original

print("=======================================================================")
print("INICIANDO COMPARATIVA EMPIRICA: CON SKILL vs SIN SKILL")
print("=======================================================================")

skill_prompt = obtener_system_prompt()
legacy_prompt = SYSTEM_PROMPT

print(f"Longitud System Prompt Legacy (Sin Skill): {len(legacy_prompt)} chars")
print(f"Longitud System Prompt con Skill: {len(skill_prompt)} chars")

resultados = []

for q in PROMPTS_TEST:
    qid = q["id"]
    pregunta = q["pregunta"]
    print(f"\n-----------------------------------------------------------------------")
    print(f"EVALUANDO: {qid} -> \"{pregunta}\"")
    print(f"-----------------------------------------------------------------------")
    
    historial_base = [
        {"role": "user", "content": "Emitir dictamen pericial completo y script de remediacion."},
        {"role": "assistant", "content": "### 1. Diagnostico Tecnico y Tipificacion Legal\nActivo: pacientes.tarjeta_credito_cvv..."},
        {"role": "user", "content": pregunta}
    ]
    
    print("  > Ejecutando SIN SKILL (Legacy)...")
    res_sin = ejecutar_consulta(legacy_prompt, historial_base)
    time.sleep(1)
    
    print("  > Ejecutando CON SKILL (Skill Activa)...")
    res_con = ejecutar_consulta(skill_prompt, historial_base)
    time.sleep(1)
    
    resultados.append({
        "id": qid,
        "pregunta": pregunta,
        "sin_skill": res_sin,
        "con_skill": res_con
    })

with open("tests/comparativa_skill_vs_noskill.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, indent=2, ensure_ascii=False)

print("\n=======================================================================")
print("TEST COMPLETADO. Guardado en tests/comparativa_skill_vs_noskill.json")
print("=======================================================================")
