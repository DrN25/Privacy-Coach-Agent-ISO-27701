# Documento de Trabajo: Plan de Refactorización y Definición Funcional del Agente 6
**Módulo:** Agente de Gestión de Incidentes de Seguridad y Brechas de Datos Personales (PII Breaches)  
**Institución:** Universidad Nacional de San Agustín de Arequipa (UNSA)  
**Marco Normativo:** ISO/IEC 27035-1/2/3, ISO/IEC 27701:2025 (Cl. 6.5.24 - 6.5.28, Cl. 7.2.9), Ley N° 29733, D.S. 016-2024-JUS  
**Archivo de Trabajo:** `docs/PLAN_REFACTORIZACION_Y_CAMBIOS_SISTEMA_AGENTE6.md`  
**Estado:** Propuesta Inicial para Revisión y Consenso con el Usuario  

---

## 1. Propósito de este Documento

Este documento establece la **hoja de ruta técnica de cambios, adaptaciones y mejoras** que se implementarán en el código del sistema (`src/`) para que nuestro agente:
1. Deje de ser un prototipo genérico de prueba y se convierta en el **Agente Pericial de Incidentes y Brechas de la UNSA**.
2. Supere la limitación de entregar solo parches SQL, implementando un **modelo de remediación multidimensional (SQL, No-SQL, Cloud, Jurídico y Organizativo)** conforme a **ISO/IEC 27035** y el control **A.5.26** de ISO 27701.
3. Se conecte e interactúe de forma realista y limpia con la base de datos institucional en PostgreSQL (`unsa_pims_db`).
4. Evite caer en sobreingeniería innecesaria (descartando dashboards de ticketing, cronómetros interactivos o asignación de tareas operativas).

---

## 2. Diagnóstico: Estado Actual vs. Estado Deseado

| Componente | Estado Actual en `src/` | Estado Deseado Propuesto | Justificación del Cambio |
| :--- | :--- | :--- | :--- |
| **Contexto y Datos** | Mockup de una clínica privada genérica (`schema_clinica_saludtotal.sql`). | Activos, dependencias y sistemas reales de la **UNSA** (`SYS-HOSPITAL`, `SYS-SISADMIS`, `APP-UNSAPAY`, `SYS-SISUNSA`, `APP-TRAMITED`, `APP-SISCOM`). | Alineación obligatoria con el proyecto de auditoría de la UNSA y los 15 macroprocesos. |
| **Persistencia** | SQLite local único (`src/data/empresa_conocimiento.db`). | **Conector Híbrido:** Conexión a PostgreSQL (`unsa_pims_db`, esquema `demo`) con fallback a SQLite local si no hay conexión externa. | Capacidad de leer y escribir directamente en `demo.core_incident` y `demo.core_securitylog`. |
| **Alcance de Remediación (A.5.26)** | Solo un texto plano corto con una sentencia SQL sugerida. | **Paquete Multidimensional en 4 Capas:**<br/>1. SQL / DDL.<br/>2. Software No-SQL / Cloud (React, Argon2id, AWS CLI).<br/>3. Jurídica (DPAs, Avisos, Denuncias).<br/>4. Organizativa (Directivas, Circulares Rectorales). | Muchas brechas (consentimiento web, retención, transferencias AWS, trabas ARCO) no se resuelven con SQL. |
| **Formato del Dictamen (A.5.28)** | Informe Markdown genérico básico. | **Dictamen Pericial Oficial bajo ISO 27035 (7 Secciones):** Incluye evaluación CID, tasación ANPD, plan de remediación en 4 capas y cédula oficial de notificación ANPD en 48h. | Validez pericial ante auditorías del OCI y fiscalizaciones de la ANPD. |
| **Interfaz de Usuario** | Vista de pestañas orientada a archivos subidos de una clínica. | Vista institucional UNSA con panel de **Incidentes Registrados (`core_incident`)**, detalle de remediación por pestañas y chat pericial. | Claridad operativa sin convertirlo en un software de ticketing complejo. |

---

## 3. Especificación Detallada de Cambios por Capa del Sistema

### Capa 1: Catálogo de Reglas y Motor de Remediación (`src/backend/core/rules_catalog.py`)

#### Problema Actual:
El catálogo define `"remediacion_sugerida": "Aplicar pgcrypto..."` como un único string, asumiendo erróneamente que todo es SQL.

#### Cambio Propuesto:
Reestructurar el diccionario tipado `ReglaAuditoria` para que cada una de las 7 reglas canónicas (`R-001` a `R-007`) proporcione una estructura de remediación completa:

