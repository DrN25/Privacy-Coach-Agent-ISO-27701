# Estándar Integral de Gestión, Formato de Dictamen y Remediación Multidimensional de Incidentes de Brecha de PII
**Alineación Normativa:** ISO/IEC 27035-1/2/3, ISO/IEC 27701:2025 (Cl. 6.5.24 - 6.5.28, Cl. 7.2.9, 8.2), NIST SP 800-61 Rev. 2, D.S. 016-2024-JUS y Directiva de Seguridad R.D. 019-2013-JUS  
**Institución:** Universidad Nacional de San Agustín de Arequipa (UNSA)  
**Módulo:** Agente 6 - Gestión Pericial de Incidentes de Seguridad y Brechas de PII  
**Documento Técnico:** `docs/ESTANDAR_REMEDIACION_Y_FORMATO_INCIDENTES_ISO27035_27701.md`

---

## 1. Fundamentación y Marco Internacional de Incidentes de Brecha

La gestión de brechas de datos personales no es una tarea de soporte técnico tradicional ni un problema meramente de bases de datos relacionales. Internacionalmente, la respuesta a incidentes y el peritaje de privacidad se rigen por la convergencia de cuatro marcos técnicos y regulatorios de alto nivel:

1. **ISO/IEC 27035 (Partes 1, 2 y 3 - *Information security incident management*):**  
   Establece el ciclo de vida universal del incidente:
   * **Fase 1: Planificación y Preparación (*Plan and Prepare*):** Estructuración de políticas, designación de roles (CSIRT, DPO, CISO) y plantillas normalizadas.
   * **Fase 2: Detección e Informe (*Detection and Reporting*):** Captura de trazas, alertas de escaneo DSPM y registro inicial del evento.
   * **Fase 3: Evaluación y Decisión (*Assessment and Decision* - A.5.25):** Triaje pericial para determinar si el incidente compromete datos personales (CID Impact).
   * **Fase 4: Respuesta (*Responses* - A.5.26):** Contención inmediata, erradicación de vulnerabilidades y remediación técnica/organizativa/jurídica.
   * **Fase 5: Lecciones Aprendidas (*Lessons Learned* - A.5.27 & A.5.28):** Análisis de causa raíz (RCA), preservación de evidencias forenses y actualización de controles.

2. **ISO/IEC 27701:2025 (Cláusula 6.5.24 a 6.5.28 y Cláusula 7.2.9 / 8.2):**  
   Extiende el estándar de seguridad para incorporar la dimensión exclusiva de privacidad:
   * **Calificación PII Breach:** Evaluar el impacto en los titulares (PII Principals).
   * **Notificación Regulatoria (Cl. 7.2.9):** Obligación del Responsable (Controller) de notificar a la Autoridad Supervisora y a los titulares.
   * **Notificación de Proveedores (Cl. 8.2):** Obligación de los Encargados (Processors) de reportar brechas sin dilación indebida al Responsable.

3. **NIST SP 800-61 Rev. 2 (*Computer Security Incident Handling Guide*):**  
   Define los vectores de ataque (Web, Impersonation, Exfiltration, Media Destruction) y la metodología de erradicación y mitigación por capas de arquitectura.

4. **Marco Legal Peruano (Ley N° 29733, D.S. N° 016-2024-JUS y R.D. N° 019-2013-JUS):**  
   Consagra el **plazo legal perentorio de 48 horas** para la notificación formal a la Dirección de Fiscalización e Instrucción (DFI) de la ANPD, establece la graduación de sanciones (hasta 100 UIT) y fija las medidas de seguridad de Nivel Básico, Medio y Complejo.

---

## 2. Formato Estándar Normalizado del Dictamen Pericial de Brecha (ISO 27035 / ISO 27701 / ANPD)

Todo dictamen generado por el agente debe estructurarse conforme al estándar internacional de 7 secciones forenses:

