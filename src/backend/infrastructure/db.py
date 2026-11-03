"""
Gestor de Conexión a Base de Datos Híbrido (PostgreSQL unsa_pims_db con Fallback SQLite).
Garantiza conexión a la base de datos institucional de la UNSA y continuidad operativa offline.
"""

import os
import sqlite3
import logging
from typing import Optional, Any

from ..core.config import Settings
from ..db import DB_PATH, DEFAULT_DB_PATH

logger = logging.getLogger("pims.db")
settings = Settings()

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    psycopg2 = None
    RealDictCursor = None
    PSYCOPG2_AVAILABLE = False


def check_postgres_alive() -> bool:
    """Comprueba si el servidor PostgreSQL institucional está disponible y accesible."""
    if not PSYCOPG2_AVAILABLE or not settings.pg_enabled:
        return False
    try:
        conn = psycopg2.connect(
            host=settings.pg_host,
            port=settings.pg_port,
            dbname=settings.pg_database,
            user=settings.pg_user,
            password=settings.pg_password,
            connect_timeout=2
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        conn.close()
        return True
    except Exception as e:
        logger.debug(f"PostgreSQL unsa_pims_db no alcanzable ({e}). Usando fallback SQLite.")
        return False


def get_postgres_connection():
    """Retorna una conexión activa a la base de datos PostgreSQL institucional (esquema demo)."""
    if not PSYCOPG2_AVAILABLE:
        raise RuntimeError("Driver psycopg2 no está disponible en el entorno.")
    
    conn = psycopg2.connect(
        host=settings.pg_host,
        port=settings.pg_port,
        dbname=settings.pg_database,
        user=settings.pg_user,
        password=settings.pg_password,
        options=f"-c search_path={settings.pg_schema},public"
    )
    return conn


def get_sqlite_connection():
    """Retorna conexión a SQLite local (modo respaldo/desarrollo offline)."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_connection():
    """Retorna conexión PostgreSQL si está disponible; de lo contrario retorna SQLite."""
    if check_postgres_alive():
        return get_postgres_connection()
    return get_sqlite_connection()


def init_db():
    """Inicializa la estructura de respaldo SQLite si se opera en modo local."""
    from ..db import init_db as _init_sqlite_db
    _init_sqlite_db()


__all__ = [
    "get_db_connection",
    "get_postgres_connection",
    "get_sqlite_connection",
    "check_postgres_alive",
    "init_db",
    "DB_PATH",
    "DEFAULT_DB_PATH",
    "RealDictCursor"
]
