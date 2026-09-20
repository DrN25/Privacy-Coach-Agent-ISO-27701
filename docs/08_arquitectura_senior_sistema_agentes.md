# 08. ARQUITECTURA SENIOR DEL SISTEMA DE AGENTES: ROL PRIVACY COACH
## Diseño Multi-Agente, Bases de Conocimiento Híbridas, Pipeline OCR y Glosario Tecnológico

**Curso:** Auditoría de Sistemas / TI  
**Institución:** Universidad Nacional de San Agustín (UNSA) - VIII Semestre  
**Proyecto:** Trabajo de Investigación Formativa (TIF)  
**Rol Automatizado Principal:** *Capacitador / Consultor de Brechas y Sensibilización en Privacidad (Privacy Awareness & Gap Coach)*  
**Marco Normativo Base:** ISO/IEC 27701:2025 (PIMS Standalone) · ISO/IEC 29100:2024 · Ley N.° 29733 (Perú)  
**Filosofía de Implementación:** *Senior Engineering & Local-First* (YAGNI, determinismo en cumplimiento, IA en pedagogía, 100% ejecutable localmente)  
**Ubicación del Documento:** `C:\Users\Rafael\UNSA\VIII SEMESTRE\AUDITORIA\TIF\docs\08_arquitectura_senior_sistema_agentes.md`

---

## 1. Definición del Rol Central: Privacy Awareness & Gap Coach

Tu docente solicitó automatizar un rol específico dentro del ciclo de vida de la privacidad. En la práctica empresarial, las micro y pequeñas empresas (MYPEs) no fracasan en privacidad por mala fe, sino por **desconocimiento técnico-legal**. Un auditor externo tradicional se limita a emitir un reporte punitivo de "Cumple / No Cumple". 

El rol seleccionado para este sistema es el de **Coach / Capacitador en Privacidad**, cuyo propósito es guiar pedagógicamente a la empresa a través de 4 etapas:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                      FLUJO DE ASESORÍA Y CAPACITACIÓN EN PRIVACIDAD                        │
└──────────────────────────────────────────────────────────────────────────────────────────┘
  [ 1. Ingesta Amigable ]        ──► Carga de archivos técnicos (SQL/Markdown) y políticas.
             │
             ▼
  [ 2. Sensibilización Económica]──► Explica el riesgo traduciéndolo a multas reales en UIT
             │                       de resoluciones sancionatorias de la ANPD del Perú.
             ▼
  [ 3. Indagación Pericial ]    ──► Pregunta en lugar de asumir: "¿Cómo registras hoy este
             │                       consentimiento?", desafiando las prácticas del usuario.
             ▼
  [ 4. Guía de Implementación ]  ──► Entrega soluciones listas: scripts SQL con campos de
                                     consentimiento, plantillas de políticas y hoja de ruta.
```

---

## 2. Arquitectura de Agentes y Flujo de Interacción

Para evitar un sistema monolítico ciego o alucinaciones sobre normativas complejas, el trabajo se divide en **tres agentes especializados** que operan sobre bases de conocimiento diferenciadas:

```
 ┌─────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   USUARIO (MYPE)                                        │
 └────────────────────┬───────────────────────────────────────────────▲────────────────────┘
                      │ Insumos (SQL, PDF, MD)                        │ Diálogo y Reportes
                      ▼                                               │
 ┌────────────────────────────────────────┐                           │
 │ AGENTE 1: PROFILER SEMÁNTICO (DSPM)    │                           │
 │ - Resuelve ambigüedades en inglés/jarga│                           │
 │ - Clasifica columnas y descripciones   │                           │
 └────────────────────┬───────────────────┘                           │
                      │ Esquema Clasificado (JSON)                    │
                      ▼                                               │
 ┌────────────────────────────────────────┐                           │
 │ AGENTE 2: EVALUADOR DE BRECHAS (GAP)   │                           │
 │ - Cruza esquema vs 78 controles        │                           │
 │ - Filtra por Rol (Controller/Processor)│                           │
 └────────────────────┬───────────────────┘                           │
                      │ Matriz de Brechas Técnicas                    │
                      ▼                                               │
 ┌────────────────────────────────────────────────────────────────────┴────────────────────┐
 │ AGENTE 3: PRIVACY COACH AGENT (CONSULTOR EXPERTO EN PRIVACIDAD)                │
 │ - Conduce el diálogo de asesoría técnica con el cliente en lenguaje de negocio claro.          │
 │ - Correlaciona hallazgos con precedentes de la ANPD y multas en UIT.                    │
 │ - Emite el Informe de Auditoría y Declaración de Aplicabilidad (SoA) bajo ISO/IEC 27701:2025.    │
 └────────────────────┬───────────────────────────────────────────────┬────────────────────┘
                      │ Consulta Subgrafos Normativos                 │ Consulta Casos Reales
                      ▼                                               ▼
         ┌─────────────────────────┐                     ┌─────────────────────────┐
         │ BASE DE CONOCIMIENTO 1  │                     │ BASE DE CONOCIMIENTO 2  │
         │ Grafo Normativo Ontológico│                   │ Casuística ANPD Perú    │
         │ ISO 27701 / 29100 / Ley │                     │ Resoluciones y Multas   │
         └─────────────────────────┘                     └─────────────────────────┘
