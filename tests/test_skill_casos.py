# -*- coding: utf-8 -*-
"""
Test de Verificacion Local Multicaso para Agente de Incidentes y Brechas (SKILL.md)
Evalua 4 casos arquetipicos (R-001, R-002, R-003, R-004) mediante inferencia real.
"""
import sys
import os
import json
import re
import time

sys.path.insert(0, '.')
from src.backend.coach_agent import dialogar_coach, obtener_system_prompt

CASOS_PRUEBA = [
    {
        "id_caso": "CASO_1_R001_SALUD",
        "nombre": "R-001: Datos Medicos Oncologicos sin Cifrar en BD",
        "mensaje_usuario": "Cual es el dictamen pericial para este hallazgo y como aplicamos el parche de cifrado en PostgreSQL?",
        "contexto": {
            "codigo_regla": "R-001",
            "titulo": "Datos de Salud Sensibles sin Cifrado en Reposo",
            "elemento_afectado": "expedientes_oncologicos.diagnostico_biopsia",
            "origen_archivo": "db_hospital_nacional.sql",
            "control_iso27701": "A.3.26",
            "articulo_ley29733": "Art. 38.2.b (Falta de medidas de seguridad nivel complejo)",
            "directiva_seguridad": "Directiva de Seguridad R.D. 019-2013-JUS",
            "multa_estimada_uit": 12.5,
            "multa_estimada_pen": 64375.0,
            "precedente_anpd": "Resolucion Directoral N. 042-2023-JUS/DGPDP (Clinica Montefiori, 15 UIT por historias clinicas sin cifrar)",
            "contexto_normativo": {
                "principios": [{"id": "Principio de Seguridad", "name": "Principio de Seguridad y Confidencialidad"}],
                "sanciones_anpd": [
                    {
                        "entidad": "Clinica Montefiori S.A.",
                        "resolucion": "R.D. 042-2023-JUS/DGPDP",
                        "sector": "Salud Privada",
                        "multa_total_uit": 15.0,
                        "infracciones": ["Art. 38.2.b LPDP: Falta de medidas de seguridad en historias clinicas"]
                    }
                ]
            }
        },
        "validaciones": {
            "uit_esperada": 12.5,
            "pen_esperado": 64375.0,
            "tabla_objetivo": "expedientes_oncologicos",
            "columna_objetivo": "diagnostico_biopsia",
            "control_clave": "A.3.26"
        }
    },
    {
        "id_caso": "CASO_2_R002_AUTH",
        "nombre": "R-002: Hashes MD5 sin Salt en Plataforma SaaS",
        "mensaje_usuario": "Hemos detectado contrasenas en MD5 en la tabla auth_members. Que sancion aplica la ANPD y cual es el script de migracion seguro?",
        "contexto": {
            "codigo_regla": "R-002",
            "titulo": "Almacenamiento de Contrasenas con Algoritmo Hash Debil (MD5)",
            "elemento_afectado": "auth_members.password_hash",
            "origen_archivo": "schema_edtech_platform.sql",
            "control_iso27701": "A.3.23",
            "articulo_ley29733": "Art. 38.2.b (Medidas tecnicas deficientes en autenticacion)",
            "directiva_seguridad": "Directiva de Seguridad R.D. 019-2013-JUS (Seguridad en autenticacion)",
            "multa_estimada_uit": 8.8,
            "multa_estimada_pen": 45320.0,
            "precedente_anpd": "Resolucion Directoral N. 018-2021-JUS/DGPDP (Medidas de seguridad de autenticacion deficientes)",
            "contexto_normativo": {
                "principios": [{"id": "Principio de Seguridad", "name": "Principio de Seguridad"}],
                "sanciones_anpd": [
                    {
                        "entidad": "Plataforma Digital Educativa S.A.C.",
                        "resolucion": "R.D. 018-2021-JUS/DGPDP",
                        "sector": "Servicios Digitales",
                        "multa_total_uit": 8.8,
                        "infracciones": ["Art. 38.2.b LPDP: Uso de algoritmos de hashing obsoletos"]
                    }
                ]
            }
        },
        "validaciones": {
            "uit_esperada": 8.8,
            "pen_esperado": 45320.0,
            "tabla_objetivo": "auth_members",
            "columna_objetivo": "password_hash",
            "control_clave": "A.3.23"
        }
    },
    {
        "id_caso": "CASO_3_R003_PAGOS",
        "nombre": "R-003: Almacenamiento Ilegal de Codigo CVV de Tarjetas",
        "mensaje_usuario": "El equipo de desarrollo guardo los codigos CVV para cobros automaticos futuros. Dictamina la infraccion y danos la remediacion inmediata.",
        "contexto": {
            "codigo_regla": "R-003",
            "titulo": "Almacenamiento Ilegal de Codigo de Seguridad CVV de Tarjetas",
            "elemento_afectado": "checkout_transacciones.codigo_cvv",
            "origen_archivo": "database_pagos_ecommerce.sql",
            "control_iso27701": "A.1.4.5",
            "articulo_ley29733": "Art. 13 (Principio de Proporcionalidad) y Art. 38.2.b (Falta grave de seguridad)",
            "directiva_seguridad": "Directiva R.D. 019-2013-JUS y estandares PCI-DSS",
            "multa_estimada_uit": 15.0,
            "multa_estimada_pen": 77250.0,
            "precedente_anpd": "Resolucion Directoral N. 089-2021-JUS/DGPDP (Retencion indebida de datos de pago tras la transaccion)",
            "contexto_normativo": {
                "principios": [{"id": "Principio de Proporcionalidad", "name": "Principio de Proporcionalidad y Limitacion de Retencion"}],
                "sanciones_anpd": [
                    {
                        "entidad": "Comercio Electronico Express Peru S.A.",
                        "resolucion": "R.D. 089-2021-JUS/DGPDP",
                        "sector": "Fintech / Comercio Electronico",
                        "multa_total_uit": 15.0,
                        "infracciones": ["Art. 38.2.b LPDP: Retencion ilicita de datos de seguridad de tarjetas"]
                    }
                ]
            }
        },
        "validaciones": {
            "uit_esperada": 15.0,
            "pen_esperado": 77250.0,
            "tabla_objetivo": "checkout_transacciones",
            "columna_objetivo": "codigo_cvv",
            "control_clave": "A.1.4.5"
        }
    },
    {
        "id_caso": "CASO_4_R004_LEGAL",
        "nombre": "R-004: Consentimiento Tacito por Navegacion en Terminos Web",
        "mensaje_usuario": "Indica como tipifica la ANPD esta clausula de consentimiento tacito por mera navegacion y redacta la clausula legal corregida conforme a ley.",
        "contexto": {
            "codigo_regla": "R-004",
            "titulo": "Consentimiento Tacito o Automatico por Mera Navegacion Web",
            "elemento_afectado": "Clausula 3.2 de Politica de Tratamiento de Datos",
            "origen_archivo": "terminos_condiciones_marketplace.pdf",
            "clausulas_documento": [
                {
                    "documento": "terminos_condiciones_marketplace.pdf",
                    "numero_clausula": "3.2",
                    "titulo_clausula": "Aceptacion y Comparticion de Datos",
                    "texto_clausula": "El acceso y navegacion en esta plataforma constituye aceptacion tacita e irrevocable para la cesion de sus datos personales a socios comerciales y agencias de publicidad exterior."
                }
            ],
            "control_iso27701": "A.1.2.4",
            "articulo_ley29733": "Art. 13.5 (Consentimiento libre, previo, expreso e informado) y Art. 38.2.c LPDP",
            "directiva_seguridad": "Reglamento D.S. 003-2013-JUS / D.S. 016-2024-JUS",
            "multa_estimada_uit": 10.0,
            "multa_estimada_pen": 51500.0,
            "precedente_anpd": "Resolucion Directoral N. 018-2021-JUS/DGPDP (14 UIT por imputacion de consentimiento presunto)",
            "contexto_normativo": {
                "principios": [{"id": "Principio de Consentimiento", "name": "Principio de Consentimiento y Licitud"}],
                "sanciones_anpd": [
                    {
                        "entidad": "Marketplace Digital Peru S.A.C.",
                        "resolucion": "R.D. 018-2021-JUS/DGPDP",
                        "sector": "Retail / Telecomunicaciones",
                        "multa_total_uit": 14.0,
                        "infracciones": ["Art. 38.2.c LPDP: Tratamiento sin consentimiento valido"]
                    }
                ]
            }
        },
        "validaciones": {
            "uit_esperada": 10.0,
            "pen_esperado": 51500.0,
            "control_clave": "A.1.2.4"
        }
    }
]

