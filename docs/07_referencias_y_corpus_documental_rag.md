# 07. CORPUS DOCUMENTAL Y ESPECIFICACIÓN DE REFERENCIAS PARA EL SISTEMA GRAPHRAG
## Repositorio de Conocimiento Normativo, Legal Peruano y Metodológico de Auditoría

**Curso:** Auditoría de Sistemas / TI  
**Institución:** Universidad Nacional de San Agustín (UNSA) - VIII Semestre  
**Proyecto:** Trabajo de Investigación Formativa (TIF)  
**Sistema:** Agente Auditor / Capacitador en Privacidad (Privacy Awareness & Gap Coach)  
**Ubicación del Documento:** `C:\Users\Rafael\UNSA\VIII SEMESTRE\AUDITORIA\TIF\docs\07_referencias_y_corpus_documental_rag.md`

---

## 1. Justificación de la Arquitectura Seleccionada (Por qué GraphRAG frente a las Alternativas)

Antes de detallar los documentos, dejamos sentada la justificación metodológica frente a las opciones evaluadas:

| Criterio de Decisión | Alternativa A: Mega-Prompt (Contexto Largo) | Alternativa B: Reglas en Código Puro (Prowler) | Propuesta Seleccionada: GraphRAG + DSPM + Agente |
| :--- | :--- | :--- | :--- |
| **Viabilidad Local (Sin Costos)** | Inviable. Requiere enviar más de 150k tokens a la nube en cada prompt ($$$ en APIs). | Viable, pero pierde la interacción de asesoría técnica personalizada. | **100% Viable localmente**. El grafo filtra el contexto exacto (1,500 tokens) para un LLM 8B. |
| **Requisito del Docente** | No utiliza arquitectura de agentes colaborativos. | No es un agente inteligente, es solo un script estático. | **Cumple al 100%**. Agente orquestador coordina análisis técnico y diálogo didáctico. |
| **Riesgo de Alucinación** | Medio-Alto. El LLM se pierde en textos masivos de 100 páginas. | Cero, pero no tiene flexibilidad para redactar explicaciones a la MYPE. | **Cero en el veredicto** (lo da el Grafo/AST) y **controlado en la redacción** del LLM. |

---

## 2. Taxonomía Integral del Corpus Documental

El repositorio de conocimiento (*Knowledge Store*) del agente no ingiere documentos de forma homogénea o ciega. Se organiza en **cuatro capas jerárquicas**:

```
                              ARQUITECTURA DEL CORPUS DOCUMENTAL
                                               │
      ┌────────────────────┬───────────────────┴───────────────────┬────────────────────┐
      ▼                    ▼                                       ▼                    ▼
[ Capa 1: Núcleo PIMS ] [ Capa 2: Principios ]          [ Capa 3: Legal Perú ] [ Capa 4: Metodología ]
  ISO/IEC 27701:2025      ISO/IEC 29100:2024              Ley 29733, DS 003     Metodología R.M. 476-2025-JUS / ISO 27701
  (78 Controles Base)     (11 Principios Rectores)        Resoluciones ANPD     ISO 27002, 29184, 20889
```

---

## 3. Ficha Técnica Detallada de Cada Documento

### 3.1. Capa 1: Estándar Núcleo de Gestión de Privacidad (El Eje Central)

#### **ISO/IEC 27701:2025**
* **Título Oficial:** *Information security, cybersecurity and privacy protection — Privacy information management systems — Requirements and guidance*
* **Edición / Fecha:** Primera edición *Standalone* (Octubre 2025).
* **Rol en el Sistema:** Es el estándar rector. Aporta:
  * Las cláusulas de gestión (Cláusulas 4 a 10: Contexto, Liderazgo, Planificación, Soporte, Operación, Evaluación y Mejora).
  * El **Anexo A (78 controles)** dividido en:
    * *Tabla A.1:* 31 controles para **PII Controllers** (`A.1.2.2` a `A.1.4.3`).
    * *Tabla A.2:* 18 controles para **PII Processors** (`A.2.2.2` a `A.2.5.9`).
    * *Tabla A.3:* 29 controles de **Seguridad de la Información** (`A.3.3` a `A.3.31`).
  * El **Anexo B:** Guías de implementación específicas para cada uno de los 78 controles.
  * Los **Anexos C, D, E y F:** Tablas oficiales de mapeo hacia ISO 29100, GDPR, ISO 27018/29151 y la versión 2019.
* **Formato de Ingesta:** Extracción determinista mediante parser Python (`fitz`) hacia grafo JSON/NetworkX.

---

### 3.2. Capa 2: Marco de Principios de Privacidad (Referencia Normativa Obligatoria)