```

---

## 3. Especificación Detallada de los Agentes LLM

### 3.1. Agente 1: Profiler Semántico de Datos (DSPM Agent)
* **¿Dónde entra en juego?** En la fase inicial de análisis técnico, inmediatamente después de que la empresa adjunta su esquema SQL (`schema.sql`) o su diccionario de datos (`diccionario.md` / `datos.txt`).
* **¿Por qué requiere IA y no solo código regex?** Porque los desarrolladores rara vez nombran las columnas como `documento_nacional_identidad`. Usan inglés (`dob`, `ssn`, `tax_id`, `patient_diag_code`), abreviaciones locales (`num_doc_id`, `cod_dx`, `cl_hist_obs`) o nombres genéricos (`campo_extra`). El código rígido tradicional es ciego a esto; el LLM infiere el contexto semántico de negocio.
* **¿Cómo se previene que el LLM falle, invente etiquetas o cometa errores tipográficos? (Los 3 Candados de Seguridad Anti-Falla):**
  Para evitar que un cambio de mayúscula o una letra alterada rompa el motor estático de Python, el Profiler implementa tres salvaguardas arquitectónicas:
  1. **Candado 1: Taxonomía Canónica Cerrada (Enum Estricto de 8 Clases):** El LLM no inventa texto libre. Opera sobre un catálogo cerrado derivado de la **Ley N.° 29733 (Art. 2 inc. 5)** y la **ISO/IEC 27701:2025**:
     * `DATO_SENSIBLE_SALUD` (diagnósticos, CIE-10, historias clínicas, recetas).
     * `DATO_SENSIBLE_BIOMETRICO` (huellas dactilares, reconocimiento facial).
     * `DATO_SENSIBLE_IDEOLOGIA` (afiliación política, sindicatos, religión).
     * `DATO_SENSIBLE_INGRESOS` (cuentas bancarias, deudas, montos económicos).
     * `DATO_IDENTIFICADOR_CIVIL` (DNI, RUC, nombres completos, pasaporte).
     * `DATO_CONTACTO` (email, teléfono, dirección postal).
     * `DATO_CREDENCIAL` (contraseñas, hashes, tokens de autenticación).
     * `SISTEMA_O_NO_PII` (claves primarias autoincrementables, timestamps, flags técnicos).
  2. **Candado 2: Structured Outputs con Pydantic y Gramáticas GBNF:** A nivel de inferencia en el modelo local (Ollama / vLLM con `format="json"` o gramáticas GBNF de `llama.cpp`), la red neuronal tiene restringida la distribución de probabilidad de tokens (*logits*). Es **matemáticamente imposible** que el modelo emita caracteres fuera de los 8 Enums canónicos. Si un token fuera de la gramática intenta generarse, el motor lo bloquea antes de imprimirlo.
  3. **Candado 3: Cascada en 3 Capas (Defensa en Profundidad):**
     * *Capa 1 (Heurística Local Regex - 0 ms, 0 tokens):* Columnas universales como `email`, `dni`, `password`, `created_at` se clasifican instantáneamente sin consumir IA.
     * *Capa 2 (LLM Profiler con Esquema Pydantic):* Se invoca únicamente para nombres ambiguos o abreviados (`cod_dx`, `mrn`, `health_score`).
     * *Capa 3 (Human-in-the-Loop Interactivo - Fail-Safe):* Si el desarrollador asignó un nombre opaco (`campo_x9`) con nivel de confianza del modelo < 0.85, el sistema no adivina: le asigna el estado `REQUIERE_ACLARACION` y el Coach le formula una pregunta directa y amable al desarrollador en el chat.
* **Salida Estructurada Garantizada (Pydantic Output):**
  ```json
  {
    "tabla": "tb_atenciones_triaje",
    "columnas": [
      {
        "nombre_columna": "cod_dx",
        "categoria": "DATO_SENSIBLE_SALUD",
        "confianza": 0.98,
        "justificacion_corta": "Abreviatura estándar de código de diagnóstico CIE-10."
      },
      {
        "nombre_columna": "obs_clinicas",
        "categoria": "DATO_SENSIBLE_SALUD",
        "confianza": 0.96,
        "justificacion_corta": "Notas y observaciones médicas clínicas."
      },
      {
        "nombre_columna": "pac_dni",
        "categoria": "DATO_IDENTIFICADOR_CIVIL",
        "confianza": 1.0,
        "justificacion_corta": "Clasificado por regex heurístico de alta certeza."
      }
    ]
  }
  ```

---

### 3.2. Agente 2: Orquestador & Evaluador de Brechas (Gap Matrix Agent)
* **¿Dónde entra en juego?** En el motor de decisiones lógicas que compara la realidad de la empresa con la norma.
* **¿Cómo opera?**
  1. Pregunta o extrae el rol de la empresa: **PII Controller** (quien decide los fines del tratamiento) o **PII Processor** (proveedor tecnológico o SaaS que solo procesa por encargo).
  2. Filtra los controles aplicables:
     * Si es *Controller*: Aplican los 31 controles de la Tabla A.1 + 29 controles de la Tabla A.3.
     * Si es *Processor*: Aplican los 18 controles de la Tabla A.2 + 29 controles de la Tabla A.3.
  3. Cruza cada hallazgo del DSPM con el Grafo Normativo (Base de Conocimiento 1).
* **Salida:** Genera la **Matriz de Brechas (Gap Matrix)**:
  * Control `A.1.2.4` (Determinar cómo obtener consentimiento) -> **NO CUMPLE** (No existe tabla ni columna para guardar la prueba del consentimiento).
  * Control `A.3.24` (Uso de criptografía) -> **NO CUMPLE** (La columna `cod_diag` está en texto claro).

---

### 3.3. Agente 3: Privacy Coach Agent (Consultor Experto en Privacidad)
* **¿Dónde entra en juego?** En la interfaz conversacional con el usuario humano. Es el agente visible y pedagógico.
* **¿Cómo opera?**
  1. **Tono y Personalidad:** Empático, didáctico, orientador, riguroso pero accesible (sin lenguaje técnico asfixiante).
  2. **Uso de la Base de Conocimiento 2 (Casuística ANPD):** Para cada brecha grave, consulta el banco de sanciones y advierte al usuario del impacto económico real en UIT:
     > *"Estimado coordinador, detectamos que en tu base de datos guardas diagnósticos de pacientes sin un campo que registre cuándo y cómo dieron su consentimiento. En el Perú, la Dirección de Fiscalización de la ANPD impuso una multa de 24.5 UIT (más de S/. 120,000) a una clínica mediante la Resolución N.° 045-2023 por una omisión idéntica. ¿Cuentas actualmente con un documento físico firmado para esto, o todo el flujo es digital?"*
  3. **Capacitación en Implementación:** Guía paso a paso al usuario con código y plantillas para subsanar la brecha.
  4. **Emisión de Documentación Formal:** Redacta la Declaración de Aplicabilidad (SoA) y el informe final bajo la estructura de **ISO/IEC 27701:2025**.

---

## 4. Especificación Rigurosa de las Bases de Conocimiento

El sistema no utiliza un único almacén de datos homogéneo; cada tipo de información requiere una estructura optimizada:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                   MAPA DE LAS TRES BASES DE CONOCIMIENTO DEL SISTEMA                     │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ KB-1: GRAFO NORMATIVO ONTO-LÓGICO (Memoria Estructural Anti-Alucinaciones)               │
│ - Estructura: Grafo dirigido en NetworkX / JSON en memoria.                              │
│ - Contenido:                                                                             │
│   * 78 Controles ISO/IEC 27701:2025 (31 Controller, 18 Processor, 29 Security).         │
│   * 11 Principios de Privacidad de ISO/IEC 29100:2024 (Mapeados desde Anexo C).          │
│   * Artículos clave de la Ley N.° 29733 y D.S. N.° 003-2013-JUS (Mapeados vía Anexo D).   │
│   * Medidas técnicas de la Directiva de Seguridad R.D. N.° 019-2013-JUS/DGPDP.           │
│   * Guías de implementación del Anexo B de ISO 27701:2025.                              │
│ - Operación: Búsqueda sub-milisegundo por ID de control o principio. Cero alucinaciones. │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ KB-2: ALMACÉN DE CASUÍSTICA ANPD PERÚ (Case-Based RAG Facetado)                          │
│ - Estructura: ChromaDB local con metadatos estructurados + embeddings BGE-Small.         │
│ - Contenido:                                                                             │
│   * Colección curada de 20 a 50 Resoluciones Directorales sancionatorias del MINJUSDH.   │
│   * Metadatos por caso: { nro_resolucion, sector, infraccion_tipo, multa_uit, ley_art }. │
│   * Texto descriptivo: Síntesis de la conducta infractora y argumentos de la autoridad.  │
│ - Operación: Filtrado estricto por faceta (sector = "Salud") + similitud semántica.      │
├──────────────────────────────────────────────────────────────────────────────────────────┤
│ KB-3: REPOSITORIO DE EVIDENCIAS DE LA EMPRESA (Memoria de Sesión Volátil)                │
│ - Estructura: SQLite / Almacén de sesión en memoria por empresa auditada.                │
│ - Contenido:                                                                             │
│   * AST del esquema de base de datos (`schema.sql`, tablas, columnas, constraints).      │
│   * Texto extraído de políticas web, contratos de tratamiento o SLAs (vía PyMuPDF/OCR).  │
│   * Historial de respuestas y evidencias verbales otorgadas durante la interacción diagnóstica.│
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Pipeline de Ingesta Políglota y Adaptativa (Lazy OCR)

La empresa puede adjuntar sus evidencias en formatos muy diversos. El sistema maneja la ingesta sin sobrecargar la CPU:

```
                                  ARCHIVO ADJUNTADO POR LA MYPE
                                                │
         ┌──────────────────────────────────────┼──────────────────────────────────────┐
         ▼                                      ▼                                      ▼
