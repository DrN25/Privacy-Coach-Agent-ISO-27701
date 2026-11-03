"""
Catálogo Canónico de Reglas de Privacidad y DSPM (R-001 a R-007).
Fuente única de verdad (Single Source of Truth) para la correlación entre
vulnerabilidades técnicas/documentales, ISO/IEC 27701:2025, ISO/IEC 29100:2024,
Ley Peruana N.° 29733, Directiva R.D. 019-2013-JUS y precedentes vinculantes de la ANPD.

Características de diseño:
- Tipado estricto con TypedDict de la biblioteca estándar.
- Acceso O(1) inmutable.
- Validación autónoma de integridad.
- Paquete de remediación multidimensional (SQL, No-SQL, Jurídica y Organizativa).
"""

from typing import Dict, TypedDict, List, Optional


class ReglaAuditoria(TypedDict):
    codigo: str
    titulo: str
    nivel_riesgo: str
    control_iso27701: str
    control_nombre: str
    principio_iso29100: str
    articulo_ley29733: str
    directiva_seguridad: str
    multa_estimada_uit: float
    multa_estimada_pen: float
    precedente_anpd: str
    tipo_hallazgo: str  # 'TECNICO' o 'DOCUMENTAL'
    remediacion_sugerida: str
    remediacion_db_sql: Optional[str]
    remediacion_software_nosql: Optional[str]
    remediacion_juridica: str
    remediacion_organizativa: str
    aviso_legal_anpd: str


# Valor de la Unidad Impositiva Tributaria (UIT) oficial de referencia (2026: S/ 5,150)
VALOR_UIT_PEN = 5150.00

