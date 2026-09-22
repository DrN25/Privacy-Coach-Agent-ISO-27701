import os
import sqlite3

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "empresa_conocimiento.db")
DB_PATH = os.path.abspath(os.getenv("DATABASE_PATH", DEFAULT_DB_PATH))

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS archivos_cargados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_archivo TEXT NOT NULL,
        tipo_archivo TEXT NOT NULL,
        fecha_carga TEXT NOT NULL,
        tamano_bytes INTEGER,
        resumen_analisis TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS inventario_activos_datos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        archivo_id INTEGER,
        nombre_tabla TEXT NOT NULL,
        nombre_columna TEXT NOT NULL,
        tipo_sql TEXT NOT NULL,
        es_clave_primaria INTEGER DEFAULT 0,
        es_clave_foranea INTEGER DEFAULT 0,
        categoria_sensible TEXT NOT NULL,
        es_dato_sensible INTEGER DEFAULT 0,
        nivel_confianza REAL DEFAULT 1.0,
        candado_deteccion TEXT,
        recomendacion_seguridad TEXT,
        FOREIGN KEY (archivo_id) REFERENCES archivos_cargados(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clausulas_documentales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        archivo_id INTEGER,
        documento TEXT NOT NULL,
        numero_clausula TEXT,
        titulo_clausula TEXT,
        texto_clausula TEXT NOT NULL,
        tipo_clausula TEXT,
        estado_cumplimiento TEXT DEFAULT 'OBSERVADO',
        alerta_legal TEXT,
        FOREIGN KEY (archivo_id) REFERENCES archivos_cargados(id)
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS hallazgos_dspm (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_regla TEXT NOT NULL UNIQUE,
        titulo TEXT NOT NULL,
        descripcion TEXT NOT NULL,
        nivel_riesgo TEXT NOT NULL,
        elemento_afectado TEXT NOT NULL,
        origen_archivo TEXT NOT NULL,
        control_iso27701 TEXT NOT NULL,
        principio_iso29100 TEXT NOT NULL,
        articulo_ley29733 TEXT NOT NULL,
        directiva_seguridad TEXT NOT NULL,
        multa_estimada_uit REAL NOT NULL,
        multa_estimada_pen REAL NOT NULL,
        precedente_anpd TEXT NOT NULL,
        estado TEXT DEFAULT 'PENDIENTE',
        fecha_deteccion TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interacciones_coach (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hallazgo_id INTEGER,
        timestamp TEXT NOT NULL,
        rol TEXT NOT NULL,
        mensaje TEXT NOT NULL,
        pensamiento_reasoning TEXT,
        parche_sql TEXT,
        FOREIGN KEY (hallazgo_id) REFERENCES hallazgos_dspm(id)
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database schema successfully verified.")