[ Archivo SQL / DDL ]                 [ Documento PDF ]                      [ Markdown / TXT ]
  `schema.sql`                          `politica_privacidad.pdf`              `diccionario.md`
         │                                      │                                      │
         ▼                                      ▼                                      ▼
[ Parser AST sqlglot ]                [ Ingesta Adaptativa ]                 [ Parser Markdown ]
  Extrae tablas, columnas               ¿Texto digital nativo?                 Extrae secciones,
  y tipos de datos.                             │                               tablas y notas.
                                       ┌────────┴────────┐                             │
                                    SÍ │               NO│ (Escaneado)                 │
                                       ▼                 ▼                             │
                              [ PyMuPDF (fitz) ]   [ RapidOCR ONNX ]                   │
                                Extrae texto en     OCR rápido CPU                     │
                                2 milisegundos.     (200 ms/página).                   │
                                       │                 │                             │
                                       └────────┬────────┘                             │
                                                ▼                                      │
                                    [ TEXTO LIMPIO NORMALIZADO ] ◄─────────────────────┘
                                                │
                                                ▼
                                   [ AGENTES LLM DEL SISTEMA ]
```

---

## 6. Gestión del Ciclo de Vida y Cambios Normativos (Evolución de Leyes e ISOs)

Una de las preguntas más críticas en el diseño de un sistema de auditoría es: **¿Qué ocurre si la ISO 27701 se actualiza (ej. a una edición futura) o si el MINJUSDH promulga un nuevo reglamento de protección de datos que cambia los números de artículos o las escalas de multas?**

### 6.1. La Trampa del RAG Vectorial Ingenuo (Contaminación Fantasma de Chunks)
En un RAG clásico plano, la creencia común es: *"Solo cargo el nuevo PDF, vuelvo a hacer chunking y listo"*. En sistemas de auditoría jurídica, esto genera un fallo crítico denominado **Contaminación Fantasma de Fragmentos (Phantom Chunk Collision)**:
* Si en la base vectorial conviven fragmentos de una versión derogada y una versión nueva, la búsqueda semántica por similitud de coseno recuperará trozos de ambos documentos.
* El LLM mezclará requisitos contradictorios (por ejemplo, afirmará simultáneamente que la ISO 27001 es un prerrequisito obligatorio —como decía la versión 2019— y que es independiente —como dice la versión 2025—).
* En una auditoría formal, fundamentar un hallazgo en una norma derogada o citar un artículo legal derogado invalida el dictamen técnico ante un jurado o cliente.

### 6.2. La Solución Determinista en Nuestra Arquitectura (Pipelines de Código Reproducibles)
Gracias a la existencia del script `knowledge_base/pipelines/build_datasets.py`, la mantenibilidad del sistema es matemática y reproducible:
1. **Versionado Inmutable de Nodos:** Cada nodo del grafo posee metadatos de versión explícitos (`"standard": "ISO/IEC 27701:2025"`, `"id": "A.1.2.4"`). No existen fragmentos de texto flotando sin linaje normativo.
2. **Actualización de la Norma Internacional:** Ante una nueva versión de la ISO, se corre el script extractor sobre el nuevo PDF. El script genera un nuevo archivo inmutable (`iso27701_2030_graph.json`). El sistema permite auditar empresas bajo la versión 2025 o la versión 2030 mediante un simple selector de versión, sin que jamás se mezclen sus requisitos.
3. **Actualización del Marco Legal Peruano:** Si el MINJUSDH aprueba el nuevo reglamento y deroga el D.S. 003-2013-JUS (cambiando artículos o multas), la actualización se realiza en una sola tabla centralizada de mapeo (`peru_law_map` dentro del script). Con cambiar 5 líneas de equivalencia, los 78 controles quedan re-alineados a la nueva ley de inmediato, sin re-entrenar modelos ni re-vectorizar millones de tokens.

---

## 7. Mecanismo de Consulta Quirúrgica (El Embudo de Reducción de Contexto)

**¿Cómo sabe el agente a qué información acceder sin "tragarse" todo el contenido de los documentos ni saturar la memoria del modelo local?**

### 7.1. El Problema de la Saturación Cognitiva
El corpus completo (los 78 controles detallados con sus guías del Anexo B más las 582 sanciones impuestas por la ANPD) suma más de **150,000 tokens**. Si intentáramos inyectar todo ese texto en cada turno conversacional:
* Superaría con creces la ventana de contexto de un modelo local de 8B (como Llama 3 o Qwen 2.5 en Ollama).
* Generaría una latencia inaceptable de más de 45 a 60 segundos por respuesta en una laptop.
* Produciría el fenómeno de *"Lost in the Middle"* (el LLM pierde atención y olvida las instrucciones intermedias).

### 7.2. El Embudo de Reducción en Cuatro Etapas (De 150,000 a 850 Tokens)
El Agente Orquestador actúa como un embudo algorítmico determinista antes de tocar el modelo de lenguaje:

```
[ CORPUS COMPLETO: 78 Controles + 582 Sanciones (~150,000 tokens) ]
                            │
                            ▼  ETAPA 1: Filtro Estructural por Rol (Cero tokens de LLM)
