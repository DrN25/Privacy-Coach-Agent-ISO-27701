"""
Servicio Unificado de Procesamiento e Ingesta Documental con OCR y AST.
Soporta PDF nativos y escaneados (PyMuPDF + RapidOCR), esquemas SQL (sqlglot) y políticas en Markdown/TXT.
Garantiza persistencia unificada en la base de datos institucional sin generar silos de datos.
"""

import os
import re
import hashlib
import logging
from typing import Dict, Any, List, Optional
import pymupdf as fitz
import sqlglot
from sqlglot import exp

from ..core.config import settings
from ..profiler import perfilar_columna
from ..infrastructure.repository import repository

logger = logging.getLogger("pims.document_processor")

# Lazy-loader para RapidOCR
_rapidocr_engine = None


def get_ocr_engine():
    global _rapidocr_engine
    if _rapidocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapidocr_engine = RapidOCR()
            logger.info("RapidOCR inicializado correctamente.")
        except Exception as e:
            logger.warning(f"RapidOCR no disponible ({e}), se utilizará extracción nativa PyMuPDF.")
            _rapidocr_engine = False
    return _rapidocr_engine if _rapidocr_engine is not False else None


class DocumentProcessor:
    """Procesador documental centralizado para auditorías de privacidad y brechas PII."""

    def __init__(self, repo=repository):
        self.repo = repo

    @staticmethod
    def calcular_hash_sha256(ruta_archivo: str) -> str:
        sha256 = hashlib.sha256()
        with open(ruta_archivo, "rb") as f:
            for bloque in iter(lambda: f.read(65536), b""):
                sha256.update(bloque)
        return sha256.hexdigest()

    def procesar_archivo(self, ruta_archivo: str, nombre_original: Optional[str] = None) -> Dict[str, Any]:
        """Detecta tipo de archivo y lo procesa integralmente."""
        nombre = nombre_original or os.path.basename(ruta_archivo)
        ext = os.path.splitext(nombre)[1].lower()

        if ext == ".pdf":
            return self.procesar_pdf(ruta_archivo, nombre)
        elif ext == ".sql":
            return self.procesar_sql(ruta_archivo, nombre)
        elif ext in (".md", ".txt"):
            return self.procesar_texto_politica(ruta_archivo, nombre)
        else:
            raise ValueError(f"Extensión no soportada: {ext}. Formatos permitidos: .pdf, .sql, .md, .txt")

    def procesar_pdf(self, ruta_archivo: str, nombre_archivo: str) -> Dict[str, Any]:
        """Extrae texto de PDF con PyMuPDF y aplica RapidOCR si detecta páginas escaneadas."""
        doc = fitz.open(ruta_archivo)
        num_paginas = len(doc)
        texto_completo = []
        paginas_ocr = 0
        ocr_engine = get_ocr_engine()

        for idx, page in enumerate(doc):
            texto_pagina = page.get_text() or ""
            # Si la página tiene menos de 40 caracteres y hay motor OCR, aplicamos OCR
            if len(texto_pagina.strip()) < 40 and ocr_engine:
                try:
                    pix = page.get_pixmap(dpi=200)
                    img_bytes = pix.tobytes("png")
                    result, _ = ocr_engine(img_bytes)
                    if result:
                        texto_ocr = " ".join([line[1] for line in result])
                        texto_pagina = f"\n[OCR Pag {idx+1}]\n{texto_ocr}"
                        paginas_ocr += 1
                except Exception as ex:
                    logger.warning(f"Fallo OCR en pag {idx+1}: {ex}")

            texto_completo.append(texto_pagina)
        doc.close()

        contenido_total = "\n".join(texto_completo)
        tamano = os.path.getsize(ruta_archivo)
        sha256 = self.calcular_hash_sha256(ruta_archivo)

        # Segmentación en cláusulas / artículos
        clausulas = self._segmentar_clausulas_texto(contenido_total, nombre_archivo)

        # Registro en el repositorio unificado
        resumen = f"PDF analizado ({num_paginas} págs, {paginas_ocr} con OCR, {len(clausulas)} cláusulas)"
        archivo_id = self.repo.registrar_archivo(
            nombre=nombre_archivo,
            tipo="PDF",
            tamano=tamano,
            resumen=resumen
        )

        for c in clausulas:
            c["archivo_id"] = archivo_id
            self.repo.registrar_clausula(c)

        return {
            "archivo_id": archivo_id,
            "nombre": nombre_archivo,
            "tipo": "PDF",
            "tamano": tamano,
            "sha256": sha256,
            "num_paginas": num_paginas,
            "paginas_ocr": paginas_ocr,
            "total_clausulas": len(clausulas),
            "clausulas": clausulas
        }

    def procesar_sql(self, ruta_archivo: str, nombre_archivo: str) -> Dict[str, Any]:
        """Parsea esquema SQL DDL con sqlglot y detecta tablas y columnas sensibles."""
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()

        tamano = os.path.getsize(ruta_archivo)
        sha256 = self.calcular_hash_sha256(ruta_archivo)

        archivo_id = self.repo.registrar_archivo(
            nombre=nombre_archivo,
            tipo="SQL",
            tamano=tamano,
            resumen="Esquema SQL DDL parseado mediante AST sqlglot"
        )

        columnas_detectadas = []
        try:
            parsed = sqlglot.parse(contenido)
            for statement in parsed:
                if isinstance(statement, exp.Create):
                    tabla_expr = statement.find(exp.Table)
                    nombre_tabla = tabla_expr.name if tabla_expr else "tabla_desconocida"
                    for col_def in statement.find_all(exp.ColumnDef):
                        nombre_col = col_def.name
                        tipo_col = col_def.kind.sql() if col_def.kind else "VARCHAR"
                        columnas_detectadas.append((nombre_tabla, nombre_col, tipo_col))
        except Exception:
            # Fallback regex
            tables = re.findall(r"CREATE TABLE (?:IF NOT EXISTS )?(\w+)\s*\((.*?)\);", contenido, re.DOTALL | re.IGNORECASE)
            for tname, body in tables:
                for line in body.split(",\n"):
                    line = line.strip()
                    if line and not line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "CONSTRAINT", "CHECK", "UNIQUE")):
                        parts = line.split()
                        if len(parts) >= 2:
                            columnas_detectadas.append((tname, parts[0], parts[1]))

        activos_registrados = []
        for tname, cname, ctype in columnas_detectadas:
            perfil = perfilar_columna(cname, tname, ctype)
            activo_data = {
                "archivo_id": archivo_id,
                "nombre_tabla": perfil.nombre_tabla,
                "nombre_columna": perfil.nombre_columna,
                "tipo_sql": perfil.tipo_sql,
                "categoria_sensible": perfil.categoria.value,
                "es_dato_sensible": perfil.es_sensible,
                "nivel_confianza": perfil.nivel_confianza,
                "candado_deteccion": perfil.candado,
                "recomendacion_seguridad": perfil.recomendacion
            }
            self.repo.registrar_activo_columna(activo_data)
            activos_registrados.append(activo_data)

        return {
            "archivo_id": archivo_id,
            "nombre": nombre_archivo,
            "tipo": "SQL",
            "tamano": tamano,
            "sha256": sha256,
            "total_columnas": len(columnas_detectadas),
            "activos_sensibles": [a for a in activos_registrados if a["es_dato_sensible"]]
        }

    def procesar_texto_politica(self, ruta_archivo: str, nombre_archivo: str) -> Dict[str, Any]:
        """Procesa archivos Markdown o TXT de políticas institucionales y contratos."""
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()

        tamano = os.path.getsize(ruta_archivo)
        sha256 = self.calcular_hash_sha256(ruta_archivo)
        tipo = "MARKDOWN" if nombre_archivo.lower().endswith(".md") else "TXT"

        archivo_id = self.repo.registrar_archivo(
            nombre=nombre_archivo,
            tipo=tipo,
            tamano=tamano,
            resumen="Documento de política institucional segmentado en cláusulas"
        )

        clausulas = self._segmentar_clausulas_texto(contenido, nombre_archivo)
        for c in clausulas:
            c["archivo_id"] = archivo_id
            self.repo.registrar_clausula(c)

        return {
            "archivo_id": archivo_id,
            "nombre": nombre_archivo,
            "tipo": tipo,
            "tamano": tamano,
            "sha256": sha256,
            "total_clausulas": len(clausulas),
            "clausulas": clausulas
        }

    def _segmentar_clausulas_texto(self, contenido: str, documento: str) -> List[Dict[str, Any]]:
        """Segmenta un texto plano en cláusulas y evalúa patrones de no conformidad."""
        lineas = contenido.split("\n")
        clausula_actual = None
        texto_acumulado = []
        resultado = []

        patron_encabezado = re.compile(
            r"^(?:##|###)?\s*(?:CLÁUSULA|SECCIÓN|ARTÍCULO|ART\.|PROCEDIMIENTO|[0-9]+\.)\s*([0-9A-Za-z\s]+)[:\-]?(.*)",
            re.IGNORECASE
        )

        for line in lineas:
            match = patron_encabezado.match(line.strip())
            if match:
                if clausula_actual and texto_acumulado:
                    resultado.append(self._construir_objeto_clausula(documento, clausula_actual, " ".join(texto_acumulado)))
                clausula_actual = match.group(0).strip()
                texto_acumulado = [match.group(2).strip()] if match.group(2) else []
            else:
                if line.strip():
                    texto_acumulado.append(line.strip())

        if clausula_actual and texto_acumulado:
            resultado.append(self._construir_objeto_clausula(documento, clausula_actual, " ".join(texto_acumulado)))

        # Si el texto no tiene encabezados clásicos, segmentar por párrafos
        if not resultado and contenido.strip():
            parrafos = [p.strip() for p in contenido.split("\n\n") if len(p.strip()) > 30]
            for idx, p in enumerate(parrafos, 1):
                resultado.append(self._construir_objeto_clausula(documento, f"Sección {idx}", p))

        return resultado

    def _construir_objeto_clausula(self, documento: str, titulo: str, texto: str) -> Dict[str, Any]:
        estado = "CONFORME"
        alerta = None
        txt_upper = f"{titulo} {texto}".upper()

        patrones_observables = [
            "TÁCITA", "TACITA", "AUTOMÁTICA", "AUTOMATICA", "SE PRESUME",
            "INDEFINIDO", "PERPETUO", "TIEMPO ILIMITADO", "SIN PLAZO DE PURGA",
            "TRANSFRONTERIZ", "EXTRANJERO", "FUERA DEL PERÚ", "FUERA DEL PAIS", "FUERA DEL PAÍS",
            "NOTARIAL", "PRESENCIAL", "TASA", "ARANCEL", "COSTO DE TRÁMITE", "COBRO", "PAGO PREVIO",
            "CVV", "TARJETA DE CRÉDITO"
        ]

        if any(w in txt_upper for w in patrones_observables):
            estado = "OBSERVADO"
            alerta = "Posible vulnerabilidad detectada frente a ISO 27701 y Ley 29733"

        return {
            "documento": documento,
            "numero_clausula": titulo[:30],
            "titulo_clausula": titulo[:100],
            "texto_clausula": texto,
            "tipo_clausula": "CONTRACTUAL",
            "estado_cumplimiento": estado,
            "alerta_legal": alerta
        }


document_processor = DocumentProcessor()
