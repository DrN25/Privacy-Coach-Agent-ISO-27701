# CONTRATO DE PRESTACIÓN DE SERVICIOS EN LA NUBE Y ENCARGO DE TRATAMIENTO (DPA / SLA)

**Conste por el presente documento el Acuerdo de Nivel de Servicio (SLA) y Encargo de Datos suscrito entre:**
* **EL CLIENTE (Responsable del Tratamiento):** SALUDTOTAL S.A.C., con RUC 20608945123, debidamente representada por su Gerente General.
* **EL PROVEEDOR (Encargado del Tratamiento):** CLOUDSERVICES LATAM LLC, empresa constituida bajo las leyes de Delaware, EE.UU., proveedora de infraestructura informática en la nube.

---

### CLÁUSULA PRIMERA: OBJETO DEL SERVICIO
EL PROVEEDOR brindará a EL CLIENTE el servicio de hosting y base de datos gestionada (PostgreSQL Managed Instance) para el almacenamiento operativo del sistema de historias clínicas y citas de EL CLIENTE.

### CLÁUSULA SEGUNDA: LOCALIZACIÓN DE LA INFRAESTRUCTURA (VULNERABILIDAD R-006)
Los datos personales y sensibles de EL CLIENTE serán almacenados en el Centro de Datos del PROVEEDOR ubicado en el estado de Virginia, Estados Unidos (Región US-East-1).
*Nota de Cumplimiento:* Las partes declaran que no se requerirá inscripción previa de este flujo transfronterizo ante la Autoridad Nacional de Protección de Datos Personales (ANPD) del Perú, por considerarse una operación técnica rutinaria.

### CLÁUSULA TERCERA: MEDIDAS DE SEGURIDAD (VULNERABILIDAD R-001)
EL PROVEEDOR garantiza la seguridad perimetral de la máquina virtual mediante firewall TCP/IP estándar. Sin embargo:
1. EL PROVEEDOR **no implementará cifrado en reposo (encryption at rest)** sobre los campos de historias clínicas o diagnósticos, siendo dicha configuración de exclusiva responsabilidad opcional de EL CLIENTE.
2. EL PROVEEDOR no mantendrá registros de auditoría (logs) de los accesos de lectura a las tablas de pacientes por razones de optimización de disco.

### CLÁUSULA CUARTA: NOTIFICACIÓN DE BRECHAS DE SEGURIDAD
En caso de fuga masiva, intrusión no autorizada o secuestro de datos (ransomware), EL PROVEEDOR notificará a EL CLIENTE dentro de los **sesenta (60) días calendario posteriores a la confirmación técnica del incidente**, deslindando toda responsabilidad indemnizatoria directa frente a los titulares de los datos.

### CLÁUSULA QUINTA: SUB-CONTRATACIÓN
EL PROVEEDOR queda facultado para subcontratar con terceros proveedores en cualquier país del mundo el soporte y análisis de telemetría de los servidores, sin necesidad de recabar aprobación previa de EL CLIENTE.