#### **ISO/IEC 29100:2024**
* **Título Oficial:** *Information technology — Security techniques — Privacy framework*
* **Edición / Fecha:** Edición 2024 (citada expresamente en la Tabla C.1 de la ISO 27701:2025).
* **Rol en el Sistema:**
  * Define la terminología formal de privacidad internacional (*PII*, *PII Principal*, *PII Controller*, *PII Processor*).
  * Provee los **11 Principios de Privacidad** que sustentan el diseño de cualquier software:
    1. Consent and choice *(Consentimiento y elección)*.
    2. Purpose legitimacy and specification *(Legitimidad y especificación de finalidad)*.
    3. Collection limitation *(Limitación de la recolección)*.
    4. Data minimization *(Minimización de datos)*.
    5. Use, retention and disclosure limitation *(Limitación de uso, retención y divulgación)*.
    6. Accuracy and quality *(Exactitud y calidad)*.
    7. Openness, transparency and notice *(Transparencia, apertura y notificación)*.
    8. Individual participation and access *(Participación y acceso del titular - Derechos ARCO)*.
    9. Accountability *(Responsabilidad proactiva)*.
    10. Information security *(Seguridad de la información)*.
    11. Privacy compliance *(Cumplimiento de la privacidad)*.
* **Formato de Ingesta:** Nodos de Grafo que actúan como "Categorías Padre" de los controles de la ISO 27701.

---

### 3.3. Capa 3: Marco Legal y Sancionatorio Peruano (Mandato Obligatorio del Docente)

#### **A. Ley N.° 29733 (Ley de Protección de Datos Personales del Perú)**
* **Edición / Estado:** Promulgada en 2011, con modificatorias vigentes (DL 1353 y DL 1412).
* **Rol en el Sistema:**
  * Define las obligaciones jurídicas en territorio peruano (Principio de consentimiento previo, expreso, informado e inequívoco - Art. 18; Banco de datos personales; Tratamiento transfronterizo).
  * Tipifica los derechos ARCO (Acceso, Rectificación, Cancelación y Oposición).

#### **B. Decreto Supremo N.° 003-2013-JUS (Reglamento de la Ley N.° 29733)**
* **Edición / Estado:** Vigente oficial.
* **Rol en el Sistema:**
  * Establece los requisitos formales para el consentimiento digital (casillas desmarcadas, cláusulas independientes).
  * Clasifica las infracciones en **Leves, Graves y Muy Graves** y la escala de multas aplicable.

#### **C. Directiva de Seguridad (R.D. N.° 019-2013-JUS/DGPDP)**
* **Edición / Estado:** Vigente oficial.
* **Rol en el Sistema:**
  * Determina las **Medidas de Seguridad Lógicas y Técnicas** exigidas a una base de datos en Perú según el nivel de riesgo:
    * *Nivel Básico:* Autenticación por contraseña, control de accesos, copias de seguridad periódicas.
    * *Nivel Medio:* Registro de accesos e intentos fallidos (*logs* de auditoría), separación de privilegios.
    * *Nivel Complejo:* Cifrado en reposo y en tránsito para datos sensibles (salud, biométricos, financieros).

#### **D. Compendio de Resoluciones Sancionatorias de la ANPD (MINJUSDH)**
* **Periodo de Casuística:** 2021 – 2025.
* **Rol en el Sistema:**
  * Casos reales resueltos por la Dirección de Fiscalización e Instrucción y la Dirección General de Transparencia, Acceso a la Información Pública y Protección de Datos Personales.
  * Aporta los datos concretos de multas en **Unidades Impositivas Tributarias (UIT)** para el rol de *Sensibilización*:
    * *Caso A:* Multa a empresa de e-commerce por casillas pre-marcadas en el checkout (Infracción Grave: 10 a 50 UIT).
    * *Caso B:* Sanción a centro médico por almacenar historias clínicas en base de datos sin cifrado ni bitácora de auditoría (Infracción Grave / Muy Grave: hasta 100 UIT).
    * *Caso C:* Multa por no inscribir el banco de datos de clientes ante el Registro Nacional de Protección de Datos Personales (Infracción Leve: 0.5 a 5 UIT).
* **Formato de Ingesta:** Colección de casos indexados vectorialmente (RAG Semántico) con metadatos estructurados: `{ "norma_violada": "Art. 18", "infraccion": "Grave", "multa_uit": 24, "sector": "Comercio" }`.

---

### 3.4. Capa 4: Estándares de Apoyo Metodológico y Técnico (Bibliografía ISO 27701:2025)

