import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
os.environ["DATABASE_PATH"] = str(PROJECT_ROOT / ".pytest_cache" / "privacy-coach-test.db")
os.environ["OPENROUTER_API_KEY"] = "test-key"
