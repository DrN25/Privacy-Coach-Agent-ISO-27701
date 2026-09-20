# 03. PROPUESTAS DE ARQUITECTURA DEL SISTEMA
## Evaluación Comparativa y Selección de la Arquitectura Óptima para el TIF

**Curso:** Auditoría de Sistemas / TI  
**Institución:** Universidad Nacional de San Agustín (UNSA) - VIII Semestre  
**Proyecto:** Trabajo de Investigación Formativa (TIF)  
**Marco Normativo Base:** ISO/IEC 27701:2025 (78 Controles Standalone) + ISO 29100 + Ley 29733  

---

## 1. Visión General de las Propuestas

Para abordar los requerimientos del docente y resolver los desafíos de auditar los **78 controles de la nueva ISO/IEC 27701:2025**, se han diseñado **tres alternativas arquitectónicas**.

---

## 2. Propuesta A: Baseline Avanzada (Dual-Stream Vector RAG + Schema Injector)

### 2.1. Descripción
Mantiene la idea inicial de separar los dominios de conocimiento en dos pipelines RAG vectoriales independientes (RAG 1: Normas ISO, RAG 2: Documentos Empresa), con un LLM orquestador central que consulta secuencialmente ambos almacenes y un inyector de texto para el DDL SQL.

### 2.2. Diagrama de Componentes
```text
[ Usuario / MYPE ] ──▶ [ Chatbot Web (React / Tailwind) ]
                                  │
                                  ▼
                    [ Orquestador FastAPI / LangChain ]
                     ├── 1. Vector Store Normativo (ChromaDB: ISO 27701:2025 + ANPD)
                     ├── 2. Vector Store Empresa (ChromaDB: SLA + Políticas)
                     └── 3. Inyector SQL (Prompt Context directo del Schema)
                                  │
                                  ▼
                         [ LLM Local / API ]
```

### 2.3. Ventajas y Desventajas
* **Ventajas:**
  * Curva de aprendizaje baja. Se puede implementar rápidamente con librerías estándar como LangChain o LlamaIndex.
* **Desventajas:**
  * **Pobre razonamiento multi-salto (*multi-hop*):** El LLM orquestador debe deducir en tiempo real cómo se relaciona una sanción de la ANPD con un control específico de los 78 controles de ISO 27701:2025.
  * **Riesgo de alucinación de controles:** Puede mezclar controles de Controllers (Anexo A: 31) con Processors (Anexo B: 18).
  * **Latencia elevada:** 3 o más llamadas secuenciales a un LLM local por consulta.

---

## 3. Propuesta B (RECOMENDADA): Arquitectura Híbrida GraphRAG + DSPM Analyzer + Agentic Reasoning

### 3.1. Descripción
Consolida tu visión del **Agente Orquestador Central**, pero reemplaza las búsquedas ciegas de texto por **dos herramientas de alto rendimiento**:
1. **Herramienta Normativa PIMS (GraphRAG):** Consulta determinista sobre el Grafo de Conocimiento de los 78 controles de ISO/IEC 27701:2025, los 11 principios de ISO 29100 y las resoluciones sancionadoras de la ANPD (MINJUSDH).
2. **Herramienta de Evidencia Corporativa (DSPM + Vector):**
   * *Sub-módulo DSPM:* Analizador sintáctico determinístico (AST con sqlglot) que parsea el esquema SQL, detecta PII y genera el semáforo de colores para el frontend.
   * *Sub-módulo Documental:* Vector store para políticas y SLAs no estructurados.

```text
                    ┌──────────────────────────────────────────────┐
                    │               INTERFAZ WEB                   │
                    │   Dashboard React + Privacy Coach Agent +      │
                    │      Visualizador DSPM de Tablas SQL         │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │           AGENTE ORQUESTADOR                 │
                    │        (LangGraph / State Machine)           │
                    │       Rol: PIMS 2025 Privacy Coach           │
                    └──────┬───────────────┼───────────────┬───────┘
                           │               │               │
            ┌──────────────┘               │               └──────────────┐
            ▼                              ▼                              ▼
┌──────────────────────┐       ┌──────────────────────┐       ┌──────────────────────┐
│     MÓDULO DSPM      │       │     GRAPHRAG PIMS    │       │   RETRIEVER HÍBRIDO  │
│  (Parser SQL + AST)  │       │ (78 Controles 2025)  │       │ (Casuística ANPD)    │
├──────────────────────┤       ├──────────────────────┤       ├──────────────────────┤
│ * Parser DDL / SQL   │       │ * 31 Controles Anx A │       │ * Resoluciones MinJus│
│ * Clasificador Regex/│       │ * 18 Controles Anx B │       │ * Multas en UIT      │
│   Presidio de PII    │       │ * 29 Controles Sec.  │       │ * Búsqueda BM25 +    │
│ * Score de Exposición│       │ * ISO 29100 + Leyes  │       │   Dense Vector Store │
└──────────────────────┘       └──────────────────────┘       └──────────────────────┘
            │                              │                              │
            └──────────────────────┬───────┴──────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────────────────────┐
                    │          LLM LOCAL / RAZONADOR               │
                    │     (Ollama: Llama-3-8B / Qwen-2.5)          │
                    │    Generación Pedagógica de Remediación      │
                    └──────────────────────────────────────────────┘
```

### 3.2. Ventajas y Desventajas
* **Ventajas:**
  * **Precisión Absoluta:** La detección de PII y la violación de controles se calcula de forma exacta sin que el LLM alucine.
  * **Trazabilidad Total:** Todo hallazgo se respalda en el Grafo de ISO 27701:2025 y en multas reales de la ANPD.
  * **Latencia Mínima:** El análisis de BD y la consulta al grafo tardan menos de 100 ms. El LLM local solo se llama una vez para generar la respuesta final.
* **Desventajas:**
  * Requiere poblar inicialmente el dataset JSON del Grafo con los 78 controles y las sanciones de la ANPD (dataset que ya queda estructurado en el proyecto).

---

## 4. Propuesta C: Multi-Agent Enterprise Orchestration (Vanta-Style Event-Driven)

### 4.1. Descripción
Emula plataformas corporativas (Vanta, Drata) con micro-agentes distribuidos mediante un bus de eventos (Redis, Celery, PostgreSQL).
* Inviable para el alcance y tiempo de un semestre universitario de 8vo ciclo.

---

## 5. Matriz de Decisión y Selección Definitiva

| Criterio de Evaluación | Propuesta A (Dual-Stream RAG) | Propuesta B (Híbrida GraphRAG + DSPM) | Propuesta C (Multi-Agente Enterprise) |
| :--- | :---: | :---: | :---: |
| **Alineamiento con ISO 27701:2025** | Parcial (Poco control de los 78) | **Total (Grafo de 78 controles)** | Total |
| **Precisión en Mapeo de BD** | Media (Riesgo de alucinación) | **Máxima (Parser AST Determinístico)** | Máxima |
| **Latencia en Hardware Local** | Alta (40 - 90 s por consulta) | **Baja (10 - 20 s por consulta)** | Alta |
| **Viabilidad en un Semestre (UNSA)** | Alta | **Óptima (Equilibrio perfecto)** | Muy Baja |
| **Impacto Visual / Demostración** | Solo Chatbot | **Chatbot + Tablas Coloreadas DSPM** | Demasiado compleja |
| **Aporte Científico / TIF** | Común | **Sobresaliente (GraphRAG + DSPM)** | Alto |

### Veredicto:
Se confirma la **Propuesta B (Arquitectura Híbrida GraphRAG + DSPM Analyzer + Agentic Reasoning)** con ISO/IEC 27701:2025.
