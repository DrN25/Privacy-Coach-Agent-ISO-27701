import os
import sqlite3

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "empresa_conocimiento.db")
DB_PATH = os.path.abspath(os.getenv("DATABASE_PATH", DEFAULT_DB_PATH))

# Autosemilla para entornos contenerizados (VPS / Docker volume)
if DB_PATH != DEFAULT_DB_PATH and os.path.exists(DEFAULT_DB_PATH):
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) == 0:
        import shutil
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        shutil.copy2(DEFAULT_DB_PATH, DB_PATH)

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

    # Migración de esquema: eliminar restricción obsoleta UNIQUE(codigo_regla)
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='hallazgos_dspm'")
    old_schema = cursor.fetchone()
    if old_schema and "UNIQUE" in old_schema[0]:
        cursor.execute("ALTER TABLE hallazgos_dspm RENAME TO _hallazgos_dspm_old")
        cursor.execute("""
        CREATE TABLE hallazgos_dspm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_regla TEXT NOT NULL,
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
        cursor.execute("INSERT INTO hallazgos_dspm SELECT * FROM _hallazgos_dspm_old")
        cursor.execute("DROP TABLE _hallazgos_dspm_old")
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS hallazgos_dspm (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_regla TEXT NOT NULL,
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
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hallazgos_codigo ON hallazgos_dspm(codigo_regla);")

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
