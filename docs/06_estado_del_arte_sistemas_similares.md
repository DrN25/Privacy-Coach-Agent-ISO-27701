# 06. ESTADO DEL ARTE: SISTEMAS SIMILARES Y ARQUITECTURAS DE AUTOMATIZACIÓN DE AUDITORÍAS
## Análisis Exhaustivo de Paradigmas, Repositorios Open-Source, Literatura Académica y Plataformas Comerciales

**Curso:** Auditoría de Sistemas / TI  
**Institución:** Universidad Nacional de San Agustín (UNSA) - VIII Semestre  
**Proyecto:** Trabajo de Investigación Formativa (TIF)  
**Marco Normativo:** ISO/IEC 27701:2025 (PIMS Standalone) · ISO/IEC 29100:2011 · Ley N.° 29733 (Perú)  
**Ubicación del Documento:** `C:\Users\Rafael\UNSA\VIII SEMESTRE\AUDITORIA\TIF\docs\06_estado_del_arte_sistemas_similares.md`

---

## 1. Taxonomía de Enfoques Existentes

Para abordar con rigor científico y sin sesgos la automatización de auditorías y capacitación en privacidad, se deben contrastar **cinco paradigmas principales** que conviven en la industria del software y la investigación académica:

```
                                  PARADIGMAS DE CUMPLIMIENTO Y AUDITORÍA
                                                    │
      ┌─────────────────────┬───────────────────────┼───────────────────────┬──────────────────────┐
      ▼                     ▼                       ▼                       ▼                      ▼
[ 1. Compliance-as-Code ] [ 2. Plataformas GRC ]  [ 3. RAG & Agentes ]    [ 4. Motores DSPM ]    [ 5. Literatura ]
  Determinista Puro         SaaS Continuo           LLMs & Grafos           Data Discovery         Papers IEEE/arXiv
  (NIST OSCAL, Prowler)    (Vanta, Drata, Sprinto) (AuditLens, ADCO)       (Presidio, pdscan)     (IntelliAudit)
```

---

## 2. Paradigma 1: Compliance-as-Code Determinista (Estándares Abiertos y Motores de Reglas)

Este paradigma prescinde de los Modelos de Lenguaje (LLMs) para la auditoría y confía en **especificaciones legibles por máquina y motores de inspección basados en código estático**.

---

