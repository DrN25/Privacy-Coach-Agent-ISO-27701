"""
Servicio de Ingesta y Procesamiento de Archivos (SQL DDL y Documentos Legales/PDF).
Capa de Aplicación / Servicios que orquesta parseo AST, segmentación de cláusulas y perfilado.
"""

import os
import re
from typing import Optional
import pymupdf as fitz
import sqlglot
from sqlglot import exp

from ..infrastructure.repository import repository
from ..profiler import perfilar_columna


class IngestionService:
    def __init__(self, repo=repository):
        self.repo = repo

    def procesar_sql(self, ruta_archivo: str, nombre_archivo: str) -> int:
        """Parsea archivo SQL DDL mediante AST sqlglot y perfila columnas sensibles."""
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            contenido = f.read()

        tamano = len(contenido.encode("utf-8"))
        archivo_id = self.repo.registrar_archivo(
            nombre=nombre_archivo,
            tipo="SQL",
            tamano=tamano,
            resumen="Esquema SQL DDL analizado mediante AST sqlglot"
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

        # Perfilar y persistir cada columna
        for tname, cname, ctype in columnas_detectadas:
            perfil = perfilar_columna(cname, tname, ctype)
            self.repo.registrar_activo_columna({
                "archivo_id": archivo_id,
                "nombre_tabla": perfil.nombre_tabla,
                "nombre_columna": perfil.nombre_columna,
                "tipo_sql": perfil.tipo_sql,
                "categoria_sensible": perfil.categoria.value,
                "es_dato_sensible": perfil.es_sensible,
                "nivel_confianza": perfil.nivel_confianza,
                "candado_deteccion": perfil.candado,
                "recomendacion_seguridad": perfil.recomendacion
            })

        return archivo_id

    def procesar_documento(self, ruta_archivo: str, nombre_archivo: str) -> int:
        """Parsea PDF o Markdown y extrae cláusulas contractuales."""
        tipo = "PDF" if nombre_archivo.lower().endswith(".pdf") else "MARKDOWN"
        contenido = ""

        if tipo == "PDF":
            doc = fitz.open(ruta_archivo)
            for page in doc:
                contenido += page.get_text() + "\n"
            doc.close()
        else:
            with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.read()

        tamano = len(contenido.encode("utf-8"))
        archivo_id = self.repo.registrar_archivo(
            nombre=nombre_archivo,
            tipo=tipo,
            tamano=tamano,
            resumen="Documento normativo/contractual analizado y segmentado en cláusulas"
        )

        lineas = contenido.split("\n")
        clausula_actual = None
        texto_acumulado = []

        for line in lineas:
            match = re.match(
                r"^(?:##|###)?\s*(?:CLÁUSULA|SECCIÓN|[0-9]+\.)\s*([0-9A-Za-z\s]+)[:\-]?(.*)",
                line.strip(),
                re.IGNORECASE
            )
            if match:
                if clausula_actual and texto_acumulado:
                    self._guardar_clausula(archivo_id, nombre_archivo, clausula_actual, " ".join(texto_acumulado))
                clausula_actual = match.group(0).strip()
                texto_acumulado = [match.group(2).strip()] if match.group(2) else []
            else:
                if line.strip():
                    texto_acumulado.append(line.strip())

        if clausula_actual and texto_acumulado:
            self._guardar_clausula(archivo_id, nombre_archivo, clausula_actual, " ".join(texto_acumulado))

        return archivo_id

    def _guardar_clausula(self, archivo_id: int, documento: str, titulo: str, texto: str):
        estado = "CONFORME"
        alerta = None
        txt_upper = f"{titulo} {texto}".upper()
        patrones_observables = [
            "TÁCITA", "TACITA", "AUTOMÁTICA", "AUTOMATICA", "SE PRESUME",
            "INDEFINIDO", "PERPETUO", "TIEMPO ILIMITADO", "SIN PLAZO DE PURGA",
            "TRANSFRONTERIZ", "EXTRANJERO", "FUERA DEL PERÚ", "FUERA DEL PAIS", "FUERA DEL PAÍS",
            "NOTARIAL", "PRESENCIAL", "TASA", "ARANCEL", "COSTO DE TRÁMITE", "COBRO", "PAGO PREVIO"
        ]
        if any(w in txt_upper for w in patrones_observables):
            estado = "OBSERVADO"
            alerta = "Posible vulnerabilidad detectada frente a la Ley 29733 e ISO 27701"

        self.repo.registrar_clausula({
            "archivo_id": archivo_id,
            "documento": documento,
            "numero_clausula": titulo[:30],
            "titulo_clausula": titulo[:100],
            "texto_clausula": texto,
            "tipo_clausula": "CONTRACTUAL",
            "estado_cumplimiento": estado,
            "alerta_legal": alerta
        })


ingestion_service = IngestionService()


# Funciones de conveniencia compatibles
def procesar_archivo_sql(ruta_archivo: str, nombre_archivo: str) -> int:
    return ingestion_service.procesar_sql(ruta_archivo, nombre_archivo)


def procesar_archivo_documento(ruta_archivo: str, nombre_archivo: str) -> int:
    return ingestion_service.procesar_documento(ruta_archivo, nombre_archivo)
