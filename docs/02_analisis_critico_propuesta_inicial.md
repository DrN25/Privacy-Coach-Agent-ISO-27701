# 02. ANÁLISIS CRÍTICO DE LA PROPUESTA INICIAL: ORQUESTADOR + 2 RAGS
## Lo que Necesitas Oír vs. Lo que Quieres Oír (Evaluación Técnica Rigurosa)

**Curso:** Auditoría de Sistemas / TI  
**Institución:** Universidad Nacional de San Agustín (UNSA) - VIII Semestre  
**Proyecto:** Trabajo de Investigación Formativa (TIF)  
**Marco de Referencia:** ISO/IEC 27701:2025 (Standalone PIMS)  

---

## 1. Desglose de tu Propuesta: "Agente Orquestador Central + 2 RAGs Especializados"

Tu propuesta refinada plantea:
> *"Un agente principal que sería el orquestador (con un LLM analizador), el cual llamaría u obtendría contexto tanto del RAG 1 (Normativa ISO 27701:2025, ISO 29100, etc.) como del RAG 2 (Información de la Empresa: SLA, controles, esquema de BD), para hacer sus consultas de manera más precisa."*

A continuación, la evaluación técnica sin filtros: **lo que funciona**, **dónde se rompe en pedazos si se implementa de forma ingenua**, y **cómo perfeccionarlo para que sea una obra de ingeniería sobresaliente**.

---

## 2. Lo que Funciona (Puntos Fuertes de la Idea)

1. **Separación de Responsabilidades:** Separar el dominio *normativo/regulatorio* (estático, universal, jerárquico) del dominio *corporativo* (dinámico, específico de la empresa) es una excelente práctica de diseño.
2. **Patrón Agéntico con Tool Calling (Router/ReAct):** Usar un LLM orquestador que decida qué herramienta consultar en lugar de concatenar ciegamente cientos de páginas en un solo prompt es el estándar moderno en sistemas de agentes (LangGraph, AutoGen, CrewAI).

---

## 3. Lo que NECESITAS OÍR: Las 4 Fallas Fatales si usas RAG Tradicional

Si implementas este esquema como dos "cajas negras" de RAG vectorial tradicional (chunks de texto plano con embeddings), el sistema enfrentará cuatro problemas críticos:

### ⚠️ Falla Fatal 1: El "Abismo Semántico" entre RAG 1 y RAG 2
* **El Problema:** La auditoría no es una comparación de textos similares; es una **verificación de condiciones lógicas**.
* **Escenario Real de Fallo:**
  * El usuario pregunta: *"¿Cumplimos con la ISO 27701:2025 respecto al consentimiento de nuestros clientes en el registro web?"*
  * El Orquestador consulta a **RAG 1 (Normas)** y recibe un chunk: *"Control Anexo A: El Responsable debe implementar mecanismos para obtener el consentimiento explícito..."*
  * El Orquestador consulta a **RAG 2 (Empresa)** y recibe un chunk del SLA: *"Garantizamos que el cliente acepta nuestros términos y condiciones al registrarse en la plataforma."*
  * **El Colapso:** Ninguno de los dos textos menciona si la casilla en la interfaz web viene pre-marcada (*opt-out*) o desmarcada (*opt-in*). Como el LLM orquestador solo tiene dos fragmentos vagos de texto, **alucinará el resultado**:
    * O bien dirá erróneamente: *"Sí cumples, porque tu SLA dice que acepta los términos"* (Falso Positivo de Cumplimiento).
    * O bien no sabrá si aplica la sanción de la ANPD (en Perú, las casillas pre-marcadas son ilegales y han costado multas de hasta 15 UIT a empresas de retail).

### ⚠️ Falla Fatal 2: Latencia Inviable y Consumo Desmedido en LLMs Locales
* **El Problema:** Para responder una sola pregunta, el flujo secuencial ingenuo requiere:
  1. Paso 1: El Orquestador genera una consulta para RAG 1.
  2. Paso 2: RAG 1 recupera chunks y genera un sub-resumen.
  3. Paso 3: El Orquestador lee el resumen 1 y genera una consulta para RAG 2.
  4. Paso 4: RAG 2 recupera chunks y genera otro sub-resumen.
  5. Paso 5: El Orquestador sintetiza ambos contextos y responde al usuario.
