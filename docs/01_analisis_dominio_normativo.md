# 01. ANÁLISIS DE DOMINIO Y MARCO NORMATIVO: ISO/IEC 27701:2025
## Sistema Autónomo de Auditoría y Capacitación en Privacidad (PIMS Standalone)

**Curso:** Auditoría de Sistemas / TI  
**Institución:** Universidad Nacional de San Agustín (UNSA) - VIII Semestre  
**Proyecto:** Trabajo de Investigación Formativa (TIF)  
**Versión Normativa:** **ISO/IEC 27701:2025 (Publicada en Octubre 2025)**  

---

## 1. ISO/IEC 27701:2025 como Norma de Gestión Independiente (Standalone)

En octubre de 2025 se publicó **ISO/IEC 27701:2025**, transformando la norma en un Sistema de Gestión de Información de Privacidad (PIMS) independiente (Tipo A). 

### 1.1. Diferencia Crítica: Versión 2019 vs. Versión 2025

| Característica | ISO/IEC 27701:2019 (Obsoleta) | ISO/IEC 27701:2025 (Vigente) |
| :--- | :--- | :--- |
| **Naturaleza Normativa** | Norma de Extensión Sectorial (Tipo B). | **Norma de Sistema de Gestión Independiente (Tipo A - Standalone).** |
| **Dependencia de ISO 27001** | **Obligatoria e Inseparable:** No se podía certificar ni implementar sin tener previamente certificado un SGSI bajo ISO/IEC 27001. | **DESAPARECE LA DEPENDENCIA OBLIGATORIA:** Una organización puede implementar y certificarse en ISO 27701:2025 de forma 100% independiente. |
| **Estructura** | Cláusulas 5 a 8 con mapeos dispersos a ISO 27001 e ISO 27002:2013. | **Estructura Armonizada (Harmonized Structure - HS):** Cláusulas 4 a 10 estándar de ISO (Contexto, Liderazgo, Planificación, Soporte, Operación, Evaluación, Mejora). |
| **Catálogo de Controles** | 49 controles específicos de PIMS divididos en Anexos A y B (sobre base 27002:2013). | **Estructura Consolidada de 78 Controles de Privacidad**, alineados con los 4 dominios de ISO/IEC 27002:2022 y guías específicas en Anexos A y B. |
| **Enfoque Tecnológico** | Enfoque tradicional de servidores y bases de datos clásicas. | **Enfoque Moderno:** Directrices explícitas para Inteligencia Artificial (AI processing), Biometría, Cloud Native, IoT y microservicios. |

> [!IMPORTANT]
> **Impacto para las MYPEs y PYMEs:**
> En la versión 2019, una pequeña empresa no podía acceder a ISO 27701 sin antes gastar decenas de miles de dólares en certificar ISO 27001. En la versión **2025**, una PYME puede implementar **directamente su Sistema de Gestión de Información de Privacidad (PIMS)** sin requerir la certificación previa de seguridad general, democratizando el cumplimiento para negocios con presupuesto acotado.

---

## 2. Desglose Estructural de los 78 Controles de ISO/IEC 27701:2025

La norma 2025 organiza el cumplimiento en torno a **78 controles de privacidad** distribuidos estratégicamente según el rol de la entidad respecto a los datos personales (PII):

```text
                        ┌─────────────────────────────────────────────────────────┐
                        │                   ISO/IEC 27701:2025                    │
                        │            (Standalone PIMS Management System)          │
                        └────────────────────────────┬────────────────────────────┘
                                                     │
                                     Estructura Armonizada (Cláusulas 4 - 10)
                                                     │
             ┌───────────────────────────────────────┼───────────────────────────────────────┐
             ▼                                       ▼                                       ▼
┌─────────────────────────────┐         ┌─────────────────────────────┐         ┌─────────────────────────────┐
│    31 Controles Anexo A     │         │    18 Controles Anexo B     │         │    29 Controles Base PIMS   │
│   (PII Controllers /        │         │    (PII Processors /        │         │   (Seguridad Aplicada a     │
│   Responsables del Trat.)   │         │   Encargados del Trat.)     │         │    la Privacidad - 27002)   │
└──────────────┬──────────────┘         └──────────────┬──────────────┘         └──────────────┬──────────────┘
               │                                       │                                       │
               └───────────────────────────────────────┴───────────────────────────────────────┘
                                                       │
                                                       ▼
                                   Total Consolidado: 78 Controles
```

### 2.1. Los 31 Controles para Responsables de Tratamiento (*PII Controllers* - Anexo A)
Diseñados para la empresa que determina los fines y medios del tratamiento (ej. el dueño del e-commerce o la clínica):
1. **Condiciones para la Recolección y Procesamiento:**
   * Determinación de base legal, mecanismos de consentimiento explícito, evaluación de impacto en privacidad (PIA/DPIA), gobernanza de cookies y rastreo.
