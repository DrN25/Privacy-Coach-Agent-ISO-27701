# 04. DISEÑO DETALLADO Y ESPECIFICACIÓN DE MÓDULOS
## Especificación de Componentes para el Agente Auditor-Capacitador PIMS (ISO/IEC 27701:2025)

**Curso:** Auditoría de Sistemas / TI  
**Institución:** Universidad Nacional de San Agustín (UNSA) - VIII Semestre  
**Proyecto:** Trabajo de Investigación Formativa (TIF)  

---

## 1. Módulo 1: Grafo de Conocimiento Normativo (GraphRAG - 78 Controles 2025)

El grafo de conocimiento modela las interdependencias de **ISO/IEC 27701:2025**:

### 1.1. Estructura Ontológica
```
  (Standard: ISO 27701:2025 Standalone)
         │
         ├──[:CONTIENE_SECCION]──▶ (Seccion: PII Controllers - Anexo A)
         │                                 │
         │                                 └──[:TIENE_CONTROL]──▶ (Control: A.7.2.2 Consentimiento)
         │                                                               │
         ├──[:MAPEADO_A]─────────────────────────────────────────────────┼──▶ (Principio: ISO 29100 P1)
         │                                                               │
         └──[:EQUIVALENTE_LEGAL]─────────────────────────────────────────┼──▶ (Articulo: Ley 29733 Art. 12)
                                                                         │
                                                                         └──[:INFRINGIDO_EN]──▶ (Resolucion: ANPD 045-2024 Multa 12 UIT)
```

### 1.2. Catálogo de los 78 Controles de ISO/IEC 27701:2025 en el Grafo
* **31 Controles de Responsables (PII Controllers - Anexo A):** Consentimiento, base legal, evaluación de impacto (PIA), derechos ARCO, minimización, retención segura y acuerdos de transferencia.
* **18 Controles de Encargados (PII Processors - Anexo B):** Sujeción a instrucciones, no utilización para fines propios, notificación inmediata de incidentes, devolución y destrucción segura.
* **29 Controles de Seguridad Aplicada a la Privacidad:** Cifrado en tránsito y reposo, gestión de accesos RBAC, hashing seguro con sal de credenciales, logging inmutable, enmascaramiento y seudonimización.

---

## 2. Módulo 2: Motor DSPM y Visualizador de Bases de Datos

### 2.1. Pipeline de Análisis del Esquema SQL
1. **Carga de Archivo:** El usuario sube su archivo `.sql` (DDL de creación de tablas o dump de esquema).
2. **Parsing Sintáctico (AST):** Se utiliza `sqlglot` en Python para descomponer tablas, columnas y tipos de datos sin chunking.
3. **Motor Heurístico de Detección de PII y Riesgo:**
   Se aplican patrones Regex y diccionarios adaptados a la normativa peruana y los controles tecnológicos de ISO 27701:2025:

| Columna Detectada | Categoría de Dato | Nivel de Riesgo | Control ISO 27701:2025 / Riesgo ANPD |
| :--- | :--- | :---: | :--- |
| `dni`, `documento`, `doc_identidad` | PII Identificable (Nacional) | **ALTO (Amarillo)** | Exige registro de banco de datos y control de acceso estricto. |
| `password`, `clave`, `pass`, `pin` | Credenciales de Autenticación | **CRÍTICO (Rojo)** | Si el tipo es `VARCHAR` y no contiene indicios de hashing (Argon2, bcrypt), se alerta infracción grave a R.D. 019-2013-JUS. |
| `tarjeta`, `cvv`, `card_number` | Datos Financieros | **CRÍTICO (Rojo)** | Prohibición estricta de almacenar CVV. Violación a normas de protección de datos y PCI-DSS. |
| `huella`, `rostro`, `biometria` | **Dato Sensible (Biométrico)** | **EXTREMO (Púrpura)** | Exige consentimiento expreso y cifrado en reposo (AES-256). Multa Muy Grave ante ANPD (hasta 100 UIT). |
| `enfermedad`, `diagnostico`, `salud` | **Dato Sensible (Salud)** | **EXTREMO (Púrpura)** | Infracción muy grave si se almacena o comparte sin consentimiento expreso y cifrado. |

### 2.2. Visualizador Interactivo en el Frontend
El frontend renderiza tarjetas visuales interactivas para cada tabla, coloreando los badges de las columnas según su nivel de riesgo:
* **Gris / Slate:** Campos sin PII (ej. `id`, `created_at`).
* **Azul:** PII básica (ej. `nombres`, `apellidos`).
* **Amarillo:** PII Identificadora directa (ej. `dni`, `telefono`, `email`).
* **Rojo:** Credenciales o datos financieros vulnerables (ej. `password` en texto plano, `numero_tarjeta`).
* **Púrpura:** Datos Sensibles de alto impacto legal (ej. `biometria`, `salud`, `cvv` prohibido).

---

## 3. Módulo 3: Matriz de Brechas (Gap Analysis) de los 78 Controles

* **Selector de Rol Inicial:**
  * ¿Tu empresa es **Responsable (Controller)** o **Encargado (Processor)**?
  * Si es Responsable, se activan los **31 controles del Anexo A** + los **29 controles de seguridad**.
  * Si es Encargado, se activan los **18 controles del Anexo B** + los **29 controles de seguridad**.
* **Estado de Cumplimiento:**
  * Conforme (Verde) / En Proceso (Amarillo) / No Conforme (Rojo) / No Aplica (Gris).
* **Score PIMS 2025:** Métrica porcentual global de madurez para la MYPE.

---

## 4. Módulo 4: Privacy Coach Agent con Casuística Real

### 4.1. System Prompt Especializado del Rol de Capacitador
```text
Eres "Aegis-PIMS", un Agente Auditor-Capacitador y Consultor Experto en Privacidad para Micro y Pequeñas Empresas (MYPEs), especializado en la norma internacional independiente ISO/IEC 27701:2025 (y sus 78 controles), el marco ISO/IEC 29100 y la Ley Peruana de Protección de Datos Personales (Ley N.° 29733, D.S. 003-2013-JUS, Directiva R.D. 019-2013-JUS y Metodología R.M. 476-2025-JUS).

Tu objetivo NO es reprobar fríamente al usuario ni abrumarlo con jerga jurídica incomprensible, sino CAPACITARLO y GUIARLO paso a paso:
1. Responde preguntas técnicas y jurídicas con precisión matemática, citando siempre el control exacto de ISO 27701:2025 (indicando si pertenece a los 31 de Controllers, 18 de Processors o 29 de Seguridad), el principio de ISO 29100 y el artículo de la Ley 29733.
2. Cada vez que detectes una vulnerabilidad o el usuario te pregunte por qué un control es importante, ILÚSTRALO con un ejemplo de casuística o sanción real de la ANPD (Ministerio de Justicia de Perú), explicando el rango de multas en UIT que arriesga la empresa.
3. Brinda soluciones técnicas y directas: si una tabla almacena contraseñas vulnerables, entrega el script de migración SQL o el código en Python/Node.js para aplicar bcrypt/Argon2id.
4. Mantén un estilo directo, profesional, claro y orientado a la remediación de riesgos para la empresa.
```
