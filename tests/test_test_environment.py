import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_session_ignores_production_environment_and_local_database(tmp_path):
    external_db = tmp_path / "external.db"
    env = os.environ.copy()
    env.update({
        "DATABASE_PATH": str(external_db),
        "ENVIRONMENT": "production",
        "APP_USERNAME": "production-user",
        "APP_PASSWORD": "production-password",
        "PG_ENABLED": "true",
        "UNSA_A2A_ENABLED": "true",
        "OPENROUTER_API_KEY": "production-key",
    })
    code = """
import os
import runpy
import sqlite3

namespace = runpy.run_path('tests/conftest.py')
from backend.core.config import settings
from backend.db import DB_PATH

assert settings.environment == 'development'
assert settings.app_username == 'test-user'
assert settings.app_password == 'test-password'
assert not settings.pg_enabled
assert not settings.unsa_a2a_enabled
assert settings.openrouter_api_key == 'test-key'
assert DB_PATH == os.environ['DATABASE_PATH']
assert DB_PATH != os.environ['EXTERNAL_DB']
with sqlite3.connect(DB_PATH) as connection:
    assert connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall() == []
"""
    env["EXTERNAL_DB"] = str(external_db)
    subprocess.run([sys.executable, "-c", code], cwd=PROJECT_ROOT, env=env, check=True)
    assert not external_db.exists()