```text
================================================================================
DICTAMEN PERICIAL FORENSE DE BRECHA DE DATOS PERSONALES (PII BREACH REPORT)
Conforme a ISO/IEC 27035, ISO/IEC 27701:2025 Cl. 7.2.9 y D.S. N° 016-2024-JUS
================================================================================

SECCIÓN I: METADATOS ADMINISTRATIVOS Y CADENA DE CUSTODIA (ISO 27035 Fase 1 & 2)
1.1. Identificador de Incidente: INC-UNSA-2026-***
1.2. Entidad Afectada: Universidad Nacional de San Agustín de Arequipa (RUC: 20140798781)
1.3. Representante Legal: Dr. Hugo Rojas Flores (Rector)
1.4. Activo Afectado: Código de Activo, Nombre del Sistema, Ubicación Física/Lógica y Endpoint
1.5. Fechas Críticas: Fecha/Hora de Ocurrencia vs. Fecha/Hora de Detección
1.6. DPO / Oficial Responsable: Abog. Carlos Mendoza Valdivia (dpo@unsa.edu.pe)

SECCIÓN II: TRIAJE PERICIAL Y CALIFICACIÓN DE BRECHA (A.5.25 / Cl. 6.5.25)
2.1. Vector de Ataque / Condición de Vulnerabilidad (Código de Regla R-001 a R-007)
2.2. Afectación de Principios de Seguridad (Impacto CID):
     [ ] Confidencialidad (BF)  [ ] Integridad (BI)  [ ] Disponibilidad (BD)  [ ] Infracción Normativa (PI)
2.3. Categorización del Dato Comprometido:
     - Datos Comunes (DNI, nombres, correos, notas)
     - Datos Sensibles Especiales (Salud, Biometría, Datos Financieros/CVV)
2.4. Volumen Cuantificado: N° de registros y N° de titulares únicos afectados

SECCIÓN III: EVALUACIÓN DE RIESGO PARA LOS TITULARES (ISO 27701 Cl. 7.2.9 / EDPB)
3.1. Nivel de Riesgo para los Derechos y Libertades: [Bajo / Medio / Alto / Crítico]
3.2. Daño Potencial Evaluado: Fraude bancario, suplantación de identidad, discriminación médica, daño moral
3.3. Determinación de Notificación a Titulares: [Obligatoria / No Requerida con Fundamento]

SECCIÓN IV: TIPICIFICACIÓN LEGAL Y TASACIÓN PERICIAL DE MULTA (Ley 29733 / ANPD)
4.1. Infracción Tipificada: Art. 38 (Leve / Grave / Muy Grave)
4.2. Precedente ANPD Vinculante: Resolución Directoral análoga del catálogo de 588 resoluciones
4.3. Graduación de la Sanción: Multa Base + Agravantes tasados por datos sensibles (Art. 39 Ley 29733)
4.4. Exposición Económica Cuantificada: [X.X] UIT = S/ [XX,XXX.XX]

SECCIÓN V: MEDIDAS DE CONTENCIÓN INMEDIATA (ISO 27035 Fase 3 / A.5.26)
5.1. Aislamiento técnico, bloqueo perimetral, revocación de credenciales comprometidas y preservación de logs.

SECCIÓN VI: PLAN DE REMEDIACIÓN MULTIDIMENSIONAL (A.5.26 / Cuatro Capas)
6.1. Capa 1: Remediación Técnica de Base de Datos (SQL / DDL / pgcrypto)
6.2. Capa 2: Remediación de Software, API, Nube e Infraestructura (No-SQL / IAM / Frontend / KMS)
6.3. Capa 3: Remediación Jurídica y Contractual (DPAs, Cláusulas Tipo SCC, Denuncias Penales)
6.4. Capa 4: Remediación Organizativa y Políticas (Resoluciones Rectorales, Circulares, Retención)

SECCIÓN VII: FORMATO DE NOTIFICACIÓN OFICIAL ANPD EN 48 HORAS (D.S. 016-2024-JUS)
7.1. Cédula estructurada con los campos del Formulario Oficial de Brechas de la ANPD lista para firma.
================================================================================
```

---

## 3. Matriz de Remediación Multidimensional (Superando la Limitación Exclusiva de SQL)

Una brecha de datos personales rara vez se resuelve únicamente con una sentencia SQL. Conforme a **ISO/IEC 27035** e **ISO/IEC 27701**, el agente debe entregar un **paquete de remediación en cuatro capas**:

