# ARQUITECTURA DUAL GRAPHRAG Y ESTADO DEL ARTE DOCUMENTAL DE LA UNSA
**Sistema Multi-Agente de Auditoría de Privacidad y Brechas PII (Agente 6)**  
*Marco Normativo: ISO/IEC 27701:2025, ISO/IEC 29100:2024, Ley N° 29733 y D.S. N° 016-2024-JUS*  
*Universidad Nacional de San Agustín de Arequipa (UNSA) — Trabajo de Investigación Formativa (TIF)*

---

## 1. EL ESTADO DEL ARTE DOCUMENTAL DE LA UNSA (DOBLE NIVEL: CORPUS CANÓNICO Y CORPUS REAL AUTÉNTICO)

Para evitar la generación de "silos de datos" y reflejar con fidelidad institucional la realidad operativa de la UNSA, el sistema maneja una arquitectura documental en dos niveles complementarios:

### A. Corpus Institucional Real Auténtico (Descargado de DSpace y Portales UNSA)
Documentos oficiales descargados directamente desde los servidores de la universidad (`transparencia.unsa.edu.pe`, `www.unsa.edu.pe`, `posgrado.unsa.edu.pe`, `fad.unsa.edu.pe`), almacenados en `media/documents/originales_unsa/`:

| N° | Archivo Real Descargado | Fuente / Servidor Oficial | Páginas | Tipo de Contenido | Procesamiento Requerido |
|:---|:---|:---|:---:|:---|:---|
| **01** | `RR_0503_2026_Creacion_CSIRT_UNSA.pdf` (414 KB) | DSpace Transparencia (Handle 1814) | 4 | Resolución Rectoral firmada | **RapidOCR (Escaneado)** |
| **02** | `RR_0987_2025_Designacion_Oficial_Proteccion_Datos_UNSA.pdf` (551 KB) | DSpace Transparencia (Handle 1627) | 5 | Designación oficial DPO UNSA | **RapidOCR (Escaneado)** |
| **03** | `RR_1234_2026_Designacion_Oficial_Gobierno_Datos_UNSA.pdf` (381 KB) | DSpace Transparencia (Handle 1916) | 4 | Designación Oficial Gobierno Datos | **RapidOCR (Escaneado)** |
| **04** | `RR_1244_2025_Designacion_Oficial_Seguridad_Confianza_Digital_UNSA.pdf` (348 KB) | DSpace Transparencia (Handle 1702) | 3 | Designación OSCD (CISO) | **RapidOCR (Escaneado)** |
| **05** | `RCU_0085_2026_Reglamento_Admision_Pregrado_UNSA_v5.pdf` (2.5 MB) | DSpace Transparencia (Handle 1795) | 32 | Reglamento Oficial Admisión v5 | **RapidOCR (Escaneado)** |
| **06** | `RR_1130_2026_TUPA_Procedimiento_Grados_Titulos_UNSA.pdf` (589 KB) | DSpace Transparencia (Handle 1894) | 12 | TUPA Oficial Proc. 73 Grados | **RapidOCR (Escaneado)** |
| **07** | `Convenios_Oficiales_Suscritos_UNSA_2009_2026.pdf` (1.07 MB) | DSpace Transparencia (Handle 1941) | 82 | Reporte Oficial Convenios (593k chars) | **PyMuPDF Nativo** |
| **08** | `Reglamento_Proteccion_Datos_Estudiantes_UNSA.pdf` (2.3 MB) | Posgrado UNSA Portal | 18 | Reglamento Estudiantes (Privacidad) | **RapidOCR (Escaneado)** |
| **09** | `Padron_Miembros_Mesa_Elecciones_Pregrado_UNSA.pdf` (926 KB) | Portal Central UNSA | 27 | Padrón Electoral con DNI/CUI (85k chars)| **PyMuPDF Nativo** |
| **10** | `Resultados_Ingresantes_Posgrado_IIFase_UNSA.pdf` (471 KB) | Posgrado UNSA Portal | 22 | Resultados concurso con DNI postulantes | **PyMuPDF Nativo** |

### B. Corpus Canónico de Auditoría y Aseguramiento Técnico (media/documents/)
Fixtures estructurados en PDF y SQL creados para pruebas unitarias de regresión continua, verificación de umbrales financieros UIT y aseguramiento de que las 7 reglas canónicas de brecha de datos (R-001 a R-007) cuenten con patrones deterministas garantizados.

---

## 2. LA ARQUITECTURA DUAL GRAPHRAG: ¿CÓMO SE CONECTAN AMBOS MUNDOS?