```python
class RemediacionIntegral(TypedDict):
    db_sql: Optional[str]              # Script SQL transaccional (BEGIN...COMMIT) o None
    software_nosql: Optional[str]      # Código No-SQL: React, Python backend, AWS CLI, etc.
    juridica: str                      # Cláusula DPA, Aviso de privacidad, Denuncia penal, etc.
    organizativa: str                  # Circular rectoral, directiva de purga, NTS MINSA, etc.
    plazo_legal_anpd: str              # Obligación y plazo (ej. "48 horas según D.S. 016-2024-JUS")
```

* **Ejemplo R-004 (Consentimiento presunto en matrícula/comedor):**
  * `db_sql`: `None` (no es un error de BD).
  * `software_nosql`: Código React/HTML con `checked=false` y desacople del botón de envío.
  * `juridica`: Rediseño de Política de Privacidad con casillas independientes por finalidad.
  * `organizativa`: Directiva DUDE que prohíbe condicionar el servicio asistencial.
* **Ejemplo R-006 (Transferencia a AWS Irlanda):**
  * `db_sql`: `None`.
  * `software_nosql`: Comandos de AWS CLI para revocar Access Keys IAM y cifrar bucket S3 con KMS.
  * `juridica`: Addendum DPA con Cláusulas Contractuales Tipo (SCC) e inscripción en RNPDP.
  * `organizativa`: Política de Homologación de Nubes de la OTI.

---

### Capa 2: Base de Datos y Persistencia Híbrida (`src/backend/infrastructure/db.py` y `repository.py`)

#### Problema Actual:
El código solo se conecta a `empresa_conocimiento.db` (SQLite). No existe forma de que el agente lea o escriba en PostgreSQL (`unsa_pims_db`).

#### Cambio Propuesto:
1. **Configuración en `.env`:**
   ```env
   # Si estas variables están presentes, el agente se conecta a PostgreSQL
   PG_HOST=localhost
   PG_PORT=5432
   PG_DATABASE=unsa_pims_db
   PG_USER=postgres
   PG_PASSWORD=tu_password
   ```
2. **Conector Híbrido con Fallback Automático:**
   * Si las credenciales de PostgreSQL son válidas y la conexión tiene éxito, el repositorio trabaja directamente sobre el esquema `demo` de PostgreSQL.
   * Si no están configuradas o el servicio está apagado (ej. pruebas sin base de datos levantada), conmuta automáticamente a SQLite para que el agente nunca falle.
3. **Mapeo de las 6 Tablas del Agente 6 en el Repositorio:**
   * Métodos para:
     * `listar_incidentes_unsa()`: Lee de `demo.core_incident`.
     * `registrar_incidente_unsa(datos)`: Inserta un nuevo incidente dictaminado en `demo.core_incident` y sus acciones en `demo.core_incidentaction`.
     * `listar_trazas_seguridad()`: Consulta eventos de `demo.core_securitylog`.

---

### Capa 3: Servicio de Generación de Dictámenes (`src/backend/services/export_service.py`)

#### Problema Actual:
Genera un informe básico de auditoría que no cumple con el estándar de incidentes ISO 27035 ni con los requisitos de notificación formal ante la ANPD.

#### Cambio Propuesto:
Implementar el generador formal de **Dictamen Pericial de Incidente de Brecha** con las 7 secciones normalizadas:
1. **Metadatos y Cadena de Custodia** (Datos del Rector, DPO, activo y fechas).
2. **Triaje y Calificación CID** (Confidencialidad, Integridad, Disponibilidad).
3. **Evaluación de Riesgo para los Titulares** (Criterios EDPB / ANPD).
4. **Tasación Pericial de Multa** (Cálculo exacto en UIT y Soles con precedente ANPD).
5. **Medidas de Contención Inmediata**.
6. **Plan de Remediación Multidimensional** (Las 4 capas de solución técnica, jurídica y organizativa).
7. **Cédula Oficial de Notificación ANPD en 48 Horas** (Formato listo para exportar y presentar ante la mesa de partes del MINJUSDH).

---

### Capa 4: Interfaz de Usuario (`src/frontend/js/app.jsx`)

#### Problema Actual:
La interfaz menciona una clínica privada ficticia, muestra solo hallazgos de archivos subidos y solo enseña un bloque de código SQL.

#### Cambio Propuesto (Simple, Limpio y sin Sobreingeniería):
1. **Reemplazo de Identidad y Activos:**
   * Cambiar el selector de mockups para que liste los sistemas reales de la UNSA:
     * *Hospital Docente de Zamácola (`SYS-HOSPITAL`)*
     * *Portal de Admisión SISADMISION (`SYS-SISADMIS`)*
     * *Tesorería Virtual UNSApay (`APP-UNSAPAY`)*
     * *Sistema Académico SISUNSA (`SYS-SISUNSA`)*
     * *Trámite Documentario TRAMITED (`APP-TRAMITED`)*
     * *Comedor Universitario SISCOM (`APP-SISCOM`)*