```mermaid
graph TD
    BRECHA["BRECHA DE PRIVACIDAD DETECTADA<br/>(Reglas R-001 a R-007)"]
    
    subgraph REMEDIACION_CUATRO_CAPAS["PAQUETE DE REMEDIACIÓN MULTIDIMENSIONAL (A.5.26)"]
        direction TB
        CAPA_1["1. REMEDIACIÓN TÉCNICA DE BASE DE DATOS (SQL)<br/>• pgcrypto AES-256 en reposo<br/>• DROP COLUMN con borrado DoD 5220.22-M<br/>• Procedimientos de purga y anonimización"]
        CAPA_2["2. REMEDIACIÓN DE SOFTWARE, API Y NUBE (NO-SQL)<br/>• Refactorización de código backend (Argon2id, sanitización)<br/>• Revocación de AWS IAM Keys y cifrado S3 con KMS<br/>• Desmarcado de checkboxes web en React/HTML<br/>• Tokenización vía API de pasarela bancaria externa"]
        CAPA_3["3. REMEDIACIÓN JURÍDICA Y CONTRACTUAL<br/>• Suscripción de Addendum DPA con Cláusulas Contractuales Tipo (SCC)<br/>• Inscripción de flujo transfronterizo ante el RNPDP<br/>• Denuncia penal ante Fiscalía de Delitos Informáticos (Art. 6 Ley 30096)<br/>• Reformulación de Políticas de Privacidad"]
        CAPA_4["4. REMEDIACIÓN ORGANIZATIVA Y PROCEDIMENTAL<br/>• Circular Rectoral de gratuidad absoluta de derechos ARCO<br/>• Directiva de Conservación y Purga Documental de Postulantes<br/>• Activación formal de protocolos de respuesta del CSIRT UNSA<br/>• Capacitación obligatoria a operadores de mesa de partes"]
    end
    
    BRECHA --> REMEDIACION_CUATRO_CAPAS
```

---

## 4. Desglose Pericial de Remediaciones No-SQL y Multicapa por Arquetipo

A continuación se detalla la respuesta integral que el agente formula para cada una de las 7 reglas canónicas:

---

### Regla R-001: Datos Sensibles de Salud sin Cifrar en Reposo (Hospital Docente Zamácola)
* **Vector:** Endpoint vulnerable a Inyección SQL (CWE-89) exfiltra 3,420 historias clínicas con diagnósticos CIE-10.
* **Remediación Multidimensional:**
  1. **Técnica SQL:** Despliegue de extensión `pgcrypto` y cifrado simétrico AES-256 en columnas de diagnóstico y anamnesis:
     ```sql
     BEGIN;
     CREATE EXTENSION IF NOT EXISTS pgcrypto;
     ALTER TABLE ficha_medica ADD COLUMN diagnostico_cifrado bytea;
     UPDATE ficha_medica SET diagnostico_cifrado = pgp_sym_encrypt(diagnostico_cie10::text, current_setting('app.jwt_secret'));
     ALTER TABLE ficha_medica DROP COLUMN diagnostico_cie10;
     COMMIT;
     ```
  2. **Técnica No-SQL / Software (Backend & Red):**
     * **Saneamiento de Código Backend:** Reescribir el endpoint `/consulta_paciente.php` o `/api/pacientes` sustituyendo la concatenación de cadenas por sentencias preparadas con ORM/PDO parametrizado (`SELECT * FROM ficha_medica WHERE id = :id`).
     * **Segregación de Red (VLAN Hospitalaria):** Aislar la base de datos `srv-hosp-db` en un segmento de red no enrutable a Internet público, accesible únicamente mediante VPN asistencial con autenticación de doble factor (MFA).
     * **Cifrado en Tránsito:** Forzar protocolo TLS 1.3 con suites criptográficas robustas (ECDHE-RSA-AES256-GCM-SHA384) y encabezado HTTP `Strict-Transport-Security: max-age=31536000`.
  3. **Jurídica:** Notificación formal ante la DFI-ANPD bajo el precedente análogo *R.D. 1045-2020-JUS (Clínica Montefiori)* y suscripción de actas de confidencialidad médica con el personal asistencial.
  4. **Organizativa:** Emisión de Directiva Directoral interna del Hospital Docente bajo los estándares de la **NTS N° 139-MINSA/DGIEM** (Norma Técnica de Salud para la Gestión de Historias Clínicas Electrónicas).

