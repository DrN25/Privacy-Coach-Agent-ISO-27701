"""
Configuración centralizada y tipada del sistema mediante Pydantic Settings.
Carga variables de entorno desde .env de forma segura y validada.
"""

import os
from typing import List
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Carga de variables de entorno explícita en os.environ
load_dotenv()
load_dotenv(".env")
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "empresa_conocimiento.db"
)


class Settings(BaseSettings):
    # Entorno
    environment: str = Field(default="development", alias="ENVIRONMENT")
    app_username: str = Field(default="", alias="APP_USERNAME")
    app_password: str = Field(default="", alias="APP_PASSWORD")

    # Inferencia LLM (100% GPT-6 Luna)
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openrouter_url: str = Field(default="https://openrouter.ai/api/v1/chat/completions", alias="OPENROUTER_URL")
    openrouter_model: str = Field(default="openai/gpt-6-luna", alias="OPENROUTER_MODEL")

    # Base de Datos SQLite (Fallback)
    database_path: str = Field(default=DEFAULT_DB_PATH, alias="DATABASE_PATH")

    # Base de Datos PostgreSQL Institucional (unsa_pims_db)
    pg_host: str = Field(default="localhost", alias="PG_HOST")
    pg_port: int = Field(default=5432, alias="PG_PORT")
    pg_database: str = Field(default="unsa_pims_db", alias="PG_DATABASE")
    pg_user: str = Field(default="postgres", alias="PG_USER")
    pg_password: str = Field(default="", alias="PG_PASSWORD")
    pg_schema: str = Field(default="demo", alias="PG_SCHEMA")
    pg_enabled: bool = Field(default=True, alias="PG_ENABLED")

    # Directorio de Almacenamiento Centralizado de Documentos
    media_dir: str = Field(default=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "media"), alias="MEDIA_DIR")

    # Integración A2A con Agente Normativo Institucional UNSA (unsa-mind)
    unsa_a2a_url: str = Field(default="http://localhost:8001/a2a", alias="UNSA_A2A_URL")
    unsa_a2a_enabled: bool = Field(default=True, alias="UNSA_A2A_ENABLED")
    unsa_a2a_api_key: str = Field(default="", alias="UNSA_A2A_API_KEY")

    # CORS
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    # Configuración de Pydantic Settings
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()


if __name__ == "__main__":
    if settings.openrouter_model != "openai/gpt-6-luna" and not os.getenv("OPENROUTER_MODEL"):
        raise AssertionError("Modelo OpenRouter no configurado")
    if not settings.database_path.endswith(".db"):
        raise AssertionError("La ruta de la base debe terminar en .db")
    print(f"Config loaded successfully: env={settings.environment}, model={settings.openrouter_model}")