2. **Pestaña Nueva: "Incidentes UNSA (`demo.core_incident`)"**:
   * Una tabla ordenada que muestra los 7 incidentes poblados con su código (`INC-UNSA-2026-001` al `007`), título, activo afectado, multa estimada y estado.
   * Botón por fila: *"Ver Dictamen Pericial"* o *"Descargar Reporte ANPD"*.
3. **Visualizador de Remediación por Pestañas en el Detalle del Hallazgo:**
   * Cuando el usuario hace clic en un hallazgo o incidente, la sección de solución se divide en sub-pestañas limpias:
     * `[Base de Datos SQL]` (Script transaccional con botón de copiar).
     * `[Software / Nube / No-SQL]` (Código React, Argon2id o comandos AWS CLI).
     * `[Medida Jurídica]` (Cláusula DPA, Aviso de privacidad, etc.).
     * `[Directiva Institucional]` (Texto de la Circular Rectoral o Resolución).
4. **Botón de Acción: "Registrar Incidente en BD UNSA"**:
   * Si el usuario realiza un análisis nuevo mediante el motor DSPM o el chat, un botón permite guardar el hallazgo como incidente formal en `demo.core_incident` de PostgreSQL.
5. **Chat con el Privacy Coach:**
   * Se mantiene tal como está, ya que su capacidad de responder con citas directas a la Ley 29733, controles ISO 27701 y precedentes de la ANPD es excelente.

---

## 4. Matriz de Decisiones de Alcance (¿Qué va y qué NO va?)

Para evitar perder tiempo en funcionalidades innecesarias, definimos con claridad los límites:

```text
+-------------------------------------------------------------+-----------+-------------------------------------------------------------+
| Funcionalidad Propuesta                                     | ¿Se Hace? | Motivo / Justificación Técnica                              |
+-------------------------------------------------------------+-----------+-------------------------------------------------------------+
| Remediación en 4 Capas (SQL, No-SQL, Jurídica, Directiva)   |    SÍ     | Vital: Cumple A.5.26 ISO 27701 y resuelve fallas no-SQL.     |
| Dictamen Pericial estructurado bajo ISO 27035 (7 secciones) |    SÍ     | Vital: Formato oficial estándar y profesional para peritajes|
| Cédula de Notificación ANPD en 48 horas en el dictamen      |    SÍ     | Vital: Cumple Cl. 7.2.9 y D.S. 016-2024-JUS sin sobrecosto. |
| Conector híbrido PostgreSQL (unsa_pims_db) + SQLite fallback|    SÍ     | Vital: Conecta el agente a la base de datos real del curso. |
| Pestaña de consulta de incidentes reales de la UNSA         |    SÍ     | Vital: Permite ver las 7 brechas maestras en la interfaz.   |
| Activos reales de la UNSA en lugar de clínica ficticia      |    SÍ     | Vital: Coherencia con el proyecto y los 15 macroprocesos.   |
+-------------------------------------------------------------+-----------+-------------------------------------------------------------+
| Widget de cronómetro regresivo de 48h en tiempo real        |    NO     | Descartado: Sobreingeniería de interfaz; no somos un reloj. |
| Módulo de asignación de tareas a personas tipo Jira/Kanban  |    NO     | Descartado: El agente es analítico/pericial, no un ERP/Ticketing.|
| Sistema de envío automatizado de correos SMTP en vivo       |    NO     | Descartado: Riesgo de envío accidental; basta generar el texto.|
| Editor WYSIWYG interactivo de contratos en el frontend     |    NO     | Descartado: Innecesario; basta con bloques de código y copia.|
+-------------------------------------------------------------+-----------+-------------------------------------------------------------+
```

---

## 5. Preguntas Abiertas y Puntos de Decisión para el Usuario

Antes de tocar código, me gustaría conocer tu opinión sobre los siguientes 3 puntos clave:

1. **Modo de Operación del Agente con PostgreSQL:**
   * *Opción A (Recomendada):* El agente puede trabajar tanto **analizando archivos de esquema/código de la UNSA** como **leyendo/guardando directamente en PostgreSQL `unsa_pims_db`** si está configurada la conexión.
   * *¿Te parece bien mantener esta flexibilidad híbrida para que nunca falle aunque no tengas PostgreSQL encendido?*

2. **Presentación de la Remediación Multidimensional en la Interfaz:**
   * ¿Prefieres que en la tarjeta de cada hallazgo aparezcan **pestañas clicables** (`[SQL]`, `[No-SQL / Código]`, `[Jurídico]`, `[Directiva]`), o prefieres que se muestren en **bloques desplegables (acordeón)** uno debajo del otro?

3. **Alcance de los Activos de la UNSA:**
   * ¿Deseas que dejemos como opciones preconfiguradas en el sistema los 6 sistemas principales analizados (*Hospital Zamácola, Admisión, Tesorería, SISUNSA, TRAMITED y Comedor*), de modo que se puedan cargar y auditar con un solo clic?