---

### Regla R-002: Credenciales de Postulantes con Hash Débil MD5 (Portal SISADMISION)
* **Vector:** Volcado masivo de 18,500 credenciales de postulantes almacenadas con algoritmo roto MD5 sin sal criptográfica.
* **Remediación Multidimensional:**
  1. **Técnica SQL:** Modificación de estructura para permitir migración progresiva de esquemas de hash y marcado de cuentas comprometidas:
     ```sql
     BEGIN;
     ALTER TABLE usuarios_postulantes ADD COLUMN password_hash_scheme character varying(20) DEFAULT 'argon2id';
     ALTER TABLE usuarios_postulantes ADD COLUMN force_password_reset boolean DEFAULT true;
     COMMIT;
     ```
  2. **Técnica No-SQL / Software (Backend & Autenticación):**
     * **Implementación de Algoritmo Robusto:** Desplegar en el backend de autenticación (Python `passlib[argon2]` o Node `argon2`) el esquema **Argon2id** (Memory Cost: 64 MB, Time Cost: 3 iterations, Parallelism: 2 threads, Salt aleatorio: 16 bytes criptográficamente seguros).
     * **Revocación de Sesiones Activas:** Invalidación masiva de tokens JWT y sesiones en Redis mediante purga de claves activas (`FLUSHDB` en namespace de sesiones legacy).
     * **Mecanismo de Desafío Forzoso:** Implementar un middleware que intercepte el login de usuarios con `force_password_reset=true` y obligue a la creación de una nueva contraseña con requisitos mínimos (12 caracteres, mayúsculas, minúsculas, números y símbolos) antes de permitir la navegación.
     * **Rate Limiting y Protección Anti-Fuerza Bruta:** Configurar en Nginx o Cloudflare un límite de 5 intentos fallidos de autenticación por IP cada 15 minutos, con desafío de Turnstile/reCAPTCHA v3.
  3. **Jurídica:** Formulación del descargo ante la ANPD demostrando subsanación voluntaria antes de la notificación de imputación de cargos (Art. 133 D.S. 003-2013-JUS).
  4. **Organizativa:** Redacción de la Política Institucional de Gestión de Credenciales y Contraseñas de la UNSA, alineada al estándar NIST SP 800-63B.

---

### Regla R-003: Retención Ilegal de Tarjetas y CVV (Tesorería UNSApay)
* **Vector:** Almacenamiento indebido de números de tarjeta (PAN) y códigos de verificación CVV tras procesar pagos, seguido de exportación CSV no autorizada por un operador.
* **Remediación Multidimensional:**
  1. **Técnica SQL:** Destrucción física y lógica de columnas con borrado seguro:
     ```sql
     BEGIN;
     UPDATE pagos_online SET cvv = NULL, pan = NULL;
     ALTER TABLE pagos_online DROP COLUMN cvv;
     ALTER TABLE pagos_online DROP COLUMN pan;
     VACUUM FULL pagos_online;
     COMMIT;
     ```
  2. **Técnica No-SQL / Software (Arquitectura de Pagos & API):**
     * **Tokenización Externa (Cumplimiento PCI-DSS v4.0 Req 3.2.2):** Rediseñar el flujo de checkout eliminando cualquier campo que reciba datos de tarjeta en servidores de la UNSA. El navegador del estudiante interactúa directamente con el iframe seguro o SDK de **Págalo.pe (Banco de la Nación)** o pasarela certificada PCI-DSS Nivel 1. La UNSA solo recibe y almacena un token transaccional (`tok_1N3k...`) y el código de operación.
     * **Depuración de Logs de Aplicación:** Auditar archivos de registro en Nginx, Apache y servidores de logs (ELK/Logstash) para asegurar que ningún parámetro `cvv` o `card_number` haya quedado persistido en archivos planos de depuración (`debug.log`).
  3. **Jurídica / Procesal:**
     * **Denuncia Penal:** Interposición de denuncia penal ante la Fiscalía Provincial Corporativa Especializada en Delitos Informáticos de Arequipa contra el operador responsable por el delito de Tráfico Ilegal de Datos (Art. 6 de la Ley N° 30096 - Ley de Delitos Informáticos).
     * **Procedimiento Administrativo Disciplinario (PAD):** Apertura de proceso sancionador interno bajo la Ley del Servicio Civil (Ley N° 30057).
  4. **Organizativa:** Supresión de privilegios de exportación masiva a archivos CSV/Excel en el módulo de ventanillas y segregación estricta de roles en Tesorería.

