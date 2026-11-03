"""
Lanzador del Servidor PIMS UNSA (Agente 6: Gestor de Incidentes y Brechas).
Asegura resolución automática de rutas tanto desde la raíz como desde subcarpetas.
"""

import os
import sys

# Agregar la raíz del repositorio y 'src' al PYTHONPATH
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")

for path in [BASE_DIR, SRC_DIR]:
    if path not in sys.path:
        sys.path.insert(0, path)

import uvicorn

if __name__ == "__main__":
    print(f"[*] Iniciando Servidor PIMS UNSA en http://127.0.0.1:8000 ...")
    uvicorn.run("src.backend.app:app", host="127.0.0.1", port=8000, reload=True)