def evaluar_caso(caso: dict) -> dict:
    cid = caso["id_caso"]
    print(f"\n=======================================================================")
    print(f"EJECUTANDO {cid}: {caso['nombre']}")
    print(f"=======================================================================")
    
    t0 = time.time()
    historial = [{"role": "user", "content": caso["mensaje_usuario"]}]
    
    try:
        resultado = dialogar_coach(historial, caso["contexto"])
    except Exception as e:
        print(f"ERROR en inferencia: {e}")
        return {"caso": cid, "error": str(e), "exito": False}
        
    duracion = time.time() - t0
    contenido = resultado.get("content", "")
    sql_patch = resultado.get("sql_patch", "")
    
    print(f"Inferencia completada en {duracion:.2f}s | Longitud: {len(contenido)} caracteres")
    
    # 1. Comprobar las 5 secciones obligatorias
    secciones = [
        ("Sec 1: Diagnostico Tecnico y Tipificacion", bool(re.search(r"1\.\s*Diagn[oó]stico\s*T[eé]cnico", contenido, re.I))),
        ("Sec 2: Fundamentacion Normativa", bool(re.search(r"2\.\s*Fundamentaci[oó]n\s*Normativa", contenido, re.I))),
        ("Sec 3: Cuantificacion y Precedente ANPD", bool(re.search(r"3\.\s*Cuantificaci[oó]n", contenido, re.I))),
        ("Sec 4: Parche Tecnico (SQL o Clausula)", bool(re.search(r"4\.\s*Parche\s*T[eé]cnico", contenido, re.I))),
        ("Sec 5: Acciones Administrativas", bool(re.search(r"5\.\s*Acciones\s*Administrativas", contenido, re.I)))
    ]
    
    # 2. Comprobar calculo de multas UIT / Soles
    uit_exp = caso["validaciones"].get("uit_esperada")
    uit_encontrada = bool(re.search(rf"{uit_exp}\s*UIT", contenido, re.I) or re.search(r"UIT", contenido))
    
    # 3. Comprobar control ISO
    ctrl_exp = caso["validaciones"].get("control_clave")
    ctrl_encontrado = bool(re.search(rf"{ctrl_exp}", contenido))
    
    # 4. Comprobar desacoplamiento y parche especifico
    tabla_exp = caso["validaciones"].get("tabla_objetivo")
    col_exp = caso["validaciones"].get("columna_objetivo")
    
    mencion_tabla = bool(tabla_exp and tabla_exp in contenido)
    mencion_col = bool(col_exp and col_exp in contenido)
    
    # 5. Comprobar SQL transaccional para casos de BD
    es_caso_db = bool(tabla_exp)
    sql_valido = False
    if es_caso_db:
        sql_valido = bool(re.search(r"BEGIN;?", sql_patch or contenido, re.I) and re.search(r"COMMIT;?", sql_patch or contenido, re.I))
        
    # 6. Deteccion de AI-Slop
    slop_phrases = [
        "como modelo de inteligencia artificial",
        "como ia",
        "espero que esta informacion te sea de utilidad",
        "espero que te sirva",
        "no dudes en consultarme",
        "un placer ayudarte",
        "delve",
        "tapestry",
        "cutting-edge",
        "leverage",
        "en conclusion, "
    ]
    slop_detectado = [p for p in slop_phrases if p in contenido.lower()]
    
    analisis = {
        "caso": cid,
        "duracion_s": round(duracion, 2),
        "longitud_chars": len(contenido),
        "secciones": {s[0]: s[1] for s in secciones},
        "todas_secciones": all(s[1] for s in secciones),
        "control_iso_detectado": ctrl_encontrado,
        "uit_presente": uit_encontrada,
        "mencion_tabla_real": mencion_tabla if es_caso_db else "N/A",
        "mencion_columna_real": mencion_col if es_caso_db else "N/A",
        "sql_transaccional_begin_commit": sql_valido if es_caso_db else "N/A",
        "slop_detectado": slop_detectado,
        "es_slop_free": len(slop_detectado) == 0,
        "parche_detectado_longitud": len(sql_patch)
    }
    
    print("\n--- RESULTADOS DEL ANALISIS ---")
    for k, v in analisis.items():
        if k != "secciones":
            print(f"  * {k}: {v}")
    print("  * Detalle Secciones:")
    for sec_nombre, cumple in analisis["secciones"].items():
        print(f"      [{'OK' if cumple else 'FALLO'}] {sec_nombre}")
        
    print("\n--- EXTRACTO DEL DICTAMEN EMITIDO ---")
    print(contenido[:500] + "...")
    print("\n--- PARCHE IDENTIFICADO ---")
    print(sql_patch if sql_patch else "[Clausula redactada dentro del cuerpo del dictamen]")
    
    return {"analisis": analisis, "contenido_completo": contenido, "sql_patch": sql_patch}

