"""
Acceso y conexión a la base de datos SQLite local (Capa de Infraestructura).
"""

from ..db import get_db_connection, init_db, DB_PATH, DEFAULT_DB_PATH

__all__ = ["get_db_connection", "init_db", "DB_PATH", "DEFAULT_DB_PATH"]