2. **Obligaciones hacia los Titulares de Datos:**
   * Políticas de privacidad transparentes, gestión automatizada de derechos ARCO (Acceso, Rectificación, Cancelación, Oposición), notificación de brechas de seguridad.
3. **Privacidad por Diseño y por Defecto (*Privacy by Design & Default*):**
   * Minimización estricta de datos recolectados, retención y borrado seguro, limitación de uso no autorizado.
4. **Compartición y Transferencias:**
   * Acuerdos de procesamiento de datos (DPA), contratos con terceros, transferencias internacionales.

### 2.2. Los 18 Controles para Encargados de Tratamiento (*PII Processors* - Anexo B)
Diseñados para la empresa que procesa datos por cuenta de un Responsable (ej. proveedores SaaS, pasarelas de pago, agencias de marketing digital):
1. Cumplimiento irrestricto de las instrucciones del Responsable.
2. Prohibición de uso de PII para fines propios (ej. no entrenar modelos de IA con datos del cliente sin autorización).
3. Devolución o eliminación segura de datos al finalizar el contrato de servicio.
4. Notificación inmediata al Responsable ante cualquier incidente de seguridad.

### 2.3. Los 29 Controles de Seguridad Aplicada a la Privacidad
Derivados de la taxonomía moderna de ISO/IEC 27002:2022, adaptados a la protección de datos:
* Controles Organizacionales (Políticas, segregación de funciones, teletrabajo).
* Controles de Personas (Concientización en privacidad, acuerdos de confidencialidad).
* Controles Físicos (Acceso a centros de datos, destrucción de soportes físicos).
* Controles Tecnológicos (Cifrado en tránsito y reposo, gestión de accesos RBAC, enmascaramiento/seudonimización de datos en desarrollo y pruebas, logging inmutable).

---

## 3. Integración con ISO/IEC 29100:2011 y Marco Peruano (ANPD / MINJUSDH)

El agente de auditoría y capacitación no solo cita la norma ISO 27701:2025; vincula cada control con los principios de **ISO/IEC 29100** y los mandatos coactivos de la **Ley Peruana N.° 29733**.

### 3.1. Los 11 Principios de ISO/IEC 29100 como Eje Pedagógico
1. Consentimiento y Elección.
2. Legitimidad y Especificación de Finalidad.
3. Limitación de Recolección.
4. Minimización de Datos.
5. Limitación de Uso, Retención y Divulgación.
6. Exactitud y Calidad.
7. Apertura, Transparencia y Notificación.
8. Participación Individual y Acceso (Derechos ARCO).
9. Rendición de Cuentas (*Accountability*).
10. Seguridad de la Información.
11. Cumplimiento de la Privacidad.

### 3.2. Marco Jurídico Peruano y Casuística Real de Sanciones (ANPD)
* **Ley N.° 29733** y su Reglamento (**D.S. 003-2013-JUS**).
* **Directiva de Seguridad R.D. 019-2013-JUS/DGPDP:** Define medidas técnicas de seguridad (Básico, Medio, Maestro).
* **R.M. N.° 476-2025-JUS:** Nueva metodología oficial para el cálculo de multas en Perú.

#### Casos Reales del MINJUSDH Indexados en el Repositorio:
* **Caso Fintech / Retail:** Multa de 45 UIT por almacenar datos de tarjetas y contraseñas sin hashing criptográfico seguro (bcrypt/Argon2id) (Infracción Grave a la Directiva de Seguridad y al Control Tecnológico de ISO 27701).
* **Caso E-commerce:** Multa de 15 UIT por casillas premarcadas de publicidad (Infracción al Principio de Consentimiento y Control Anexo A de ISO 27701).
* **Caso Salud / Clínicas:** Multa de 70 UIT por fuga de diagnósticos médicos por WhatsApp (Infracción Muy Grave por tratamiento de Datos Sensibles).

---

## 4. Delimitación del Rol a Automatizar: El "Capacitador y Consultor de Brechas"

El docente fue preciso: *"no es TODA la iso, sino solamente un rol, como el rol de CAPACITADOR"*.

* **Por qué NO un Auditor Certificador Externo:** La certificación formal requiere acreditación de una entidad de certificación humana (ej. AENOR, SGS, DNV). Un software no puede firmar un certificado ISO legal.
* **Por qué SÍ el Agente Capacitador y Consultor PIMS:** Es el rol que acompaña a la pequeña empresa:
  1. Realiza el **Gap Analysis inicial** frente a los 78 controles de ISO 27701:2025.
  2. Detecta vulnerabilidades en su base de datos y procesos.
  3. **Capacita con casuística:** Le explica a los dueños y desarrolladores el porqué de cada control usando sanciones reales de la ANPD para crear conciencia del riesgo financiero (multas en UIT).
  4. Entrega planes y código de remediación directa.