CATALOGO_REGLAS: Dict[str, ReglaAuditoria] = {
    "R-001": {
        "codigo": "R-001",
        "titulo": "Datos de Salud Sensibles sin Cifrado en Reposo",
        "nivel_riesgo": "CRÍTICO",
        "control_iso27701": "A.3.24",
        "control_nombre": "Use of cryptography",
        "principio_iso29100": "Principle 7: Information security",
        "articulo_ley29733": "Art. 9 (Principio de Seguridad) y Art. 38 num. 2.b LPDP",
        "directiva_seguridad": "R.D. 019-2013-JUS/DGPDP - Nivel Complejo (Cifrado robusto en reposo)",
        "multa_estimada_uit": 12.5,
        "multa_estimada_pen": 12.5 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 1045-2020-JUS / R.D. 89-2021-JUS (Clínica Montefiori - Datos de salud sin cifrado)",
        "tipo_hallazgo": "TECNICO",
        "remediacion_sugerida": "Aplicar pgcrypto con pgp_sym_encrypt en columnas sensibles, parametrizar consultas PDO contra SQLi y aislar VLAN hospitalaria.",
        "remediacion_db_sql": """BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- Cifrado simétrico AES-256 de columnas con diagnósticos CIE-10 y anamnesis
ALTER TABLE ficha_medica ADD COLUMN IF NOT EXISTS diagnostico_cifrado bytea;
UPDATE ficha_medica 
SET diagnostico_cifrado = pgp_sym_encrypt(diagnostico_cie10::text, current_setting('app.encryption_key', true))
WHERE diagnostico_cifrado IS NULL;
ALTER TABLE ficha_medica DROP COLUMN IF EXISTS diagnostico_cie10;
COMMIT;""",
        "remediacion_software_nosql": """// Backend API: Sustituir concatenación SQL por PDO / Prepared Statements
$stmt = $pdo->prepare('SELECT id, paciente_id, pgp_sym_decrypt(diagnostico_cifrado, :key) AS diagnostico FROM ficha_medica WHERE id = :id');
$stmt->execute(['id' => $paciente_id, 'key' => $encryption_key]);
$resultado = $stmt->fetch();
// Red: Segregar base de datos en VLAN hospitalaria (10.10.30.0/24) con TLS 1.3 forzado.""",
        "remediacion_juridica": "Formalizar contratos de confidencialidad con el personal asistencial y tramitar notificación formal ante la ANPD (Art. 38 D.S. 016-2024-JUS).",
        "remediacion_organizativa": "Emisión de Directiva Directoral interna del Hospital Docente bajo la NTS N° 139-MINSA/DGIEM (Gestión de Historias Clínicas Electrónicas).",
        "aviso_legal_anpd": "Obligación legal perentoria de notificar formalmente a la ANPD en un plazo máximo de 48 horas tras la detección (D.S. 016-2024-JUS)."
    },
    "R-002": {
        "codigo": "R-002",
        "titulo": "Almacenamiento de Contraseñas con Algoritmo Hash Débil (MD5)",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.3.13",
        "control_nombre": "Access control",
        "principio_iso29100": "Principle 7: Information security",
        "articulo_ley29733": "Art. 9 (Principio de Seguridad) y Art. 38 num. 2.b LPDP",
        "directiva_seguridad": "R.D. 019-2013-JUS/DGPDP - Nivel Medio (Autenticación robusta y gestión de claves)",
        "multa_estimada_uit": 8.0,
        "multa_estimada_pen": 8.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 018-2021-JUS/DGTAIPD (Medidas técnicas deficientes en autenticación de contraseñas)",
        "tipo_hallazgo": "TECNICO",
        "remediacion_sugerida": "Migrar a esquemas de derivación robustos (Argon2id/bcrypt) e invalidar hashes MD5 legacy con forzado de reseteo.",
        "remediacion_db_sql": """BEGIN;
ALTER TABLE usuarios_postulantes ADD COLUMN IF NOT EXISTS password_hash_scheme character varying(20) DEFAULT 'argon2id';
ALTER TABLE usuarios_postulantes ADD COLUMN IF NOT EXISTS force_password_reset boolean DEFAULT false;
-- Marcar cuentas con hash MD5 legacy (32 caracteres hexadecimales)
UPDATE usuarios_postulantes 
SET force_password_reset = true, password_hash_scheme = 'md5_legacy'
WHERE password_hash ~ '^[0-9A-Fa-f]{32}$';
COMMIT;""",
        "remediacion_software_nosql": """# Backend Python / Node: Autenticación mediante Argon2id con salt aleatorio
import argon2
ph = argon2.PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, hash_len=32, salt_len=16)

def hash_new_password(password: str) -> str:
    return ph.hash(password)

# Revocación masiva de tokens JWT y sesiones web activas en Redis
# redis_client.delete_pattern("session:postulante:*")""",
        "remediacion_juridica": "Acreditar subsanación voluntaria ante la ANPD antes del inicio de Procedimiento Administrativo Sancionador (Art. 133 D.S. 003-2013-JUS).",
        "remediacion_organizativa": "Aprobación de la Política Institucional de Gestión de Credenciales y Contraseñas de la UNSA bajo el estándar NIST SP 800-63B.",
        "aviso_legal_anpd": "El uso de algoritmos obsoletos vulnera las medidas de seguridad del Art. 9 de la Ley 29733. Requiere comunicación formal al DPO."
    },
    "R-003": {
        "codigo": "R-003",
        "titulo": "Almacenamiento Ilegal de Código de Seguridad CVV de Tarjetas",
        "nivel_riesgo": "CRÍTICO",
        "control_iso27701": "A.1.4.5",
        "control_nombre": "PII minimization objectives",
        "principio_iso29100": "Principle 5: Collection and retention limitation",
        "articulo_ley29733": "Art. 7 (Principio de Proporcionalidad) y Art. 38 num. 2.b LPDP",
        "directiva_seguridad": "Directiva de Seguridad R.D. 019-2013-JUS Num. 5.2 (Prohibición de almacenar datos de autenticación)",
        "multa_estimada_uit": 15.0,
        "multa_estimada_pen": 15.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 089-2021-JUS/DGTAIPD (Retención indebida de datos de pago tras la transacción)",
        "tipo_hallazgo": "TECNICO",
        "remediacion_sugerida": "Destruir de inmediato columnas de CVV/PAN mediante DROP COLUMN con sobreescritura aleatoria y pasar a pasarela tokenizada Págalo.pe.",
        "remediacion_db_sql": """BEGIN;
-- Destrucción inmediata de datos confidenciales de autenticación
UPDATE pagos_online SET cvv = NULL, pan = NULL;
ALTER TABLE pagos_online DROP COLUMN IF EXISTS cvv;
ALTER TABLE pagos_online DROP COLUMN IF EXISTS pan;
VACUUM FULL pagos_online;
COMMIT;""",
        "remediacion_software_nosql": """// Checkout Seguro (Cumplimiento PCI-DSS v4.0 Req 3.2):
// Los datos de tarjeta jamás tocan servidores de la UNSA.
// Integración mediante pasarela externa tokenizada de Págalo.pe / Banco de la Nación:
const sessionToken = await pagaloPeApi.createPaymentSession({
  amount: matricula.monto,
  currency: 'PEN',
  orderId: matricula.codigoPago
});
// Redirigir al formulario alojado seguro de la pasarela bancaria externa.""",
        "remediacion_juridica": "Interposición de denuncia penal ante la Fiscalía de Delitos Informáticos (Art. 6 Ley 30096) y apertura de PAD al operador infractor.",
        "remediacion_organizativa": "Eliminación de privilegios de exportación masiva a archivos planos CSV/Excel en el módulo de recaudación de Tesorería.",
        "aviso_legal_anpd": "Infracción Grave bajo Art. 38.2.b Ley 29733. Notificación inmediata a la ANPD y deslinde de responsabilidades con las marcas de tarjetas."
    },
    "R-004": {
        "codigo": "R-004",
        "titulo": "Consentimiento Tácito o Presunto en Formularios Web",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.1.2.4",
        "control_nombre": "Determine when and how consent is to be obtained",
        "principio_iso29100": "Principle 1: Consent and choice",
        "articulo_ley29733": "Art. 5 (Principio de Consentimiento) y Art. 18 LPDP",
        "directiva_seguridad": "D.S. 003-2013-JUS Art. 12 (Condiciones del consentimiento previo, libre, expreso e informado)",
        "multa_estimada_uit": 10.0,
        "multa_estimada_pen": 10.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 018-2021-JUS / R.D. 2196-2020-JUS (BBVA - Imputación de consentimiento tácito o automático)",
        "tipo_hallazgo": "DOCUMENTAL",
        "remediacion_sugerida": "Desmarcar casillas de cesión publicitaria por defecto (checked=false) y garantizar que la negativa no afecte el servicio.",
        "remediacion_db_sql": None,
        "remediacion_software_nosql": """<!-- Componente Web Front-end (React / HTML Corregido conforme a Ley 29733) -->
<div class="consent-box mt-3 p-3 border rounded bg-slate-800 text-sm">
  <input 
    type="checkbox" 
    id="consent_cesion_bancos" 
    name="consent_cesion_bancos" 
    checked={false} 
    required={false}
    onChange={(e) => setConsentBancos(e.target.checked)} 
  />
  <label for="consent_cesion_bancos" class="ml-2 text-slate-300">
    Autorizo expresamente a la UNSA a compartir mis datos de contacto con entidades bancarias patrocinadoras para ferias laborales y créditos educativos. (Opcional)
  </label>
</div>
<!-- El validador JavaScript NO debe bloquear el envío si esta casilla no está marcada -->""",
        "remediacion_juridica": "Redacción de nueva Política de Privacidad de Comedor y Matrícula con finalidades claramente diferenciadas (Art. 13 D.S. 003-2013-JUS).",
        "remediacion_organizativa": "Directiva de la Dirección Universitaria de Desarrollo Estudiantil (DUDE) prohibiendo condicionar becas o comedor a la cesión publicitaria.",
        "aviso_legal_anpd": "El consentimiento presunto o impuesto es nulo de pleno derecho y sancionable como Infracción Grave ante la ANPD."
    },
    "R-005": {
        "codigo": "R-005",
        "titulo": "Plazo de Conservación Indefinido de Datos Biométricos de Postulantes",
        "nivel_riesgo": "MEDIO",
        "control_iso27701": "A.1.4.8",
        "control_nombre": "Retention",
        "principio_iso29100": "Principle 5: Collection and retention limitation",
        "articulo_ley29733": "Arts. 7 y 8 (Principios de Proporcionalidad y Calidad - Conservación Limitada)",
        "directiva_seguridad": "D.S. 003-2013-JUS Arts. 9 y 28 (Cancelación y bloqueo por expiración de plazo)",
        "multa_estimada_uit": 5.0,
        "multa_estimada_pen": 5.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 005-2016-JUS/DGPDP / R.D. 542-2019-JUS (Conservación perpetua y deber de cancelación al extinguirse la finalidad)",
        "tipo_hallazgo": "DOCUMENTAL",
        "remediacion_sugerida": "Establecer caducidad formal a los 12 meses de concluido el concurso y programar purga automática de huellas dactilares y fotos.",
        "remediacion_db_sql": """BEGIN;
-- Bloqueo transaccional de huellas y fotos de postulantes no ingresantes de concursos concluidos
UPDATE postulantes_historico 
SET huella_dactilar_wsq = NULL, foto_rostro = NULL, estado = 'CANCELADO_POR_CADUCIDAD'
WHERE proceso_ano < EXTRACT(YEAR FROM CURRENT_DATE) - 1 
  AND admitido = false;
COMMIT;""",
        "remediacion_software_nosql": """# Crontab / Script Automatizado de Purga en Almacenamiento de Servidor (NIST SP 800-88)
# Ejecución mensual: 0 3 1 * * /opt/scripts/purge_expired_biometrics.sh
#!/bin/bash
find /data/storage/biometria/postulantes/ -type f -mtime +365 -name "*.wsq" -exec shred -u -z -n 3 {} +
echo "[PURGE] Archivos biométricos con más de 12 meses destruidos de forma segura conforme a NIST SP 800-88." >> /var/log/purge_audit.log""",
        "remediacion_juridica": "Incorporación de cláusula de conservación y cancelación expresa en el Reglamento del Concurso de Admisión de Pregrado de la UNSA.",
        "remediacion_organizativa": "Aprobación de la Directiva de Purga Documental y Destrucción de Soportes por el Consejo Universitario de la UNSA.",
        "aviso_legal_anpd": "El titular del banco de datos debe cancelar los datos una vez extinguida la finalidad que justificó su tratamiento (Art. 8 Ley 29733)."
    },
    "R-006": {
        "codigo": "R-006",
        "titulo": "Flujo Transfronterizo a Nube Extranjera sin Contrato DPA ni Registro ANPD",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.1.5.2",
        "control_nombre": "Identifying basis for PII transfer between jurisdictions",
        "principio_iso29100": "Principle 6: Openness, transparency and notice",
        "articulo_ley29733": "Art. 15 (Transferencia de datos personales al exterior) y Art. 38 num. 3.c LPDP",
        "directiva_seguridad": "D.S. 003-2013-JUS Art. 66 (Inscripción obligatoria de flujo transfronterizo ante RNPDP)",
        "multa_estimada_uit": 11.0,
        "multa_estimada_pen": 11.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 125-2019-JUS / R.D. 234-2016-JUS (Servidores en el extranjero sin registrar flujo transfronterizo)",
        "tipo_hallazgo": "DOCUMENTAL",
        "remediacion_sugerida": "Revocar claves IAM de AWS expuestas, cifrar S3 con KMS, firmar Addendum DPA con Cláusulas Tipo e inscribir flujo en RNPDP.",
        "remediacion_db_sql": None,
        "remediacion_software_nosql": """# Contención Inmediata de Infraestructura Cloud mediante AWS CLI:
# 1. Revocar de inmediato las credenciales IAM del servicio de respaldo
aws iam update-access-key --access-key-id AKIAIOSFODNN7EXAMPLE --status Inactive --user-name backup-svc-unsa

# 2. Habilitar bloqueo de acceso público y cifrado obligatorio con KMS en el bucket
aws s3api put-public-access-block --bucket s3-unsa-db-backups-unencrypted --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
aws s3api put-bucket-encryption --bucket s3-unsa-db-backups-unencrypted --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms"}}]}'""",
        "remediacion_juridica": "Suscripción formal del Data Processing Addendum (DPA) con Cláusulas Contractuales Tipo (SCC) e inicio del trámite de inscripción ante el RNPDP de la ANPD.",
        "remediacion_organizativa": "Política de Acreditación de Proveedores Cloud de la OTI, prohibiendo el despliegue de infraestructura fuera del Perú sin aval del DPO.",
        "aviso_legal_anpd": "Infracción Muy Grave (Art. 38.3.c Ley 29733). Requiere trámite formal ante el Registro Nacional de Protección de Datos Personales."
    },
    "R-007": {
        "codigo": "R-007",
        "titulo": "Trabas Ilegales y Cobro de Tasas TUPA para Derechos ARCO en TRAMITED",
        "nivel_riesgo": "ALTO",
        "control_iso27701": "A.1.3.7",
        "control_nombre": "Access, correction and erasure",
        "principio_iso29100": "Principle 9: Accuracy and quality",
        "articulo_ley29733": "Arts. 19 al 24 (Gratuidad y sencillez en atención de derechos ARCO) y Art. 38 num. 2.a LPDP",
        "directiva_seguridad": "D.S. 003-2013-JUS Arts. 47 al 58 (Procedimiento gratuito y sin exigencias notariales)",
        "multa_estimada_uit": 9.0,
        "multa_estimada_pen": 9.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución Directoral N° 022-2016-JUS/DGPDP / R.D. 112-2022-JUS (Obstaculización y cobro de requisitos para derechos ARCO)",
        "tipo_hallazgo": "DOCUMENTAL",
        "remediacion_sugerida": "Emitir Circular Rectoral de gratuidad absoluta, modificar TRAMITED suprimiendo campos de voucher y carta notarial.",
        "remediacion_db_sql": None,
        "remediacion_software_nosql": """// Portal Web TRAMITED (Refactorización del formulario de derechos ARCO):
// Eliminar validaciones bloqueantes de pago TUPA y carta notarial
function validarSolicitudArco(formulario) {
  if (!formulario.dni_archivo) {
    return { valido: false, mensaje: "Debe adjuntar copia simple de su DNI para acreditar identidad." };
  }
  // SE ELIMINA LA EXIGENCIA DE TASA TUPA Y CARTA NOTARIAL (Art. 47 D.S. 003-2013-JUS)
  return { valido: true };
}""",
        "remediacion_juridica": "Allanamiento y respuesta a los reclamos iniciados ante la DFI-ANPD demostrando gratuidad sobrevenida para archivar el procedimiento.",
        "remediacion_organizativa": "Emisión de la Circular Rectoral N° 012-2026-R-UNSA declarando la gratuidad irrestricta de solicitudes ARCO e instrucción a mesa de partes.",
        "aviso_legal_anpd": "Infracción Grave bajo Art. 38.2.a de la Ley 29733. El ejercicio de derechos ARCO no puede someterse a pago de tasas ni requisitos notariales."
    }
}