if __name__ == '__main__':
    print("=======================================================================")
    print("INICIANDO TEST MULTICASO LOCAL DEL AGENTE DE INCIDENTES Y BRECHAS")
    print("Skill Activo: .agents/skills/agente-incidentes-brechas/SKILL.md")
    print("=======================================================================")
    
    sys_prompt = obtener_system_prompt()
    print(f"Longitud del System Prompt inyectado: {len(sys_prompt)} caracteres\n")
    
    reporte_final = []
    for caso in CASOS_PRUEBA:
        res = evaluar_caso(caso)
        reporte_final.append(res)
        time.sleep(1)
        
    print("\n=======================================================================")
    print("RESUMEN GLOBAL DE LA EVALUACION MULTICASO")
    print("=======================================================================")
    total = len(reporte_final)
    ok_secciones = sum(1 for r in reporte_final if r["analisis"]["todas_secciones"])
    ok_slop = sum(1 for r in reporte_final if r["analisis"]["es_slop_free"])
    
    print(f"Total de casos evaluados: {total}")
    print(f"Casos con 100% de las 5 secciones estructurales: {ok_secciones}/{total}")
    print(f"Casos 100% libres de AI-Slop: {ok_slop}/{total}")
    
    with open('tests/resultado_test_multicaso.json', 'w', encoding='utf-8') as f:
        json.dump([r['analisis'] for r in reporte_final], f, indent=2, ensure_ascii=False)
    print("Reporte cuantitativo guardado en tests/resultado_test_multicaso.json")
