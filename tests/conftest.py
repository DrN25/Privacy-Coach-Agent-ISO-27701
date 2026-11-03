import os
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Cada proceso de pytest tiene su propia base y no hereda servicios reales.
TEST_DIRECTORY = TemporaryDirectory(prefix="privacy-coach-test-")
TEST_DATABASE = Path(TEST_DIRECTORY.name) / "test.db"

# La aplicación copia la base local si el destino no existe o está vacío.
# Crear una base SQLite válida impide importar datos ajenos a las pruebas.
with closing(sqlite3.connect(TEST_DATABASE)) as connection:
    connection.execute("PRAGMA user_version = 1")

os.environ["DATABASE_PATH"] = str(TEST_DATABASE)
os.environ["ENVIRONMENT"] = "development"
os.environ["APP_USERNAME"] = "test-user"
os.environ["APP_PASSWORD"] = "test-password"
os.environ["PG_ENABLED"] = "false"
os.environ["UNSA_A2A_ENABLED"] = "false"
os.environ["OPENROUTER_API_KEY"] = "test-key"