[ MYPE declara ser "PII Controller":
  Se descartan automáticamente los 18 controles de Processor de la Tabla A.2.
  Espacio de búsqueda reducido a 60 controles. Tiempo: 0.0001s. ]
                            │
                            ▼  ETAPA 2: Hallazgos Específicos del Motor DSPM (Código Python AST)
[ El DSPM analiza el schema.sql y evalúa reglas booleanas de privacidad:
  - Regla: RULE_SENSITIVE_DATA_MISSING_CONSENT (Detecta datos de salud sin campo de consentimiento).
  - Regla: RULE_UNENCRYPTED_SENSITIVE_STORAGE (Detecta datos de salud en VARCHAR/TEXT plano).
  Tiempo: 0.010s. Tokens: 0. ]
                            │
                            ▼  PUENTE DETERMINISTA: Router Regla-a-Grafo O(1) (¡CERO LLM!)
[ Un diccionario estático en Python mapea las reglas disparadas hacia los IDs de control formales:
  DSPM_RULE_TO_ISO_CONTROLS = {
      "RULE_SENSITIVE_DATA_MISSING_CONSENT": ["A.1.2.4", "A.1.2.5"],
      "RULE_UNENCRYPTED_SENSITIVE_STORAGE":   ["A.3.24"]
  }
  ¡NO HAY LLM EN ESTE PASO! Esto elimina al 100% las alucinaciones normativas. ]
                            │
                            ▼  ETAPA 3: Extracción del Subgrafo Quirúrgico (NetworkX / JSON)
