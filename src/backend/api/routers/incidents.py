"""
Router de Gestión de Incidentes de Seguridad y Brechas de PII (Agente 6).
Endpoints: /api/incidents, /api/incidents/{id}, /api/incidents/{id}/actions,
/api/security-logs, /api/recipients, /api/unsa-assets, /api/incidents/{id}/close,
/api/incidents/{id}/export-dictamen.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from typing import List, Dict, Any, Optional

from ...infrastructure.repository import repository
from ...core.rules_catalog import resolver_regla_con_fallback

router = APIRouter(tags=["Incidents"])


MAPA_EVIDENCIA_DOCUMENTAL = {
    "R-001": {
        "documento_fuente_pdf": "Manual_Procedimientos_Hospital_Docente_Zamacola_UNSA.pdf",
        "descripcion_documento": "Manual de Procedimientos y Custodia de Historias Clínicas (Hospital Docente Zamácola)",
        "esquema_fuente_sql": "schema_unsa_servicios_centrales.sql",
        "tabla_afectada": "pacientes_hospital_zamacola",
        "columnas_afectadas": ["diagnostico_cie10", "tratamiento_medico", "historia_clinica_numero"],
        "evidencia_texto": "Cláusula 4.2 del Manual y tabla SQL pacientes_hospital_zamacola: Almacenamiento de diagnósticos y tratamientos clínicos en texto plano sin cifrado AES-256 en reposo.",
        "clausula_observada": "Numeral 4.2: Los expedientes clínicos digitales se registrarán en la base de datos centralizada de historias clínicas para acceso del personal médico asistencial sin restricción criptográfica interna.",
        "url_pdf_raw": "/api/documents/raw?filename=Manual_Procedimientos_Hospital_Docente_Zamacola_UNSA.pdf",
        "url_sql_raw": "/api/documents/raw?filename=schema_unsa_servicios_centrales.sql"
    },
    "R-002": {
        "documento_fuente_pdf": "RCU_0085_2026_Reglamento_Admision_Pregrado_UNSA_v5.pdf",
        "descripcion_documento": "Reglamento Oficial Proceso de Admisión Pregrado versión 5 vigente (32 páginas)",
        "esquema_fuente_sql": "schema_unsa_servicios_centrales.sql",
        "tabla_afectada": "usuarios_admision_sisunsa",
        "columnas_afectadas": ["password_hash", "dni_postulante"],
        "evidencia_texto": "Tabla SQL usuarios_admision_sisunsa: Contraseñas almacenadas utilizando función hash MD5 sin salting criptográfico, expuestas a ataques de diccionario y colisión rápida.",
        "clausula_observada": "Artículo 45 del Reglamento de Admisión: El postulante accederá con su DNI y clave generada al inscribirse, almacenada en el repositorio de autenticación del portal SISADMISION.",
        "url_pdf_raw": "/api/documents/raw?filename=RCU_0085_2026_Reglamento_Admision_Pregrado_UNSA_v5.pdf",
        "url_sql_raw": "/api/documents/raw?filename=schema_unsa_servicios_centrales.sql"
    },
    "R-003": {
        "documento_fuente_pdf": "Convenio_Pasarela_Pagos_Tesoreria_BancoNacion_UNSA.pdf",
        "descripcion_documento": "Convenio de Recaudación Electrónica Págalo.pe y No Almacenamiento de CVV (R.R. 0178-2025)",
        "esquema_fuente_sql": "schema_unsa_servicios_centrales.sql",
        "tabla_afectada": "transacciones_pagos_tesoreria",
        "columnas_afectadas": ["numero_tarjeta_pan", "codigo_seguridad_cvv", "titular_tarjeta"],
        "evidencia_texto": "Tabla SQL transacciones_pagos_tesoreria: Retención indebida del código de seguridad CVV/CVC y número de tarjeta PAN con posterioridad a la autorización de pago bancario.",
        "clausula_observada": "Cláusula Quinta: La Universidad procesará los pagos con tarjeta de crédito/débito conservando en la pasarela interna los registros de transacción para conciliación contable.",
        "url_pdf_raw": "/api/documents/raw?filename=Convenio_Pasarela_Pagos_Tesoreria_BancoNacion_UNSA.pdf",
        "url_sql_raw": "/api/documents/raw?filename=schema_unsa_servicios_centrales.sql"
    },
    "R-004": {
        "documento_fuente_pdf": "Reglamento_Comedor_Universitario_SISCOM_UNSA.pdf",
        "descripcion_documento": "Reglamento de Bienestar Estudiantil y Comedores SISCOM (DUDE / RCU N° 0340-2025)",
        "esquema_fuente_sql": None,
        "tabla_afectada": "fichas_socioeconomicas_comedor",
        "columnas_afectadas": ["autorizacion_cesion_publicitaria"],
        "evidencia_texto": "Ficha Socioeconómica SISCOM: Casilla de consentimiento pre-marcada para compartir datos de contacto con patrocinadores comerciales externos como condición para becas.",
        "clausula_observada": "Artículo 18: La ficha de solicitud de beca de comedor incluirá la aceptación automática de términos de convenios de patrocinio universitario para soporte de subvenciones.",
        "url_pdf_raw": "/api/documents/raw?filename=Reglamento_Comedor_Universitario_SISCOM_UNSA.pdf",
        "url_sql_raw": None
    },
    "R-005": {
        "documento_fuente_pdf": "Reglamento_Admision_Pregrado_UNSA_2026.pdf",
        "descripcion_documento": "Reglamento General de Admisión Pregrado (Biometría, Huella, RCU N° 0103-2026)",
        "esquema_fuente_sql": "schema_unsa_servicios_centrales.sql",
        "tabla_afectada": "postulantes_biometria_historico",
        "columnas_afectadas": ["minucia_huella_dactilar", "patron_facial_biometrico"],
        "evidencia_texto": "Tabla SQL postulantes_biometria_historico: Conservación indefinida de huellas dactilares y biometría facial de 45,200 postulantes no ingresantes sin política de supresión.",
        "clausula_observada": "Artículo 29: Los registros biométricos capturados durante el examen de admisión se archivarán en el histórico institucional de la Dirección de Admisión para cotejo en procesos futuros sin plazo de caducidad.",
        "url_pdf_raw": "/api/documents/raw?filename=Reglamento_Admision_Pregrado_UNSA_2026.pdf",
        "url_sql_raw": "/api/documents/raw?filename=schema_unsa_servicios_centrales.sql"
    },
    "R-006": {
        "documento_fuente_pdf": "Contrato_DPA_Google_Workspace_Education_UNSA_2026.pdf",
        "descripcion_documento": "Acuerdo de Tratamiento de Datos (DPA) Google Workspace for Education (R.R. 0089-2026)",
        "esquema_fuente_sql": None,
        "tabla_afectada": "backups_s3_cloud_eu_west",
        "columnas_afectadas": ["expedientes_academicos_tar"],
        "evidencia_texto": "Copias de seguridad de OTI: Transferencia transfronteriza y almacenamiento de expedientes académicos en servidores de la región UE/EEUU sin DPA específico ni registro ante ANPD.",
        "clausula_observada": "Cláusula Novena: Los respaldos de datos de alumnos y docentes podrán replicarse en centros de datos internacionales del proveedor de nube para fines de alta disponibilidad.",
        "url_pdf_raw": "/api/documents/raw?filename=Contrato_DPA_Google_Workspace_Education_UNSA_2026.pdf",
        "url_sql_raw": None
    },
    "R-007": {
        "documento_fuente_pdf": "TUPA_UNSA_Procedimientos_Administrativos_2026.pdf",
        "descripcion_documento": "TUPA Institucional UNSA (Procedimientos de Derechos ARCO y Tasas - R.R. 0214-2026)",
        "esquema_fuente_sql": None,
        "tabla_afectada": "solicitudes_arco_tramited",
        "columnas_afectadas": ["comprobante_pago_tupa"],
        "evidencia_texto": "Procedimiento N° 14 del TUPA Institucional: Exigencia de pago de tasa administrativa de S/ 28.50 y carta notarial para atender solicitudes de Acceso, Rectificación, Cancelación u Oposición (ARCO).",
        "clausula_observada": "Procedimiento 14 TUPA: 'Ejercicio de Derechos ARCO': Requisitos: 1. Formulario Único de Trámite (FUT). 2. Recibo de pago de tasa por derecho de trámite de S/ 28.50 en Caja Central. 3. Carta notarial de acreditación.",
        "url_pdf_raw": "/api/documents/raw?filename=TUPA_UNSA_Procedimientos_Administrativos_2026.pdf",
        "url_sql_raw": None
    }
}


@router.get("/api/incidents")
def list_incidents():
    """Retorna la lista de incidentes y brechas institucionales enriquecidos con evidencia documental."""
    incidentes = repository.listar_incidentes_unsa()
    enriquecidos = []
    for inc in incidentes:
        item = dict(inc)
        regla_cod = inc.get("regla_codigo") or "R-001"
        evidencia = MAPA_EVIDENCIA_DOCUMENTAL.get(regla_cod, {})
        item.update({
            "documento_fuente_pdf": evidencia.get("documento_fuente_pdf"),
            "esquema_fuente_sql": evidencia.get("esquema_fuente_sql"),
            "tabla_afectada": evidencia.get("tabla_afectada"),
            "url_pdf_raw": evidencia.get("url_pdf_raw"),
            "url_sql_raw": evidencia.get("url_sql_raw"),
        })
        enriquecidos.append(item)
    return {
        "incidents": enriquecidos,
        "incidentes": enriquecidos,
        "total": len(enriquecidos)
    }


@router.get("/api/incidents/{incident_id}")
def get_incident(incident_id: int):
    """Retorna el detalle completo de una brecha con su evidencia documental y paquete de remediación."""
    inc = repository.obtener_incidente_unsa(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    regla_codigo = inc.get("regla_codigo") or "R-001"
    regla_info = resolver_regla_con_fallback(regla_codigo)
    evidencia = MAPA_EVIDENCIA_DOCUMENTAL.get(regla_codigo, {})

    acciones = repository.listar_acciones_incidente(incident_id)
    historial = repository.listar_historial_incidente(incident_id)

    res = dict(inc)
    res.update({
        "regla": regla_info,
        # Evidencia Documental y Trazabilidad Física
        "documento_fuente_pdf": evidencia.get("documento_fuente_pdf"),
        "descripcion_documento": evidencia.get("descripcion_documento"),
        "esquema_fuente_sql": evidencia.get("esquema_fuente_sql"),
        "tabla_afectada": evidencia.get("tabla_afectada"),
        "columnas_afectadas": evidencia.get("columnas_afectadas", []),
        "evidencia_texto": evidencia.get("evidencia_texto"),
        "clausula_observada": evidencia.get("clausula_observada"),
        "url_pdf_raw": evidencia.get("url_pdf_raw"),
        "url_sql_raw": evidencia.get("url_sql_raw"),
        "remediacion_db_sql": regla_info.get("remediacion_db_sql"),
        "remediacion_software_nosql": regla_info.get("remediacion_software_nosql"),
        "remediacion_juridica": regla_info.get("remediacion_juridica"),
        "remediacion_organizativa": regla_info.get("remediacion_organizativa"),
        "aviso_legal_anpd": regla_info.get("aviso_legal_anpd"),
        "acciones": acciones,
        "historial": historial,
        # Backward compatibility
        "incidente": inc,
        "remediacion": {
            "db_sql": regla_info.get("remediacion_db_sql"),
            "software_nosql": regla_info.get("remediacion_software_nosql"),
            "juridica": regla_info.get("remediacion_juridica"),
            "organizativa": regla_info.get("remediacion_organizativa"),
            "aviso_legal_anpd": regla_info.get("aviso_legal_anpd")
        }
    })
    return res


@router.get("/api/incidents/{incident_id}/actions")
def get_incident_actions(incident_id: int):
    """Retorna las acciones de contención, remediación y mitigación."""
    acciones = repository.listar_acciones_incidente(incident_id)
    return {
        "actions": acciones,
        "acciones": acciones
    }


@router.get("/api/incidents/{incident_id}/history")
def get_incident_history(incident_id: int):
    """Retorna la línea de tiempo forense."""
    historial = repository.listar_historial_incidente(incident_id)
    return {
        "history": historial,
        "historial": historial
    }


@router.post("/api/incidents/{incident_id}/close")
def close_incident(incident_id: int):
    """Actualiza el estado del incidente a cerrado tras verificar remediación."""
    success = repository.actualizar_estado_incidente(incident_id, "C")
    return {
        "success": success,
        "nuevo_estado": "C",
        "mensaje": f"Incidente {incident_id} cerrado formalmente tras verificar remediación."
    }


@router.get("/api/security-logs")
def list_security_logs(incident_id: Optional[int] = None):
    """Retorna las trazas técnicas de seguridad disparadoras (demo.core_securitylog)."""
    logs = repository.listar_trazas_seguridad()
    if incident_id:
        logs = [l for l in logs if l.get("incident_id") == incident_id]
    return {
        "logs": logs,
        "total": len(logs)
    }


@router.get("/api/recipients")
def list_recipients():
    """Retorna el directorio oficial de notificación de brechas (demo.core_incidentrecipient)."""
    dest = repository.listar_destinatarios_notificacion()
    return {
        "recipients": dest,
        "destinatarios": dest
    }


@router.get("/api/unsa-assets")
def list_unsa_assets():
    """Retorna los activos y sistemas institucionales de la UNSA (demo.core_asset)."""
    activos = repository.listar_activos_unsa()
    return {
        "assets": activos,
        "activos": activos,
        "total": len(activos)
    }


@router.get("/api/incidents/{incident_id}/export-dictamen", response_class=PlainTextResponse)
def export_incident_dictamen(incident_id: int):
    """Genera y descarga el Dictamen Pericial Oficial bajo ISO 27035 y Ley 29733 (7 secciones)."""
    inc = repository.obtener_incidente_unsa(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    regla = resolver_regla_con_fallback(inc.get("regla_codigo", "R-001"))
    acciones = repository.listar_acciones_incidente(incident_id)

    lineas = [
        "================================================================================",
        "DICTAMEN PERICIAL OFICIAL DE BRECHA DE DATOS PERSONALES (PII BREACH)",
        "Universidad Nacional de San Agustín de Arequipa (UNSA) - CSIRT UNSA / DPO",
        "Conforme a ISO/IEC 27035-1/2/3, ISO/IEC 27701:2025 Cl. 7.2.9 y D.S. N° 016-2024-JUS",
        "================================================================================\n",
        "SECCIÓN I: METADATOS Y CADENA DE CUSTODIA",
        f"1. Código de Incidente: {inc.get('incident_code')} (ID: {inc.get('id')})",
        "2. Entidad: Universidad Nacional de San Agustín de Arequipa (RUC: 20140798781)",
        "3. Representante Legal: Dr. Hugo Rojas Flores (Rector)",
        f"4. Oficial de Privacidad: {inc.get('dpo_contact_name', 'Abog. Carlos Mendoza Valdivia')}",
        f"5. Sistema Afectado: {inc.get('compromised_system', 'Sistema UNSA')}",
        f"6. Endpoint / URL: {inc.get('affected_url', 'N/A')}",
        f"7. Fecha Detección: {inc.get('detection_date', '2026-10-24')} {inc.get('detection_time', '08:45:00')}\n",
        "SECCIÓN II: TRIAJE Y CALIFICACIÓN DE BRECHA (ISO 27701 A.5.25)",
        f"1. Regla Canónica: [{regla['codigo']}] {regla['titulo']}",
        f"2. Tipo de Incidente: {'Brecha de Confidencialidad (BF)' if inc.get('incident_type') == 'BF' else 'Infracción de Principios (PI)'}",
        f"3. Severidad / Impacto: Severidad '{inc.get('severity', 'A')}' | Impacto '{inc.get('impact', 'C')}'",
        f"4. Titulares Afectados: {inc.get('num_affected_subjects', 0):,} ciudadanos/estudiantes",
        f"5. Tipología de Datos: {inc.get('affected_data_types', [])}\n",
        "SECCIÓN III: EVALUACIÓN DE RIESGO PARA LOS TITULARES (Cl. 7.2.9)",
        "- Nivel de Riesgo Evaluado: CRÍTICO / ALTO",
        "- Notificación a Titulares: Requerida por la naturaleza de los datos comprometidos.\n",
        "SECCIÓN IV: TIPIFICACIÓN Y TASACIÓN ANPD (Art. 38 y 39 Ley 29733)",
        f"1. Precedente ANPD Vinculante: {regla['precedente_anpd']}",
        f"2. Exposición Sancionadora Estimada: {inc.get('multa_estimada_uit', 0.0):.1f} UIT (S/ {inc.get('multa_estimada_pen', 0.0):,.2f})\n",
        "SECCIÓN V: MEDIDAS DE CONTENCIÓN ADOPTADAS (A.5.26)",
        "- Desconexión perimetral, bloqueo de credenciales y aislamiento del vector vulnerable.\n",
        "SECCIÓN VI: PLAN DE REMEDIACIÓN MULTIDIMENSIONAL (A.5.26)",
    ]

    if regla.get("remediacion_db_sql"):
        lineas.extend([
            "--- [CAPA 1: REMEDIACIÓN BASE DE DATOS SQL] ---",
            regla["remediacion_db_sql"],
            ""
        ])

    if regla.get("remediacion_software_nosql"):
        lineas.extend([
            "--- [CAPA 2: REMEDIACIÓN SOFTWARE / CLOUD / NO-SQL] ---",
            regla["remediacion_software_nosql"],
            ""
        ])

    lineas.extend([
        "--- [CAPA 3: MEDIDA JURÍDICA Y CONTRACTUAL] ---",
        regla["remediacion_juridica"],
        "",
        "--- [CAPA 4: DIRECTIVA INSTITUCIONAL Y POLÍTICA] ---",
        regla["remediacion_organizativa"],
        "",
        "SECCIÓN VII: CÉDULA DE NOTIFICACIÓN OFICIAL ANPD (48 HORAS)",
        f"Aviso Regulatorio: {regla['aviso_legal_anpd']}",
        "Destinatario Oficial: anpd.denuncias@minjus.gob.pe (Mesa de Partes MINJUSDH)",
        "Estado del Trámite: Notificación formal tramitada por el Despacho Rectoral.",
        "================================================================================"
    ])

    return "\n".join(lineas)