### 2.1. NIST OSCAL (Open Security Controls Assessment Language)
* **Repositorio Oficial:** [github.com/usnistgov/OSCAL](https://github.com/usnistgov/OSCAL)
* **Comunidad y Documentación:** [oscal.io](https://oscal.io/)
* **Herramientas de Ecosistema:** [oscal-compass/compliance-to-policy](https://github.com/oscal-compass/compliance-to-policy)

#### Arquitectura y Funcionamiento:
OSCAL es un estándar en JSON/XML/YAML desarrollado por el NIST estadounidense para estandarizar catálogos de controles (ISO 27001, ISO 27701, NIST 800-53), perfiles de implementación y evidencias de auditoría.
* **Componentes Clave:**
  1. *Catalog Layer:* Define los controles y parámetros formales.
  2. *Profile Layer:* Adapta los controles a la organización (Declaración de Aplicabilidad - SoA).
  3. *Assessment Layer:* Estructura los resultados de pruebas automatizadas para auditores humanos.
* **Flujo de Trabajo:** Un pipeline de CI/CD o un agente evalúa el estado del sistema y serializa los hallazgos en un documento OSCAL estructurado.

#### Evaluación Crítica:
* **Puntos Fuertes:** Cero alucinaciones, interoperabilidad estándar internacional, determinismo matemático absoluto.
* **Puntos Débiles:** Rigidez total. No tiene capacidad de consultoría interactiva ni interpretación contextual; no explica el "porqué" ni sabe interpretar leyes locales con ambigüedad semántica (como la Ley 29733 de Perú) salvo que un humano codifique la regla exacta.

---

### 2.2. Prowler y Cloud Custodian
* **Prowler:** [github.com/prowler-cloud/prowler](https://github.com/prowler-cloud/prowler)
* **Cloud Custodian:** [github.com/cloud-custodian/cloud-custodian](https://github.com/cloud-custodian/cloud-custodian)

#### Arquitectura y Funcionamiento:
* **Prowler:** Escáner que ejecuta más de 800 pruebas deterministas sobre infraestructura (AWS, Azure, GCP, Kubernetes) mapeadas a ISO 27001, GDPR, CIS y PCI-DSS. Extrae configuraciones reales (ej. "¿Está el bucket S3 público?") y emite un veredicto booleano: `PASS` o `FAIL`.
* **Cloud Custodian:** Motor de *Policy-as-Code* basado en YAML que detecta violaciones y ejecuta la remediación automática en tiempo real.

#### Evaluación Crítica:
* **Puntos Fuertes:** Excelente para auditar infraestructura cloud con costo computacional mínimo.
* **Puntos Débiles:** Es ciego al contenido semántico de las bases de datos de una MYPE (no sabe qué almacena una columna) y no genera capacitación interactiva.

---

## 3. Paradigma 2: Plataformas Comerciales de Cumplimiento Continuo (GRC Moderno)

Compañías consolidadas que automatizan el 80% de la auditoría tradicional para startups y empresas.

---

### 3.1. Vanta y Drata
* **Sitios Oficiales:** [vanta.com](https://www.vanta.com) | [drata.com](https://drata.com)

#### Arquitectura Subyacente:
1. **Capa de Conectores API (Integraciones):** Cientos de conectores a GitHub, AWS, Jira, Datadog, Okta y bases de datos relacionales.
2. **Motor de Reglas y Evidencias:** Monitorea de forma continua (cada 1-24 horas) si las configuraciones cumplen controles de ISO 27001, ISO 27701, SOC 2 o HIPAA.
3. **Capa LLM Asistente:**
   * *Questionnaire Automation:* El LLM responde cuestionarios de seguridad de clientes usando las políticas aprobadas de la empresa.
   * *Policy Copilot:* Redacta políticas corporativas iniciales basadas en el stack detectado.

#### Evaluación Crítica:
* **Puntos Fuertes:** Líderes indiscutibles de mercado; automatización real en producción.
* **Puntos Débiles:** Suscripciones extremadamente costosas ($10,000 a $40,000 USD anuales, inaccesibles para MYPEs peruanas), código privativo cerrado, y enfoque primario en nubes y personal corporativo, con poca profundidad en el análisis de código o esquemas SQL a nivel de columnas de privacidad.

---

### 3.2. Sprinto
* **Sitio Oficial:** [sprinto.com](https://sprinto.com)
* **Enfoque:** Diseñado para empresas medianas y pequeñas en crecimiento.
* **Arquitectura:** Combina plantillas prediseñadas de políticas con agentes que se instalan en las máquinas de los empleados para monitorear cifrado de disco y antivirus, mapeando todo a controles ISO.

---

## 4. Paradigma 3: Sistemas Multi-Agente y Asistentes RAG de Código Abierto (GitHub)

Proyectos de la comunidad open-source enfocados en auditoría, cumplimiento y análisis de políticas con LLMs.

---

### 4.1. AuditLens (adhit-r/audit-lens)
* **Repositorio:** [github.com/adhit-r/audit-lens](https://github.com/adhit-r/audit-lens)
* **Arquitectura:** Motor de cumplimiento agéntico que procesa evidencias heterogéneas (documentos, logs) y genera espacios de trabajo auditables para ISO 27001, SOC 2 y HIPAA.
* **Fortaleza:** Diseñado específicamente para reducir la fricción entre el auditado y el auditor.
* **Debilidad:** Dependencia de LLMs en la nube y falta de validación de datos relacionales locales (SQL).

---

### 4.2. VerifyWise (verifywise-ai/verifywise)
* **Repositorio:** [github.com/verifywise-ai/verifywise](https://github.com/verifywise-ai/verifywise)
* **Arquitectura:** Plataforma de gobernanza y evaluación de riesgos de IA que mapea comportamientos de sistemas a ISO 27001, NIST AI RMF y el EU AI Act.
* **Fortaleza:** Mapeo formal y riguroso contra taxonomías internacionales de riesgo.
* **Debilidad:** Orientado a auditar modelos de IA, no a auditar la privacidad de una MYPE comercial tradicional.

---

### 4.3. Trust-Agent (tiffanymwr15/trust-agent)
* **Repositorio:** [github.com/tiffanymwr15/trust-agent](https://github.com/tiffanymwr15/trust-agent)
* **Arquitectura:** Gobernanza de IA en tiempo de ejecución. Detecta fugas de PII y credenciales en prompts y flujos de datos, mapeando las infracciones a controles de ISO 27001.
* **Fortaleza:** Detección activa de fuga de datos en tiempo real.
* **Debilidad:** Se enfoca en la capa de inferencia, no en la estructura de almacenamiento persistente (DDL/bases de datos).

---

### 4.4. Compliance Intelligence (Affan-cybersecuritist/compliance-intelligence)
* **Repositorio:** [github.com/Affan-cybersecuritist/compliance-intelligence](https://github.com/Affan-cybersecuritist/compliance-intelligence)
* **Arquitectura:** Espacio de trabajo asistido por IA para el análisis de brechas (*gap analysis*) de políticas de seguridad contra ISO 27001:2022.
* **Fortaleza:** Especializado en el análisis semántico de políticas y documentación textual.
* **Debilidad:** No inspecciona artefactos de software (bases de datos ni código).

---

### 4.5. ADCO (Autonomous Data & Compliance Officer)
* **Tópico en GitHub:** [compliance-automation / ADCO](https://github.com/topics/compliance-automation)
* **Arquitectura:** Enjambre de 3 micro-agentes:
  1. *Scanner Agent:* Rastrea código y bases de datos buscando cadenas PII.
  2. *Policy Matcher Agent:* Aplica RAG para contrastar hallazgos contra normativas (GDPR / ISO).
  3. *Reporter Agent:* Genera la lista de brechas y recomendaciones de remediación.
* **Fortaleza:** Desacopla la inspección técnica del razonamiento normativo.
* **Debilidad:** El Policy Matcher depende de RAG vectorial ingenuo, sufriendo de fragmentación de contexto cuando los controles tienen excepciones condicionales.

---

### 4.6. hamzasid04 / AI-Compliance-Assistant
* **Repositorio:** [github.com/hamzasid04/AI-Compliance-Assistant-](https://github.com/hamzasid04/AI-Compliance-Assistant-)
* **Arquitectura:** FastAPI + LangChain + ChromaDB. Compara PDFs de políticas internas contra un checklist de ISO 27001 y exporta un CSV con las brechas detectadas.
* **Fortaleza:** Local-first, portable y simple de entender educativamente.
* **Debilidad:** No audita bases de datos ni vincula precedentes jurídicos locales (ANPD).

---

## 5. Paradigma 4: Motores de Data Security Posture Management (DSPM) y Escáneres de PII

Herramientas especializadas en inspeccionar fuentes de datos relacionales y no relacionales para descubrir información confidencial.

---

### 5.1. Microsoft Presidio
* **Repositorio Oficial:** [github.com/microsoft/presidio](https://github.com/microsoft/presidio)
* **Arquitectura:** Combina reconocimiento léxico (Regex exacto para DNI, tarjetas, pasaportes) con NLP/NER (Named Entity Recognition con spaCy/Transformers) y un motor de anonimización (hash, redact, mask).
* **Fortaleza:** Mantenido por Microsoft, altamente extensible para incorporar formatos peruanos (DNI, RUC).
* **Debilidad:** Diseñado primariamente para texto no estructurado; requiere adaptadores para procesar esquemas SQL relacionales.

---

### 5.2. Escáneres SQL Especializados (pdscan / detectpii)
* **pdscan:** [github.com/ankane/pdscan](https://github.com/ankane/pdscan)
* **detectpii:** [github.com/thescalaguy/detectpii](https://github.com/thescalaguy/detectpii)
* **Arquitectura:** Herramientas de terminal ultraligeras que inspeccionan el diccionario de datos (`INFORMATION_SCHEMA`) en PostgreSQL, MySQL o SQLite para detectar columnas sensibles o muestrear filas.

---

## 6. Paradigma 5: Literatura Académica Reciente (Papers IEEE / arXiv 2025-2026)

Investigaciones científicas que abordan la automatización de auditorías ISO mediante LLMs:

| Paper / Estudio | Medio y Año | Aporte Técnico Principal | Conclusión Clave sobre LLMs |
| :--- | :---: | :--- | :--- |
| **IntelliAudit: Using Large Language Models to Evaluate Audit Controls** | arXiv, 2026 | Evalúa la suficiencia de evidencias heterogéneas (texto, hojas de cálculo) para controles semánticos de ISO 27001 con validación de auditores humanos. | Los LLMs fallan si se les pide emitir el veredicto final; son óptimos para evaluar suficiencia y preparar el pre-dictamen. |
| **Leveraging LLMs for Cybersecurity Compliance: Pilot Study in ISO 27001 Audit Planning** | IEEE EuroS&PW, 2025 | Asistencia en la fase de planificación de auditorías ISO 27001 evaluando confiabilidad y escalabilidad de LLMs. | Destaca la necesidad de RAG estructurado para evitar interpretaciones distorsionadas de controles de seguridad. |
| **Conceptual Framework for ISO/IEC 27001 Audit Augmentation** | Preprints, 2026 | Marco multi-modal con un **proceso de revisión en dos etapas**: auto-consistencia interna de la IA (el modelo desafía sus propios hallazgos) + revisión humana obligatoria. | Refuerza el concepto de *Cognitive Augmentation* (aumento cognitivo) frente a la automatización ciega. |
| **Systematization of Human-Centered Continuous Audit for Security Compliance** | Journal of Cybersecurity (Oxford), 2026 | Mapeo sistemático de herramientas de auditoría computarizada, pasando de motores de reglas a colaboración humano-IA. | Define que la relación óptima no es la "delegación total", sino la "colaboración interactiva humano-IA". |

---

## 7. Cuadro Comparativo Global de Paradigmas

| Criterio | Paradigma 1: Code/OSCAL | Paradigma 2: GRC SaaS (Vanta) | Paradigma 3: RAG Agéntico Abierto | Paradigma 4: DSPM (Presidio) |
| :--- | :---: | :---: | :---: | :---: |
| **Determinismo Técnico** | **100% (Código puro)** | **100% (Tests de API)** | Variable (Depende del LLM) | **95% (Heurística/NER)** |
| **Capacidad Pedagógica** | Nula (Solo flags) | Media (Asistente básico) | **Alta (Privacy Coaching y Parches SQL)** | Nula (Solo reporte) |
| **Soporte ISO 27701:2025** | Parcial (NIST OSCAL) | Propietario en actualización | Requiere dataset estructurado | Indirecto (Solo PII) |
| **Costo para MYPE** | Gratuito / Open Source | Inviable ($$$$) | **Cero / Bajo (Local)** | **Gratuito / Open Source** |
| **Análisis de Bases de Datos** | Nulo | Medio (Metadatos cloud) | Bajo (si se usa texto plano) | **Máximo (Inspección PII)** |

---

## 8. Análisis de Vulnerabilidades y Puntos Débiles de la Solución Propuesta (GraphRAG + DSPM)

Para cumplir estrictamente con el principio de **cero sesgos y rigor académico**, a continuación se detallan las limitaciones y debilidades reales de la propuesta híbrida:

### ⚠️ Debilidad 1 del GraphRAG: Costo de Mantenibilidad y Rigidez del Grafo
* **La Crítica Real:** Un grafo de conocimiento es tan bueno como las aristas que se le programen. Si la ANPD emite una nueva resolución o la ISO 27701 publica una fe de erratas, alguien debe actualizar el archivo de relaciones. Si el usuario hace una pregunta que cruza dos nodos que no tienen una arista explícita, un motor de grafo puro no encontrará el camino (*path*) y fallará, mientras que un LLM con gran ventana de contexto podría encontrar la correlación intuitivamente.

### ⚠️ Debilidad 2 del DSPM: Falso Sentido de Seguridad ante Columnas Ofuscadas (*Data Obfuscation*)
* **La Crítica Real:** Un analizador de esquemas DDL SQL basado en nombres de columnas depende de que el desarrollador use nombres coherentes (`dni`, `password`, `email`). Si un desarrollador descuidado o malicioso nombra sus columnas como `col_a1 VARCHAR(50)` o `campo_extra TEXT`, el analizador de AST y regex fallará al 100% en detectar que allí se guardan contraseñas o tarjetas, a menos que se realice un muestreo de datos reales (*data sampling/profiling*).

### ⚠️ Debilidad 3 del Agente Orquestador: Latencia y Sobrecarga en Modelos Pequeños Cuantizados
* **La Crítica Real:** Aunque se reduzca a una sola llamada final al LLM, los modelos open-source de 8B (Llama 3 o Qwen 2.5) corriendo en CPU o GPU modesta pueden sufrir para razonar sobre un JSON complejo con 5 tablas y 20 hallazgos simultáneos, requiriendo técnicas de *Structured Outputs* (JSON mode / Pydantic) estrictas para no corromper la respuesta.

---

## 9. Alternativas Arquitectónicas para Debate y Refutación

Si en tu análisis grupal decides refutar la propuesta híbrida, dispones de dos alternativas arquitectónicas viables:

### Alternativa A: Mega-Prompt de Contexto Extendido (Zero-RAG / Full Context Window)
* **Cómo funciona:** Modelos modernos (Gemini 1.5/2.0 Flash o Llama 3.1 con 128k tokens) pueden recibir **la norma ISO 27701:2025 completa (aprox. 40,000 tokens), el compendio de resoluciones de la ANPD (30,000 tokens) y el esquema SQL (5,000 tokens) directamente en el System Prompt**.
* **Ventaja:** Elimina toda la complejidad de bases de datos vectoriales, fragmentación y grafos. La IA ve el documento entero de principio a fin.
* **Desventaja:** No es viable para ejecutarse 100% en hardware local modesto de estudiantes; requiere conexión a APIs comerciales de nube y tiene un costo recurrente por millón de tokens procesados.

### Alternativa B: Motor de Cumplimiento Basado en Reglas (Estilo Prowler/OSCAL) + LLM Explicador
* **Cómo funciona:** Se programa una matriz de 78 funciones en Python puro (una por cada control). Cada función evalúa una regla determinista sobre el esquema y las respuestas del usuario. El LLM **nunca decide si se cumple o no un control**; el LLM solo recibe el reporte de fallos y genera el texto didáctico para capacitar al usuario.
* **Ventaja:** Auditabilidad matemática absoluta. Cero posibilidad de que el LLM cometa un falso positivo.
* **Desventaja:** Mayor esfuerzo de programación manual de las 78 reglas lógicas en código.