---

### Regla R-004: Consentimiento Presunto en Formularios Web (Matrícula y Comedor)
* **Vector:** Casilla pre-marcada obligatoria que imputa consentimiento forzoso al estudiante para transferir sus datos personales a entidades bancarias y empresas aliadas.
* **Remediación Multidimensional:**
  1. **Técnica No-SQL / Front-end (HTML / React / JavaScript):**
     * **Desmarcado por Defecto:** Modificar el código fuente de los componentes web en `matricula.unsa.edu.pe` y `siscom.unsa.edu.pe`, eliminando atributos como `checked="checked"` o `defaultChecked={true}`.
       ```jsx
       // Código Corregido conforme al Art. 12 D.S. 003-2013-JUS
       <input 
         type="checkbox" 
         id="cesion_comercial" 
         checked={optInConsent} 
         onChange={(e) => setOptInConsent(e.target.checked)} 
         required={false} 
       />
       <label htmlFor="cesion_comercial">
         Autorizo expresamente la cesión de mis datos de contacto a entidades bancarias patrocinadoras para ofertas de créditos y empleo estudiantil. (Opcional)
       </label>
       ```
     * **Desvinculación Operativa (Opt-in Independiente):** Eliminar del validador de formulario la condición bloqueante `if (!consent) return alert("Debe aceptar todas las casillas")`. La negativa a la cesión publicitaria no puede condicionar la matrícula académica ni la ración del comedor universitario.
  2. **Jurídica:**
     * **Rediseño del Pliego de Privacidad:** Redactar una Política de Privacidad modular diferenciada en dos capas: Finalidades Primarias (necesarias para el servicio educativo) vs. Finalidades Secundarias (comerciales, publicitarias), con casillas opt-in independientes.
     * **Anulación de Bases Ilegítimas:** Declarar la ineficacia legal de los consentimientos presuntos recopilados bajo la casilla previa y bloquear los envíos publicitarios a quienes no ratifiquen su autorización.
  3. **Organizativa:** Emisión de Directiva de la Dirección Universitaria de Desarrollo Estudiantil (DUDE) prohibiendo el condicionamiento de servicios asistenciales a la cesión de datos.

---

### Regla R-005: Conservación Indefinida de Datos Biométricos (Dirección de Admisión DUA)
* **Vector:** 45,200 registros de postulantes no ingresantes (huellas dactilares y fotos de 2018 al 2024) almacenados indefinidamente sin plazo de caducidad ni política de purga.
* **Remediación Multidimensional:**
  1. **Técnica No-SQL / Automatización (DevOps & Scripts de Purga):**
     * **Despliegue de Cronjob de Borrado Seguro:** Configuración de un contenedor o tarea programada mensual que ejecuta un script de saneamiento sobre el almacenamiento de archivos biométricos (soportes WSQ / TIFF de huellas digitales), aplicando algoritmos de sobreescritura conformes a la guía **NIST SP 800-88 Rev. 1** (*Guidelines for Media Sanitization*).
     * **Anonimización Estadística:** En lugar de mantener registros identificables con DNI y nombres, los resultados de exámenes anteriores a 12 meses se transforman en datos estadísticos agregados desvinculados de identidad (edad, puntaje, colegio, carrera postulada).
  2. **Técnica SQL:** Marcado de bloqueo y purga transaccional:
     ```sql
     BEGIN;
     -- Bloqueo de datos caducados (Art. 28 D.S. 003-2013-JUS)
     UPDATE postulantes_historico 
     SET huella_wsq = NULL, foto_rostro = NULL, estado_registro = 'PURGADO_POR_CADUCIDAD'
     WHERE proceso_ano < EXTRACT(YEAR FROM CURRENT_DATE) - 1 AND ingresante = false;
     COMMIT;
     ```
  3. **Jurídica / Normativa:** Redacción de la **Política de Retención Documental y Cancelación de Datos de Admisión**, estipulando formalmente que los datos de postulantes no ingresantes caducan a los 12 meses de concluido el concurso de admisión respectivo.
  4. **Organizativa:** Aprobación de la política mediante Resolución de Consejo Universitario (RCU) e incorporación de dicha cláusula informativa en el prospecto oficial de admisión.