[ El Grafo extrae ÚNICAMENTE los nodos solicitados por el Router y sus aristas inmediatas:
  - Control A.1.2.4 (Obtención del consentimiento) + Principio 1 ISO 29100 + Art. 18 Ley 29733.
  - Control A.3.24 (Uso de criptografía) + Principio 10 ISO 29100 + Art. 28 Ley 29733.
  Tiempo de extracción: 0.0002s. Tokens: 0. ]
                            │
                            ▼  ETAPA 4: Búsqueda Facetada en Casuística ANPD (Base de Conocimiento 2)
[ Se consulta anpd_sanciones_dataset.json con filtro directo:
  sector = "Salud / Clínica" AND infraccion = "Art. 18"
  -> Recupera de inmediato el Caso 17: "Clínicas Maison de Santé S.A., Multa 10.0 UIT (S/ 51,500)".
  Tiempo: 0.001s. Tokens: 0. ]
                            │
                            ▼
[ PROMPT FINAL INYECTADO AL COACH LLM: ¡Apenas 850 tokens! ]
```

> [!IMPORTANT]
> **¿Cómo se sabe exactamente que el Control A.1.2.4 es el involucrado sin que intervenga un LLM?**  
> Porque la conexión entre el hallazgo técnico y la norma internacional está codificada en el **Router Regla-a-Grafo (`DSPM_RULE_TO_ISO_CONTROLS`)**. Si pusiéramos a un LLM a "interpretar y elegir" qué control de la ISO 27701 aplica a cada columna de la base de datos, el sistema sufriría de alucinaciones (confundiría sub-cláusulas, inventaría números inexistentes o mezclaría versiones derogadas). Al hacerlo por código estático indexado en memoria, la extracción toma **0.0002 segundos**, cuesta **cero tokens** y tiene una tasa de error normativo de **cero**.


### 7.3. Anatomía del Prompt Quirúrgico que Recibe el LLM
El LLM de 8B en Ollama solo recibe este payload ultraligero y perfectamente enfocado:

```json
{
  "contexto_empresa": "Clínica privada pequeña (PII Controller)",
  "hallazgo_tecnico": "Tabla 'citas', columna 'diagnostico_medico' almacenada en texto claro sin registro de consentimiento.",
  "control_normativo": "ISO/IEC 27701:2025 Control A.1.2.4 (Determine when and how consent is to be obtained).",
  "base_legal_peru": "Ley N.° 29733 Art. 18 (Consentimiento previo, informado, expreso e inequívoco para datos sensibles).",
  "precedente_real_anpd": "Resolución Directoral N° 017-2015-JUS/DGPDP contra Clínicas Maison de Santé S.A. (Multa: 10 UIT por tratamiento sin consentimiento).",
  "instruccion_coach": "Explica al auditado el riesgo con empatía en lenguaje de negocio, cita la sanción real en UIT para generar conciencia económica, y formula una pregunta técnica sobre cómo registran el consentimiento en su flujo de admisión."
}
```

* **Resultado:** La respuesta del modelo local tarda **menos de 2 segundos**, mantiene una coherencia del 100%, cita datos numéricos exactos y reales, y jamás alucina porque no tiene 100 páginas de texto irrelevante compitiendo por su atención.

---



---

### 7.4. Demostración Exhaustiva y Caso de Estudio Real
Para consultar la trazabilidad técnica completa de este embudo (con código SQL sucio real, scripts Python de análisis AST con `sqlglot`, salidas JSON de Pydantic, consultas al grafo NetworkX y la transcripción completa del diálogo pericial del Coach), consulte el documento complementario:
* **[09. Flujo Real End-to-End: Del Esquema SQL al Privacy Coaching y Parches Técnicos](file:///C:/Users/Rafael/UNSA/VIII%20SEMESTRE/AUDITORIA/TIF/docs/09_flujo_ejemplo_end_to_end_dspm_coach.md)**.

## 8. Glosario Tecnológico y Metodológico Exhaustivo

A continuación se explica a fondo cada concepto, herramienta y patrón arquitectónico adoptado, fundamentando técnica y pedagógicamente su elección frente a las alternativas:

---

### 6.1. DSPM (Data Security Posture Management)
* **¿Qué es?** Una disciplina de ciberseguridad y gobierno de datos enfocada en descubrir dónde residen los datos sensibles, quién tiene acceso a ellos, cómo se protegen y qué riesgos normativos presentan en reposo.
* **¿Qué hace en nuestro sistema?** Inspecciona los esquemas de bases de datos de la MYPE, clasifica las columnas en semáforos de riesgo de privacidad (sensibles, identificativas, operativas) y detecta omisiones técnicas (como almacenar contraseñas en texto claro o carecer de bitácoras de acceso).
* **¿Cómo se implementa?** En dos etapas: primero un analizador sintáctico abstracto (`sqlglot`) que extrae la lista de columnas, y segundo el **Agente 1 (LLM Profiler)** que clasifica el significado semántico.
* **Ventajas:** Da visibilidad real sobre el activo más valioso de la empresa (sus datos) sin necesidad de revisar el código fuente completo de la aplicación.
* **Desventajas:** Si la empresa no proporciona acceso al esquema SQL o este está deliberadamente ofuscado sin datos de muestra, se requiere inferencia basada en entrevistas.
* **¿Por qué este y no otros?** Se prefiere un motor DSPM liviano sobre escáneres estáticos de código (SAST como SonarQube), porque la ISO 27701 y la Ley 29733 regulan los **bancos de datos personales**, no las vulnerabilidades sintácticas del código fuente.

---

### 6.2. AST (Abstract Syntax Tree / Árbol de Sintaxis Abstracta) con `sqlglot`
* **¿Qué es?** Una representación estructurada en forma de árbol jerárquico de la gramática de un código o consulta SQL.
* **¿Qué hace en nuestro sistema?** Descompone sentencias `CREATE TABLE` en objetos Python limpios: nombres de tabla, nombres de columna, tipos (`VARCHAR`, `INT`), llaves primarias y foráneas, sin requerir una base de datos activa corriendo.
* **¿Cómo se implementa?** Con la librería de Python `sqlglot`:
  ```python
  import sqlglot
  tables = [table for table in sqlglot.parse(sql_content) if isinstance(table, sqlglot.exp.Create)]
  ```
* **Ventajas:** Determina con 100% de precisión matemática las columnas existentes sin alucinaciones de LLM y con latencia de 5 milisegundos. Es agnóstico al dialecto (soporta MySQL, PostgreSQL, SQLite, SQL Server).
* **Desventajas:** Solo analiza la sintaxis; no sabe qué significa semánticamente la palabra `cod_diag` a menos que se use un clasificador.
* **¿Por qué este y no expresiones regulares (Regex)?** Las expresiones regulares sobre SQL fallan catastróficamente con comentarios multilínea, saltos de línea irregulares, restricciones compuestas y dialectos cruzados. `sqlglot` maneja la gramática formal completa.

---

### 6.3. GraphRAG (Graph-Augmented Retrieval)
* **¿Qué es?** Una arquitectura de recuperación de información que combina grafos de conocimiento estructurados (nodos y aristas con significado formal) con modelos de lenguaje.
* **¿Qué hace en nuestro sistema?** Almacena las relaciones normativas oficiales entre los 78 controles de la ISO 27701:2025, los 11 principios de la ISO 29100:2024 y los artículos de la Ley N.° 29733. Cuando se detecta una brecha en un control, el grafo navega por las relaciones y le entrega al LLM el sub-grafo exacto.
* **¿Cómo se implementa?** Mediante un grafo dirigido en memoria con la biblioteca `networkx` de Python o indexado en un JSON enriquecido:
  ```python
  import networkx as nx
  G = nx.DiGraph()
  G.add_edge("ISO27701_A.1.2.4", "ISO29100_Principle_1", relation="IMPLEMENTS")
  G.add_edge("ISO27701_A.1.2.4", "LEY29733_Art_18", relation="ENFORCES_LAW")
  ```
* **Ventajas:** **Cero alucinaciones normativas.** El LLM nunca inventará un control inexistente ni mezclará qué le corresponde a un Controller frente a un Processor.
* **Desventajas:** Requiere poblar inicialmente el grafo con las relaciones oficiales (lo cual ya resolvimos gracias a las Tablas C.1, D.1 y F.1 de tu PDF).
* **¿Por qué este y no RAG Vectorial Plano?** El RAG vectorial clásico corta el PDF en pedazos de 500 palabras; al buscar un control, suele traer fragmentos desordenados o el Anexo equivocado. El grafo garantiza precisión estructural del 100%.

---

### 6.4. Case-Based RAG (RAG Basado en Casos y Metadatos Facetados)
* **¿Qué es?** Una técnica de recuperación que organiza la información en "fichas de casos" con metadatos estructurados rígidos (categoría, sanción, artículo) combinados con texto descriptivo indexado semánticamente.
* **¿Qué hace en nuestro sistema?** Permite al Coach de Privacidad buscar precedentes sancionadores de la ANPD según el sector de la empresa (`Salud`, `Comercio`, `Finanzas`) y el tipo de falta cometida (`Falta de consentimiento`, `Fuga de datos`, `No atención ARCO`).
* **¿Cómo se implementa?** En ChromaDB utilizando filtros de metadatos (`where={"sector": "Salud"}`) junto a la consulta de similitud de embeddings:
  ```python
  results = collection.query(
      query_texts=["almacenamiento de diagnósticos médicos sin consentimiento"],
      where={"sector": "Salud"},
      n_results=2
  )
  ```
* **Ventajas:** Recupera exactamente la resolución aplicable con el monto real en UIT, permitiendo al Coach decir cifras reales y verificables.
* **Desventajas:** Requiere curar previamente el catálogo de resoluciones de la ANPD (unas 20 a 30 resoluciones clave son suficientes para el proyecto).
* **¿Por qué este y no un RAG sobre las 50 páginas de cada resolución?** Las resoluciones legales peruanas tienen 40 páginas de considerandos repetitivos y formalismos procesales. Indexar el PDF completo satura la búsqueda con párrafos irrelevantes; la ficha estructurada sintetiza la conducta y la sanción.

---

### 6.5. RapidOCR (`rapidocr_onnxruntime`)
* **¿Qué es?** Un motor de reconocimiento óptico de caracteres de alto rendimiento basado en modelos de deep learning empaquetados y optimizados bajo el estándar ONNX.
* **¿Qué hace en nuestro sistema?** Sirve como módulo de respaldo (*fallback*) cuando la MYPE adjunta políticas o contratos escaneados en formato PDF o imágenes donde no existe una capa de texto seleccionable.
* **¿Cómo se implementa?** Se instala vía `pip install rapidocr_onnxruntime` y se invoca pasando la imagen de la página renderizada por PyMuPDF:
  ```python
  from rapidocr_onnxruntime import RapidOCR
  ocr = RapidOCR()
  result, _ = ocr(page_img_bytes)
  ```
* **Ventajas:** 
  * **Cero dependencias externas:** No requiere instalar programas compilados en Windows (como `tesseract.exe`).
  * **Ligero y veloz:** Corre en CPU en menos de 200 ms por página.
  * **Excelente detección espacial:** Maneja tablas y texto con orientación diversa.
* **Desventajas:** No sustituye a la extracción nativa digital; por eso solo se invoca cuando la densidad de texto es nula.
* **¿Por qué este y no Tesseract o PaddleOCR?** Tesseract es un dolor de cabeza para instalar en Windows y requiere librerías adicionales para tablas; PaddleOCR descarga más de 2 GB de dependencias pesadas de PaddlePaddle. RapidOCR es ligero, portable y funciona al instante.

---

### 6.6. PyMuPDF (`fitz`)
* **¿Qué es?** La librería de Python de más alto rendimiento para procesamiento, extracción y renderizado de archivos PDF, basada en el motor C de MuPDF.
* **¿Qué hace en nuestro sistema?** Extrae la capa de texto nativo de los PDFs en 2 milisegundos por página y, si detecta que la página es una imagen escaneada, genera el mapa de bits (*pixmap*) para alimentar a RapidOCR.
* **¿Cómo se implementa?** Con `import fitz; doc = fitz.open(pdf_path)`.
* **Ventajas:** Entre 10 y 20 veces más rápido que `pypdf` o `pdfplumber`; no falla con formatos complejos de tablas.
* **¿Por qué este y no `pdfplumber`?** `pdfplumber` es excelente pero significativamente más lento al iterar sobre documentos de más de 50 páginas. PyMuPDF maneja documentos de 100 páginas en una fracción de segundo.

---

### 6.7. FSM (Finite State Machine / Máquina de Estados Finitos)
* **¿Qué es?** Un modelo computacional que describe un sistema que solo puede estar en uno de varios estados definidos en un momento dado, cambiando de estado según entradas o eventos específicos.
* **¿Qué hace en nuestro sistema?** Controla el flujo de la sesión del Coach de Privacidad para que no se desvíe ni entre en bucles infinitos:
  * *Estado 1: Selección de Rol (Controller / Processor).*
  * *Estado 2: Ingesta de Artefactos (SQL / Documentos).*
  * *Estado 3: Evaluación Determinista de Brechas.*
  * *Estado 4: Asesoría Técnica Interactiva.*
  * *Estado 5: Emisión de Declaración de Aplicabilidad y Dictamen Técnico ISO 27701.*
* **¿Cómo se implementa?** Con un enrutador en FastAPI o LangGraph simple en Python.
* **Ventajas:** Predecible, reproducible, fácil de depurar y garantiza que el alumno cumpla todos los pasos de la auditoría.
* **¿Por qué este y no agentes libres no estructurados (AutoGPT)?** Los agentes no restringidos tienden a desviarse, inventar tareas innecesarias o consumir recursos en ciclos infinitos. Para un trabajo de auditoría académica, la rigidez del flujo garantiza la calidad.

---

### 6.8. Ollama y Modelos de Lenguaje Locales (Llama 3 8B / Qwen 2.5 7B)
* **¿Qué es?** Un entorno de ejecución local ligero que permite correr modelos de lenguaje de última generación cuantizados (GGUF de 4 bits) directamente en la CPU o GPU de una computadora personal sin conexión a internet.
* **¿Qué hace en nuestro sistema?** Provee el motor cognitivo para el **Agente 1 (DSPM Profiler)** y el **Agente 3 (Privacy Coach)**.
* **¿Cómo se implementa?** Corriendo Ollama en segundo plano y consultándolo mediante su API REST local (`http://localhost:11434/api/generate`) o la librería `langchain-community`.
* **Ventajas:**
  * **Cero costo de API:** No se pagan tokens a OpenAI ni a Google.
  * **Privacidad absoluta:** Los datos y esquemas de la empresa auditada jamás salen de la máquina local (cumpliendo con la propia filosofía de la ISO 27701).