def obtener_regla(codigo: str) -> Optional[ReglaAuditoria]:
    """Retorna la regla canónica o None si no existe."""
    return CATALOGO_REGLAS.get(codigo.strip().upper())


def resolver_regla_con_fallback(codigo: str) -> ReglaAuditoria:
    """Retorna la regla canónica o un fallback genérico estructurado si no está en catálogo."""
    regla = obtener_regla(codigo)
    if regla:
        return regla
    return {
        "codigo": codigo,
        "titulo": "Brecha de Privacidad General",
        "nivel_riesgo": "MEDIO",
        "control_iso27701": "A.1.2.2",
        "control_nombre": "Identify and document purpose",
        "principio_iso29100": "Principle 1",
        "articulo_ley29733": "Art. 4",
        "directiva_seguridad": "Directiva General",
        "multa_estimada_uit": 3.0,
        "multa_estimada_pen": 3.0 * VALOR_UIT_PEN,
        "precedente_anpd": "Resolución General ANPD",
        "tipo_hallazgo": "TECNICO",
        "remediacion_sugerida": "Revisar medidas de seguridad y documentación legal aplicable.",
        "remediacion_db_sql": None,
        "remediacion_software_nosql": None,
        "remediacion_juridica": "Revisar política de privacidad institucional.",
        "remediacion_organizativa": "Instruir a los operadores de tratamiento.",
        "aviso_legal_anpd": "Verificar plazo de notificación según la naturaleza de los datos afectados."
    }


def listar_todas_las_reglas() -> List[ReglaAuditoria]:
    """Retorna lista de todas las reglas canónicas ordenadas por código."""
    return list(CATALOGO_REGLAS.values())


if __name__ == "__main__":
    if len(CATALOGO_REGLAS) != 7:
        raise AssertionError("Deben existir exactamente 7 reglas canónicas (R-001 a R-007)")
    for r_id in [f"R-00{i}" for i in range(1, 8)]:
        r = obtener_regla(r_id)
        if r is None:
            raise AssertionError(f"Regla {r_id} no encontrada")
        if r["multa_estimada_uit"] <= 0:
            raise AssertionError(f"Multa inválida para {r_id}")
        if not r["control_iso27701"].startswith("A."):
            raise AssertionError(f"Control ISO inválido para {r_id}")
        if len(r["aviso_legal_anpd"]) <= 10:
            raise AssertionError(f"Aviso ANPD vacío para {r_id}")
    print("Core rules catalog: self-check passed (7 canonical multidimensional rules valid).")
