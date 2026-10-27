"""
Patrón Repositorio (Repository Pattern) para persistencia SQLite.
Encapsula todas las operaciones SQL desacoplando la capa de servicios y API.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import sqlite3

from .db import get_db_connection


class AuditRepository:
    def __init__(self, connection_factory=get_db_connection):
        self.get_conn = connection_factory

    def resetear_base_de_datos(self) -> None:
        """Limpia todas las tablas del sistema."""
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM interacciones_coach")
        cur.execute("DELETE FROM hallazgos_dspm")
        cur.execute("DELETE FROM clausulas_documentales")
        cur.execute("DELETE FROM inventario_activos_datos")
        cur.execute("DELETE FROM archivos_cargados")
        conn.commit()
        conn.close()

    def obtener_estadisticas_globales(self) -> Dict[str, int]:
        """Retorna conteos de archivos, inventario y hallazgos."""
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM archivos_cargados")
        num_archivos = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) as cnt FROM inventario_activos_datos")
        num_activos = cur.fetchone()["cnt"]
        cur.execute("SELECT COUNT(*) as cnt FROM hallazgos_dspm")
        num_hallazgos = cur.fetchone()["cnt"]
        conn.close()
        return {
            "num_archivos": num_archivos,
            "num_activos": num_activos,
            "num_hallazgos": num_hallazgos
        }

    def registrar_archivo(
        self, nombre: str, tipo: str, tamano: int, resumen: Optional[str] = None
    ) -> int:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO archivos_cargados (nombre_archivo, tipo_archivo, fecha_carga, tamano_bytes, resumen_analisis)
            VALUES (?, ?, ?, ?, ?)
            """,
            (nombre, tipo, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), tamano, resumen or "")
        )
        conn.commit()
        file_id = cur.lastrowid
        conn.close()
        return file_id

    def registrar_activo_columna(self, activo: Dict[str, Any]) -> int:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO inventario_activos_datos (
                archivo_id, nombre_tabla, nombre_columna, tipo_sql,
                es_clave_primaria, es_clave_foranea, categoria_sensible,
                es_dato_sensible, nivel_confianza, candado_deteccion, recomendacion_seguridad
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                activo.get("archivo_id"),
                activo["nombre_tabla"],
                activo["nombre_columna"],
                activo["tipo_sql"],
                1 if activo.get("es_clave_primaria") else 0,
                1 if activo.get("es_clave_foranea") else 0,
                activo.get("categoria_sensible", "NO_SENSIBLE"),
                1 if activo.get("es_dato_sensible") else 0,
                activo.get("nivel_confianza", 1.0),
                activo.get("candado_deteccion"),
                activo.get("recomendacion_seguridad")
            )
        )
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return last_id

    def registrar_clausula(self, clausula: Dict[str, Any]) -> int:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO clausulas_documentales (
                archivo_id, documento, numero_clausula, titulo_clausula,
                texto_clausula, tipo_clausula, estado_cumplimiento, alerta_legal
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clausula.get("archivo_id"),
                clausula["documento"],
                clausula.get("numero_clausula"),
                clausula.get("titulo_clausula"),
                clausula["texto_clausula"],
                clausula.get("tipo_clausula"),
                clausula.get("estado_cumplimiento", "OBSERVADO"),
                clausula.get("alerta_legal")
            )
        )
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return last_id

    def limpiar_hallazgos(self) -> None:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM hallazgos_dspm")
        conn.commit()
        conn.close()

    def insertar_hallazgo(self, hallazgo: Dict[str, Any]) -> int:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO hallazgos_dspm (
                codigo_regla, titulo, descripcion, nivel_riesgo, elemento_afectado, origen_archivo,
                control_iso27701, principio_iso29100, articulo_ley29733, directiva_seguridad,
                multa_estimada_uit, multa_estimada_pen, precedente_anpd, fecha_deteccion, estado
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hallazgo["codigo_regla"],
                hallazgo["titulo"],
                hallazgo["descripcion"],
                hallazgo["nivel_riesgo"],
                hallazgo["elemento_afectado"],
                hallazgo["origen_archivo"],
                hallazgo["control_iso27701"],
                hallazgo["principio_iso29100"],
                hallazgo["articulo_ley29733"],
                hallazgo["directiva_seguridad"],
                hallazgo["multa_estimada_uit"],
                hallazgo["multa_estimada_pen"],
                hallazgo["precedente_anpd"],
                hallazgo.get("fecha_deteccion", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                hallazgo.get("estado", "PENDIENTE")
            )
        )
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return last_id

    def obtener_todos_los_hallazgos(self) -> List[Dict[str, Any]]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM hallazgos_dspm ORDER BY multa_estimada_uit DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def obtener_hallazgo_por_id(self, hallazgo_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM hallazgos_dspm WHERE id = ?", (hallazgo_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def obtener_vista_completa_base_datos(self) -> Dict[str, List[Dict[str, Any]]]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM archivos_cargados ORDER BY id DESC")
        archivos = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM inventario_activos_datos ORDER BY id ASC")
        inventario = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM clausulas_documentales ORDER BY id ASC")
        clausulas = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM hallazgos_dspm ORDER BY multa_estimada_uit DESC")
        hallazgos = [dict(r) for r in cur.fetchall()]
        conn.close()
        return {
            "archivos": archivos,
            "inventario": inventario,
            "clausulas": clausulas,
            "hallazgos": hallazgos
        }

    def guardar_interaccion_coach(
        self, hallazgo_id: int, rol: str, mensaje: str, reasoning: Optional[str] = None, parche: Optional[str] = None
    ) -> int:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO interacciones_coach (hallazgo_id, timestamp, rol, mensaje, pensamiento_reasoning, parche_sql)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (hallazgo_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rol, mensaje, reasoning or "", parche or "")
        )
        conn.commit()
        last_id = cur.lastrowid
        conn.close()
        return last_id

    def obtener_interacciones_por_hallazgo(self, hallazgo_id: int) -> List[Dict[str, Any]]:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM interacciones_coach WHERE hallazgo_id = ? ORDER BY id ASC", (hallazgo_id,))
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def actualizar_estado_hallazgo(self, hallazgo_id: int, nuevo_estado: str) -> bool:
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE hallazgos_dspm SET estado = ? WHERE id = ?", (nuevo_estado, hallazgo_id))
        conn.commit()
        affected = cur.rowcount
        conn.close()
        return affected > 0


repository = AuditRepository()