#### **A. Marco Metodológico de Dictamen Técnico y Evaluación de Privacidad (Alineado a ISO/IEC 27701:2025 y Ley 29733)**
* **Rol:** Proporciona la estructura del reporte de auditoría generado por el agente:
  * Criterio de auditoría (*Audit Criteria*).
  * Evidencia de auditoría (*Audit Evidence* extraída del SQL).
  * Hallazgo de auditoría (*Audit Finding*).
  * Calificación: **No Conformidad Mayor**, **No Conformidad Menor**, u **Oportunidad de Mejora**.

#### **B. ISO/IEC 27002:2022 (Controles de Seguridad de la Información)**
* **Rol:** Brinda el detalle técnico para evaluar los 29 controles de seguridad de la Tabla A.3 de la ISO 27701 (ej. Controles 8.20 Seguridad de Redes, 8.24 Cifrado, 5.15 Control de Accesos).

#### **C. ISO/IEC 29184:2020 (Avisos de Privacidad en Línea y Consentimiento)**
* **Rol:** Parámetros formales para auditar la política de privacidad de la página web de la MYPE (lenguaje claro, momento de entrega del aviso, mecanismos de retiro del consentimiento).

#### **D. ISO/IEC 20889:2018 (Técnicas de Desidentificación de Datos)**
* **Rol:** Marco conceptual para evaluar si las columnas sensibles de la base de datos SQL aplican seudonimización, hashing criptográfico con sal (*salted hash*) o enmascaramiento.

#### **E. ISO/IEC 29134:2017 (Privacy Impact Assessment - PIA / EIPD)**
* **Rol:** Guía metodológica para evaluar el control `A.1.2.6 (PIA)` cuando la MYPE procesa datos biométricos, médicos o masivos.

#### **F. GDPR (Reglamento UE 2016/679)**
* **Rol:** Actúa como puente ontológico estándar internacional gracias a la Tabla D.1 de la norma.

---

## 4. Estrategia de Ingesta Diferenciada por Tipo de Documento

Para maximizar el rendimiento y eliminar alucinaciones en un entorno local (laptop con CPU/GPU estándar), no se procesa todo con embeddings planos:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ DOCUMENTO                  TIPO DE PROCESAMIENTO        ESTRUCTURA DE ALMACENAMIENTO    │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ ISO/IEC 27701:2025         Extracción Determinista AST  Grafo de Conocimiento (JSON/Nx) │
│ ISO/IEC 29100:2024         Estructurado por Principios  Nodos Jerárquicos del Grafo     │
│ Ley 29733 / DS 003         Mapeo de Artículos / Reglas  Aristas Relacionales del Grafo  │
│ Resoluciones ANPD (Casos)  RAG Semántico Vectorial      ChromaDB Local (Embeddings BGE) │
│ Metodología R.M. 476-2025-JUS / ISO 27701             Plantilla de Prompting       System Prompt del Auditor       │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Matriz de Conexión Cruzada de Ejemplo (Lo que consultará el Agente)

Cuando el agente analice, por ejemplo, una columna `password` o `dni_cliente` en el esquema SQL, el sistema recorrerá esta cadena de relaciones pre-programada:

```
[ Hallazgo Técnico SQL ]
      │ (columna: "dni_cliente" sin cifrar y sin registro de accesos)
      ▼
[ Control ISO 27701:2025 ] ───► A.3.10 (Protection of records) & A.3.24 (Use of cryptography)
      │
      ├───► [ ISO 29100:2024 ] ───► Principle 10: Information security
      │
      ├───► [ Ley 29733 ] ────────► Art. 28 (Seguridad del tratamiento de datos personales)
      │
      ├───► [ Directiva Seg. ] ───► Medidas Nivel Básico/Medio (Cifrado y Control de Acceso)
      │
      └───► [ Precedente ANPD ] ──► Resolución Dir. N.° 018-2023-JUS/DGTAIPD
                                    (Multa de 12 UIT por almacenar documentos de identidad en texto claro)
```

---

## 6. Checklist de Archivos Requeridos en la Carpeta `Material/`

Para que el proyecto cuente con todo el corpus listo para ingesta:

- [x] `ISO 27701-2025_ocr.pdf` *(Ya presente en `Material/`, procesado con éxito)*
- [ ] `ISO_29100_2024_Framework.pdf` o extracto estructurado de sus 11 principios.
- [ ] `Ley_29733_y_Reglamento_DS_003_2013_JUS.pdf` *(Descarga pública gratuita desde MINJUSDH)*.
- [ ] `Directiva_Seguridad_RD_019_2013_JUS.pdf` *(Descarga pública gratuita desde MINJUSDH)*.
- [ ] `Compendio_Sanciones_ANPD_2021_2025.json` *(Dataset sintético/real curado con 10-15 resoluciones clave para pruebas)*.
- [ ] `Esquema_Clinica_O_Comercio.sql` *(Script SQL de prueba que simula el sistema de la MYPE)*.