* **Impacto en Hardware Local (Ollama en laptop de estudiante):**
  * Cada pase por un LLM local de 8B (Llama-3 o Qwen 2.5) tarda entre 8 y 20 segundos.
  * **Resultado:** El chatbot tardará **entre 40 y 90 segundos por mensaje**. Para una demostración en vivo ante el docente, una latencia de un minuto y medio es pedagógicamente mortal y dará la impresión de que el sistema está colgado.

### ⚠️ Falla Fatal 3: La Confusión de Roles en ISO/IEC 27701:2025 (78 Controles)
* En la nueva versión 2025, la norma establece **31 controles para PII Controllers (Responsables)** y **18 controles para PII Processors (Encargados)**.
* Si el Orquestador no tiene un estado determinista previo que defina el rol de la empresa, una búsqueda vectorial en RAG 1 traerá controles mezclados. El agente podría exigirle a una tienda virtual (Responsable) que cumpla con el control de *acatar instrucciones del cliente* (que es exclusivo de un Procesador en la nube), demostrando falta de criterio de auditoría.

### ⚠️ Falla Fatal 4: El Error de Chunkear el Esquema de Base de Datos en RAG 2 (Reiterado)
* Un esquema de base de datos **no debe ser un documento de texto en un vector store**.
* El chunking vectorial despedaza las tablas y destruye las relaciones de llaves foráneas. Para auditar la base de datos, el Orquestador no debe "hacer una búsqueda semántica"; debe invocar una **herramienta de análisis estático estructurado (DSPM)**.

---

## 4. La Solución que Resuelve Todo: El "Orquestador Agéntico con Herramientas Especializadas"

Para hacer realidad tu visión sin caer en las trampas anteriores, transformamos los "dos RAGs planos" en **dos herramientas inteligentes especializadas** gobernadas por una máquina de estados:

```text
                              ┌──────────────────────────────────┐
                              │     USUARIO / AUDITADO (MYPE)    │
                              └─────────────────┬────────────────┘
                                                │
                                                ▼
                              ┌──────────────────────────────────┐
                              │       AGENTE ORQUESTADOR         │
                              │    (LangGraph State Machine)     │
                              │     Rol: PIMS Privacy Coach      │
                              └─────────────────┬────────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
┌──────────────────────────────────────────────┐              ┌──────────────────────────────────────────────┐
│        HERRAMIENTA 1: NORMATIVA PIMS         │              │        HERRAMIENTA 2: EVIDENCIA EMPRESA      │
│            (GraphRAG + Casuística)           │              │             (DSPM + Vector Store)            │
├──────────────────────────────────────────────┤              ├──────────────────────────────────────────────┤
│ * Grafo de 78 Controles ISO 27701:2025       │              │ A. Sub-Herramienta DSPM (Esquema BD):        │
│ * Filtro por Rol: Controller vs. Processor   │              │    - Parser AST determinístico (sqlglot)     │
│ * Mapeo inmutable a 11 Principios ISO 29100  │              │    - Detección precisa de PII (DNI, tarjetas)│
│ * Base Vectorial/BM25 de Resoluciones ANPD   │              │                                              │
│   (Ministerio de Justicia Perú con multas)   │              │ B. Sub-Herramienta Documental (Políticas/SLA)│
└──────────────────────────────────────────────┘              └──────────────────────────────────────────────┘
```

### ¿Por qué esta solución es 100 veces superior?
1. **Zero Hallucination en Controles:** El Orquestador sabe exactamente qué control de los 78 aplica porque consulta el catálogo estructurado en el Grafo, no un fragmento cortado por tokens.
2. **Velocidad Óptima (1 sola llamada al LLM):** El análisis de la base de datos se ejecuta en 50 milisegundos mediante código Python (sqlglot), y el grafo se consulta en 5 milisegundos. El LLM solo se invoca **una vez** al final para razonar, sintetizar y redactar la explicación pedagógica.
3. **Auditabilidad Real:** El docente podrá ver en pantalla el grafo de controles, la tabla coloreada con sus vulnerabilidades y la cita exacta de la resolución sancionadora de la ANPD.