El sistema no utiliza un RAG plano tradicional (que se limita a buscar fragmentos de texto por similitud de coseno en vectores), sino una **Arquitectura Dual GraphRAG** donde conviven dos grafos interconectados:

```
+----------------------------------------------------+       +------------------------------------------------------+
|       GRAFO 1: TEÓRICO / NORMATIVO (NetworkX)      |       |      GRAFO 2: DOCUMENTAL / EMPRESARIAL (PostgreSQL)  |
|                                                    |       |                                                      |
|   [ISO/IEC 27701:2025 Controls] (142 nodos)        |       |   [Documentos Institucionales UNSA] (11 fuentes)     |
|              |                                     |       |              |                                       |
|              v                                     |       |              v                                       |
|   [ISO/IEC 29100 Principles] (11 principios)       |       |   [Cláusulas / Artículos Segmentados] (PyMuPDF/OCR)  |
|              |                                     |       |              |                                       |
|              v                                     |       |              v                                       |
|   [Ley 29733 & D.S. 003-2013-JUS] (Infracciones)   |       |   [Activos de Información & Esquemas SQL AST]        |
|              |                                     |       |              |                                       |
|              v                                     |       |              v                                       |
|   [Precedentes Sancionadores ANPD] (588 casos)     |       |   [Columnas Sensibles PII: Salud, Tarjetas, Creds]   |
+----------------------------------------------------+       +------------------------------------------------------+
                         \                                                /
                          \                                              /
                           v                                            v
                      +------------------------------------------------------+
                      |      PUENTE DE FUSIÓN DETERMINISTA (O(1) Stitching)  |
                      |                                                      |
                      |  * Columna sin cifrar -> Dispara A.3.24 + R-001      |
                      |  * Hash MD5 -> Dispara A.3.19 + R-002                |
                      |  * Retención infinita -> Dispara A.1.2.11 + R-005    |
                      |  * Traba notarial ARCO -> Dispara A.1.2.18 + R-007   |
                      +------------------------------------------------------+
                                                 |
                                                 v
                      +------------------------------------------------------+
                      |        ORQUESTADOR MULTI-AGENTE (LangGraph)          |
                      |                                                      |
                      |  Context -> Profiler -> DSPM -> Normative -> Coach   |
                      |                                                      |
                      |  * Genera Solución Técnica Directa (SQL / Software)  |
                      |  * Cuantifica Multa ANPD en UIT y Soles              |
                      |  * Emite Cédula de Notificación de Brecha en 48h     |
                      +------------------------------------------------------+
```

### Grafo 1: El Grafo Normativo (Theoretical Knowledge Graph)
- **Implementación**: `src/backend/graph_engine.py` (`PIMSGraphEngine`).
- **Naturaleza**: Estático, precargado en memoria RAM en milisegundos mediante `networkx`.
- **Contenido**:
  - **142 Controles de Privacidad de ISO/IEC 27701:2025** (Mapeados a ISO 27001/27002:2022).
  - **11 Principios Rectores de ISO/IEC 29100:2024** (Consentimiento, Licitud, Finalidad, Seguridad, etc.).
  - **Escala de Infracciones de la Ley N° 29733** (Art. 38 y Art. 132 del Reglamento: Leves, Graves, Muy Graves).
  - **588 Resoluciones Sancionadoras Reales de la ANPD**: Casos reales emitidos por la Dirección de Fiscalización (Clínica Montefiori, BCP, BBVA, bancos de postulantes) con medidas correctivas dictadas y multas impuestas.
- **Función**: Responder *"¿Qué exige la norma internacional, cuál es el precedente administrativo y cuál es la multa aplicable?"*.

### Grafo 2: El Grafo Documental y de Datos de la UNSA (Local Data & Asset Graph)
- **Implementación**: `src/backend/services/document_processor.py` y `src/backend/infrastructure/repository.py`.
- **Naturaleza**: Dinámico, respaldado por la base de datos relacional (`unsa_pims_db.demo` y SQLite local).
- **Contenido**:
  - **Activos de Información (`demo.core_asset`)**: 10 activos institucionales ancla (SISUNSA, Hospital Zamácola, SISADMISION, Google Workspace, Moodle, Archivo Central, TRAMITED, UNSApay, SISTUTORIA, SISCOM).
  - **Estructura AST de Tablas y Columnas (`inventario_activos_datos`)**: Detectadas mediante parseo AST sintáctico (`sqlglot`) con tipología de datos, llaves foráneas y categorización PII.
  - **Cláusulas Documentales Segmentadas (`clausulas_documentales`)**: Artículos extraídos de los PDFs (mediante PyMuPDF nativo o RapidOCR cuando hay texto escaneado) con banderas de conformidad o alerta legal.