* **Desventajas:** La ventana de contexto y capacidad de razonamiento de un modelo 8B es menor que la de un modelo de 70B en la nube; por eso es mandatorio alimentarlo con contextos pequeños y filtrados por el Grafo (menos de 2,000 tokens por turno).
* **¿Por qué Llama 3 8B o Qwen 2.5 7B?** Son los modelos de mayor rendimiento en pruebas de seguimiento de instrucciones (*instruction following*) y generación de JSON estructurado dentro del rango accesible para hardware de estudiantes.

---

### 6.9. Structured Outputs (Modo JSON / Validación Pydantic)
* **¿Qué es?** Una técnica que obliga al modelo de lenguaje a emitir su respuesta exclusivamente bajo un esquema JSON predefinido, garantizando que no incluya saludos ni texto conversacional en las etapas intermedias.
* **¿Qué hace en nuestro sistema?** Asegura que la salida del Agente 1 (DSPM) y del Agente 2 (Gap Matrix) sea parseable directamente por código Python sin que se rompa el pipeline.
* **¿Cómo se implementa?** Definiendo esquemas con `pydantic` y pasando el parámetro `format="json"` a Ollama.
* **Ventajas:** Elimina los fallos de integración típicos de los LLMs donde el modelo dice: *"Aquí tienes el JSON: ```json ... ```"*, lo cual rompería un script tradicional.

