# 05. PLAN DE IMPLEMENTACIÓN Y GUÍA DE SUSTENTACIÓN DEL TIF
## Hoja de Ruta Tecnológica, Stack y Defensa Académica para el 8vo Semestre

**Curso:** Auditoría de Sistemas / TI  
**Institución:** Universidad Nacional de San Agustín (UNSA) - VIII Semestre  
**Proyecto:** Trabajo de Investigación Formativa (TIF)  

---

## 1. Stack Tecnológico Recomendado (100% Viable y Local)

Para garantizar que el sistema pueda ejecutarse y defenderse en vivo en la laptop del equipo sin depender de costosas suscripciones de nube o APIs externas que fallen por falta de crédito o conexión a internet:

| Capa | Tecnología Seleccionada | Justificación Técnica para el TIF |
| :--- | :--- | :--- |
| **Backend API** | **FastAPI (Python 3.11+)** | Asíncrono, generación automática de Swagger/OpenAPI docs, integración nativa con ecosistemas de IA. |
| **Parsing SQL (DSPM)** | **sqlglot + Regex Engine** | Analizador léxico y sintáctico (AST) ultraligero y completo y verificado. No requiere base de datos activa para parsear esquemas .sql. |
| **Knowledge Graph (GraphRAG)** | **NetworkX / SQLite** | Grafo en memoria ultrarrápido ((1)$) guardado en JSON o SQLite. Elimina la necesidad de levantar un servidor pesado de Neo4j en la sustentación. |
| **Vector Store (Casuística)** | **ChromaDB / FAISS** | Almacén vectorial embebido, ligero y sin dependencias externas complejas. |
| **LLM Local / Motor IA** | **Ollama (llama3:8b / qwen2.5:7b)** | Inferencia 100% local, privada y offline. Se puede cambiar dinámicamente a Claude/Gemini API mediante variables de entorno si se desea máxima potencia. |
| **Frontend UI** | **React (Vite) + Tailwind CSS + Lucide** | Interfaz moderna, responsiva, con dark mode, semáforo de riesgo y visualizador de tablas de base de datos. |

---

## 2. Cronograma de Desarrollo por Sprints (4 Fases)

```text
[ Fase 1: Corpus & Grafo ] ──▶ [ Fase 2: DSPM & Backend ] ──▶ [ Fase 3: Frontend Web ] ──▶ [ Fase 4: Pruebas & Demo ]
     (Semana 1 - 2)                   (Semana 3)                    (Semana 4)                    (Semana 5)
```

### Fase 1: Estructuración del Grafo Normativo y Corpus de Casuística (Semanas 1 - 2)
* **Dataset de Controles:** Crear el archivo data/iso27701_controls.json con los 31 controles del Anexo A (Controllers), 18 controles del Anexo B (Processors) y su mapeo a los 11 principios de ISO 29100.
* **Corpus de Jurisprudencia ANPD:** Recopilar de 15 a 25 resoluciones sancionadoras públicas del portal de la ANPD (MINJUSDH) en formatos de casos tipo (Retail, Fintech, Clínicas, Call Centers, Colegios).
* **Construcción del Grafo:** Script en Python que carga la ontología en NetworkX.

### Fase 2: Motor DSPM y Orquestación Agéntica (Semana 3)
* Implementar el endpoint /api/analyze-schema que recibe un archivo .sql y retorna la lista de tablas coloreadas por riesgo con sus violaciones normativas asociadas.
* Implementar el endpoint /api/chat que ejecuta la recuperación híbrida (Grafo + Casuística) e inyecta el System Prompt de Capacitador en Ollama.

### Fase 3: Desarrollo del Frontend y Visualizador DSPM (Semana 4)
* Vista 1: **Dashboard de Estado de Cumplimiento:** Resumen ejecutivo de la MYPE, score PIMS y brechas detectadas.
* Vista 2: **Visualizador DSPM de Base de Datos:** Tarjetas de tablas con badges de color por columna (Azul = PII básica, Amarillo = PII identificable, Rojo = Crítico, Púrpura = Sensible) y alertas al hacer clic.
* Vista 3: **Privacy Coach Agent:** Chat en tiempo real con sugerencias de preguntas rápidas (*"¿Qué sanción arriesgo por no cifrar contraseñas?"*, *"¿Qué controles de ISO 27701 aplican a mi e-commerce?"*).

### Fase 4: Pruebas, Validación y Documentación del TIF (Semana 5)
* Pruebas con 3 casos de estudio de pequeñas empresas simuladas:
  1. *Caso A: E-commerce con fuga de tarjetas y consentimientos forzados.*
  2. *Caso B: Clínica dental con historias clínicas sin control de acceso.*
  3. *Caso C: Aplicación SaaS B2B que procesa datos como PII Processor (Anexo B).*
* Redacción del informe final del TIF y preparación de la demo en vivo.

---

## 3. Argumentos Maestros para la Sustentación ante el Docente (Defensa 20/20)

Cuando el docente o el jurado evalúe el proyecto, estos son los argumentos técnicos y metodológicos que garantizarán la calificación máxima:

### Pregunta 1: "¿Por qué no usaron un RAG simple con todos los PDFs de las ISOs?"
* **Respuesta del Equipo:**
  > *"Un RAG ingenuo (Naive Vector RAG) fragmenta la norma en bloques aislados de texto y utiliza similitud de coseno, lo cual es ineficaz para la auditoría. En una auditoría, la relación entre un hallazgo y un control no es de similitud léxica, sino de implicación lógica y jerarquía normativa. Al implementar **GraphRAG**, preservamos la estructura de dependencia: Cláusula $\to$ Control $\to$ Principio de ISO 29100 $\to$ Artículo de Ley 29733 $\to$ Precedente de la ANPD. Esto elimina las alucinaciones de controles y permite responder preguntas complejas de tipo multi-salto con trazabilidad formal del 100%."*

### Pregunta 2: "¿Cómo auditan el esquema de la base de datos sin alucinar o perder datos?"
* **Respuesta del Equipo:**
  > *"Reconocimos tempranamente que hacer RAG vectorial sobre un script SQL es un anti-patrón porque el chunking destruye las relaciones de llaves foráneas y tipos de datos. Por ello, adoptamos el enfoque de la industria (DSPM - Data Security Posture Management) mediante un analizador sintáctico (AST) determinístico. Este módulo clasifica los campos según la Directiva R.D. 019-2013-JUS y el Anexo A de ISO 27701 con certeza matemática, y luego alimenta al LLM con un diagnóstico estructurado para que actúe en lo que mejor sabe hacer: la pedagogía y la remediación."*

### Pregunta 3: "¿Por qué decidieron automatizar el rol de CAPACITADOR y no el de Auditor Líder?"
* **Respuesta del Equipo:**
  > *"El rol de Auditor Líder externo emite un veredicto legal formal para otorgar un certificado, lo cual requiere responsabilidad civil y jurídica humana. En cambio, para el segmento MYPE (que no tiene presupuesto para una consultora), la mayor brecha no es el examen, sino la preparación: necesitan un **Capacitador y Consultor de Brechas** que les traduzca la norma a su realidad, les muestre casos reales de multas del Ministerio de Justicia para crear conciencia y les entregue código concreto para subsanar sus vulnerabilidades. Es donde la IA aporta el 90% del valor real a una pequeña empresa."*