- **Función**: Responder *"¿Qué activos posee la universidad, qué datos personales trata y qué cláusulas regulan dichos tratamientos?"*.

---

## 3. ¿CÓMO SE ANALIZAN LOS DOCUMENTOS? (PIPELINE PASO A PASO)

Cuando un documento ingresa al sistema (sea mediante el corpus precargado o subido por el usuario en `/api/upload`), se somete al siguiente pipeline:

### Paso 1: Ingesta Criptográfica y Extracción Textual Híbrida
```
PDF / DDL SQL / Markdown ---> [Hash SHA-256] ---> Cadena de Custodia Legal
      |
      +---> ¿Es archivo SQL?
      |         |
      |         v
      |     [Parseo AST sqlglot] ---> Tablas, Columnas, Data Types, Constraints
      |
      +---> ¿Es archivo PDF?
                |
                v
            [PyMuPDF fitz.open]
                |
                v
            ¿Página con texto < 40 chars?
                |-- SÍ --> [RapidOCR onnxruntime] (Extracción visual de pixmap)
                |-- NO --> [PyMuPDF page.get_text()] (Extracción directa rápida)
```

### Paso 2: Segmentación Semántica y Perfilado de Datos
- **En Esquemas SQL**: Cada columna es evaluada por el `profiler.py` aplicando el **Candado 1** (taxonomía canónica + regex cerradas para identificar diagnósticos médicos, passwords, números de tarjeta PAN, CVV, biometría).
- **En Documentos PDF/Texto**: El documento es segmentado en artículos o cláusulas normativas. Si la cláusula contiene términos observados como `"TÁCITA"`, `"INDEFINIDO"`, `"SIN PLAZO DE PURGA"`, `"TRANSFRONTERIZ"`, `"EXTRANJERO SIN REGISTRO"`, `"NOTARIAL"` o `"TASA"`, se le asigna el estado `OBSERVADO`.

### Paso 3: Fusión y Correlación Cruzada (Dual Graph Stitching)
El motor de auditoría (`AuditService`) ejecuta las 7 reglas canónicas de la ISO 27701:
1. Toma el hallazgo del **Grafo Documental** (ej. Columna `hospital_historias_clinicas.datos_sensibles_salud` sin cifrar).
2. Localiza en el **Grafo Normativo** el Control ISO `A.3.24` (Cifrado de datos personales).
3. Conecta el subgrafo con el **Principio de Seguridad de la ISO 29100**.
4. Tipifica la infracción en la **Ley N° 29733** (Art. 38 num. 2 literal c: No adoptar medidas técnicas de seguridad).
5. Recupera el precedente análogo de la ANPD (Resolución Directoral N° 1045-2020-JUS / R.D. 89-2021-JUS - Clínica Montefiori).
6. Calcula la exposición en multas: **12.5 UIT = S/ 64,375.00**.

### Paso 4: Generación de la Solución Técnica Directa y Dictamen
El motor genera:
- **Capa Técnica (Zero AI-Slop)**: Script SQL defensivo (`ALTER TABLE ... ADD COLUMN ... pgcrypto`) o script de software (Argon2id, AWS CLI, React checkbox).
- **Capa Regulatoria**: Cédula de Notificación de Brecha en 48 horas bajo D.S. N° 016-2024-JUS.
- **Dictamen Pericial Descargable**: Informe oficial de 7 secciones bajo la norma ISO/IEC 27035 y Ley 29733.

---

## 4. INTEGRACIÓN INTER-AGENTE A2A (`unsa-mind:8001`)

Adicionalmente, el sistema cuenta con el cliente **Protocolo A2A v0.3.0** (`src/backend/infrastructure/unsa_a2a_client.py`).  
Cuando el auditor o el usuario formulan preguntas abiertas en el Asistente DPO (`/api/chat`) sobre regulaciones universitarias internas:
1. El `normative_agent` detecta términos clave agustinos (`unsa`, `admision`, `comedor`, `matricula`).
2. Dispara una llamada JSON-RPC 2.0 por HTTP hacia `http://localhost:8001/a2a` al agente institucional `unsa-mind`.
3. Si `unsa-mind` está en línea, devuelve citas oficiales vigentes de las resoluciones de Consejo Universitario.
4. Si está fuera de línea o el repositorio interno no cuenta con directiva propia, el Agente aplica automáticamente el **principio de supletoriedad legal**, fundamentando el dictamen directamente en la Ley N° 29733 y el estándar ISO/IEC 27701:2025.

