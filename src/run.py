import os
import sys
import threading
import time
import webbrowser
import uvicorn

def abrir_navegador():
    time.sleep(1.5)
    webbrowser.open("http://localhost:8000")

def main():
    print("=" * 75)
    print("SISTEMA MULTI-AGENTE: PRIVACY COACH & DSPM ENGINE (TIF UNSA)")
    print("Normativas: ISO/IEC 27701:2025 | ISO/IEC 29100:2024 | Ley N.° 29733 (Perú)")
    print("Bases de Conocimiento: Grafo NetworkX (78 Controles) + 588 Casos ANPD (UIT)")
    print("Memoria Local: SQLite (empresa_conocimiento.db)")
    print("Modelo LLM: deepseek/deepseek-v4.1-flash (OpenRouter)")
    print("=" * 75)
    print("Servidor web iniciado en: http://localhost:8000")
    print("Abriendo interfaz de usuario en el navegador...")

    threading.Thread(target=abrir_navegador, daemon=True).start()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False, log_level="info")

if __name__ == "__main__":
    main()