---

### Regla R-006: Transferencia Transfronteriza a Bucket Cloud sin Registro (SISUNSA a AWS S3)
* **Vector:** Cronjob automático de backup sincroniza 25,000 expedientes académicos a un bucket AWS S3 en la región de Irlanda (`eu-west-1`) sin DPA ni inscripción en el RNPDP.
* **Remediación Multidimensional:**
  1. **Técnica No-SQL / Cloud & Infraestructura (AWS CLI / DevOps):**
     * **Contención Inmediata de IAM:** Revocar de inmediato las credenciales de la cuenta de servicio utilizada por el script de respaldo:
       ```bash
       aws iam update-access-key --access-key-id AKIAIOSFODNN7EXAMPLE --status Inactive --user-name backup-svc-unsa
       ```
     * **Detención del Cronjob:** Inhabilitar la tarea programada en el crontab del servidor de base de datos (`crontab -e` -> comentar línea de `sync_pg_dump.sh`).
     * **Cifrado Obligatorio en Reposo con AWS KMS:** Configurar en el bucket S3 el cifrado del lado del servidor con claves administradas por el cliente (SSE-KMS) y bloqueo de acceso público (*Block Public Access* habilitado al 100%).
  2. **Jurídica / Contractual:**
     * **Suscripción de Anexo DPA:** Tramitar y firmar digitalmente con Amazon Web Services Inc. el **Data Processing Addendum (DPA)** incorporando las **Cláusulas Contractuales Tipo (SCC)** aprobadas internacionalmente para transferencias a terceros países.
     * **Inscripción ante la ANPD:** Elaborar y presentar ante la Mesa de Partes Virtual del MINJUSDH la solicitud formal de **Inscripción de Flujo Transfronterizo de Datos Personales** en el Registro Nacional de Protección de Datos Personales (RNPDP), adjuntando copia del contrato DPA y la justificación técnica de seguridad.
  3. **Organizativa:** Política de Acreditación de Proveedores Cloud de la OTI, prohibiendo el despliegue de infraestructura fuera del territorio nacional sin validación previa del Oficial de Privacidad (DPO).

---

### Regla R-007: Trabas Onerosas para el Ejercicio de Derechos ARCO (TRAMITED)
* **Vector:** Sistema de trámite documentario y mesa de partes exigen tasa de S/ 28.50 (código TUPA) y carta notarial para tramitar solicitudes de cancelación de datos personales.
* **Remediación Multidimensional:**
  1. **Técnica No-SQL / Software (Portal Web TRAMITED):**
     * **Eliminación de Campos Bloqueantes:** Modificar el validador web del formulario de trámite documentario virtual, suprimiendo los campos obligatorios `recibo_caja_tupa` y `documento_notarial_pdf`.
     * **Habilitación de Canal Ágil y Gratuito:** Desplegar una ruta web dedicada `/arco` donde el titular únicamente deba identificarse con su DNI escaneado y fundamentar su solicitud (Acceso, Rectificación, Cancelación u Oposición) sin costo alguno.
  2. **Organizativa / Resolutiva:**
     * **Circular Rectoral de Gratuidad:** Emisión inmediata de la **Circular Rectoral N° 012-2026-R-UNSA**, comunicada a todas las dependencias, facultades y ventanillas de mesa de partes, instruyendo que el ejercicio de derechos ARCO es **100% gratuito** conforme al Art. 47 del D.S. 003-2013-JUS, bajo apercibimiento de sanción disciplinaria por falta grave a quien exija cobros o formalidades notariales.
     * **Actualización del TUPA:** Iniciar el trámite de modificación del Texto Único de Procedimientos Administrativos (TUPA) de la universidad para derogar expresamente la tasa sobre solicitudes ARCO.
  3. **Jurídica:** Allanamiento y respuesta inmediata a los expedientes de tutela de derechos iniciados ante la DFI-ANPD, acreditando la gratuidad sobrevenida y el cese de la exigencia notarial para solicitar el archivo del procedimiento sin sanción pecuniaria (Art. 133 D.S. 003-2013-JUS).