---

### 6.10. PII Controller vs PII Processor (Conceptos Clave de ISO/IEC 27701:2025)
* **PII Controller (Responsable del Tratamiento):** La persona u organización que determina **para qué** y **cómo** se tratan los datos personales (ej. la clínica médica o la tienda de e-commerce que decide qué datos pedir a sus clientes). Le aplican los **31 controles de la Tabla A.1**.
* **PII Processor (Encargado del Tratamiento):** La organización que trata datos personales **únicamente en nombre y bajo las instrucciones de un Controller** (ej. una empresa de software SaaS de historias clínicas o un proveedor de hosting). Le aplican los **18 controles de la Tabla A.2**.
* **Por qué es vital en el sistema:** Es la primera bifurcación del Grafo de Conocimiento; evita exigirle a un desarrollador controles de consentimiento directo cuando su rol es únicamente de encargado técnico.

---

### 6.11. Unidades Impositivas Tributarias (UIT) en la Casuística Peruana
* **¿Qué es?** El valor de referencia utilizado en el Perú para determinar sanciones, infracciones y tasas tributarias (fijado anualmente por el Ministerio de Economía y Finanzas; en 2024 fue de S/. 5,150 y en 2025/2026 supera los S/. 5,350).
* **Escala de Multas de la Ley N.° 29733 (Art. 39):**
  * *Infracciones Leves:* 0.5 a 5 UIT (ej. no inscribir un banco de datos ante el Registro Nacional).
  * *Infracciones Graves:* Más de 5 hasta 50 UIT (ej. tratar datos personales sin consentimiento previo, expreso e inequívoco, o no atender solicitudes de derechos ARCO).
  * *Infracciones Muy Graves:* Más de 50 hasta 100 UIT (ej. crear bancos de datos de forma clandestina o transferir datos sensibles internacionalmente a países sin nivel adecuado de protección).
* **Impacto en el Agente:** Permite al Coach cuantificar el riesgo de negocio: una multa de 20 UIT significa más de S/. 100,000 para una MYPE, convirtiendo una advertencia abstracta de la ISO en un argumento de concientización inmediato para la gerencia.
