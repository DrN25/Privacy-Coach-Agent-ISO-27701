"""
Aplicación Principal FastAPI (Capa de Presentación / API).
Configura middlewares, autenticación básica de producción, CORS, routers y frontend estático.
"""

import os
import base64
import binascii
import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from ..core.config import settings
from ..infrastructure.db import init_db
from .routers.audit import router as audit_router
from .routers.files import router as files_router
from .routers.coach import router as coach_router
from .routers.normative import router as normative_router
from .routers.incidents import router as incidents_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.is_production:
        if not settings.app_username or not settings.app_password:
            raise RuntimeError("APP_USERNAME y APP_PASSWORD son obligatorios en producción")
    init_db()
    yield


app = FastAPI(
    title="Privacy & DSPM Multi-Agent System",
    description="Sistema Multi-Agente de Auditoría de Privacidad (ISO 27701, ISO 29100, Ley 29733) con LangGraph y GPT-6 Luna",
    version="3.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def production_basic_auth(request, call_next):
    env = os.getenv("ENVIRONMENT", settings.environment)
    if env.lower() != "production" or request.url.path == "/api/status":
        return await call_next(request)

    authorization = request.headers.get("Authorization", "")
    try:
        scheme, encoded = authorization.split(" ", 1)
        username, password = base64.b64decode(encoded).decode("utf-8").split(":", 1)
    except (ValueError, UnicodeDecodeError, binascii.Error):
        scheme, username, password = "", "", ""

    expected_user = os.getenv("APP_USERNAME", settings.app_username)
    expected_password = os.getenv("APP_PASSWORD", settings.app_password)
    valid_user = secrets.compare_digest(username, expected_user)
    valid_password = secrets.compare_digest(password, expected_password)
    if scheme.lower() != "basic" or not (valid_user and valid_password):
        return JSONResponse(
            status_code=401,
            content={"detail": "Autenticación requerida"},
            headers={"WWW-Authenticate": 'Basic realm="Privacy Coach"'},
        )
    return await call_next(request)


@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    if not settings.is_production:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.exception_handler(OSError)
async def os_error_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": "Ruta inválida en sistema operativo"})


# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_origins_list != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusión de routers
app.include_router(audit_router)
app.include_router(files_router)
app.include_router(coach_router)
app.include_router(normative_router)
app.include_router(incidents_router)

# Montaje de Frontend estático (React 18)
base_backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dir = os.path.join(os.path.dirname(base_backend), "frontend")
if not os.path.exists(frontend_dir):
    frontend_dir = os.path.join(base_backend, "..", "frontend")

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