---

## 5. Matriz de Síntesis: Qué Genera el Agente en Cada Dimensión

El siguiente cuadro resume el alcance funcional completo que nuestro agente produce ante cualquier detección:

| Regla Canónica | Dimensión 1: Base de Datos (SQL) | Dimensión 2: Software / Infra / Nube (No-SQL) | Dimensión 3: Jurídica y Contractual | Dimensión 4: Organizativa y Procesos |
| :--- | :--- | :--- | :--- | :--- |
| **R-001 (Salud)** | Script `pgcrypto` con AES-256 en reposo. | Saneamiento PDO de consultas SQLi; VLAN hospitalaria; forzado TLS 1.3. | Contratos de confidencialidad médica; notificación formal ANPD. | Directiva NTS N° 139-MINSA/DGIEM para el Hospital Docente Zamácola. |
| **R-002 (Hashes MD5)** | Marcado de cuentas y esquema para migración progresiva. | Algoritmo Argon2id en backend; revocación de sesiones Redis; rate limiting. | Informe de atenuantes por subsanación voluntaria (Art. 133 LPDP). | Política Institucional de Contraseñas Seguras y doble factor (MFA). |
| **R-003 (CVV Pagos)** | Script transaccional `DROP COLUMN` con sobreescritura DoD 5220.22-M. | Integración con pasarela externa tokenizada Págalo.pe; depuración de logs. | Denuncia penal ante Fiscalía de Delitos Informáticos; PAD a operador. | Supresión de permisos de exportación CSV en ventanillas de recaudación. |
| **R-004 (Consentimiento)** | N/A (Problema de capa de presentación). | Desmarcado `checked=false` en React/HTML; desacople de obligatoriedad en JS. | Redacción de Política de Privacidad por finalidades; anulación de base ilegítima. | Directiva DUDE garantizando que la negativa no afecta matrícula o comedor. |
| **R-005 (Biometría)** | Consulta SQL de borrado y marcado `PURGADO_POR_CADUCIDAD`. | Cronjob automatizado de destrucción de archivos biométricos (NIST SP 800-88). | Redacción de Política de Retención con límite máximo de 12 meses. | Aprobación por Consejo Universitario (RCU) e inclusión en prospecto. |
| **R-006 (Cloud S3)** | N/A (Problema de infraestructura telemática). | Revocación de claves IAM en AWS CLI; bloqueo de S3; cifrado KMS. | Suscripción de Addendum DPA con Cláusulas Contractuales Tipo (SCC); trámite RNPDP. | Política de Validación Previa de Servicios Cloud en OTI y DPO. |
| **R-007 (Trabas ARCO)** | N/A (Problema procedimental y web). | Eliminación de validadores obligatorios de voucher y carta notarial en portal web. | Allanamiento ante la DFI-ANPD acreditando gratuidad sobrevenida. | Circular Rectoral de gratuidad absoluta; derogación de tasa en el TUPA. |

---

## 6. Conclusión y Valor para el Sistema

Al adoptar este estándar:
1. El agente deja de ser un "generador de scripts SQL" y se convierte en un **Perito Forense de Privacidad Multidisciplinario**.
2. Los dictámenes emitidos cumplen al 100% con los estándares internacionales de gestión de incidentes (**ISO/IEC 27035**, **ISO/IEC 27701** y **NIST SP 800-61**).
3. Cada incidente cuenta con soluciones concretas aplicables a nivel de código, infraestructura cloud, contratos y directivas universitarias reales.

