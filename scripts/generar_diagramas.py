"""
Generador de Diagramas del Sistema PIMS UNSA (Agente 6: Gestor de Incidentes y Brechas).
Genera:
  1. Diagrama de Flujo del Grafo Multi-Agente en LangGraph (StateGraph cíclico con reflexión).
  2. Diagrama de Arquitectura en Capas del Sistema Completo.
Utiliza matplotlib.pyplot y exporta imágenes PNG de alta resolución (300 DPI) y gráficos vectoriales.
"""

import os
import shutil
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configuración de estilo global
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'


def generar_diagrama_langgraph(output_path: str):
    """Genera el diagrama de flujo detallado del orquestador multi-agente LangGraph."""
    fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
    fig.patch.set_facecolor('#0f172a')  # Fondo Slate 900
    ax.set_facecolor('#0f172a')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # Título institucional
    ax.text(8, 9.4, "ORQUESTADOR MULTI-AGENTE LANGGRAPH • GESTOR PERICIAL DE BRECHAS PII",
            color='#ffffff', fontsize=15, fontweight='bold', ha='center', va='center')
    ax.text(8, 8.95, "Flujo Cíclico StateGraph con Supervisión, Verificación Forense y Bucle de Reflexión Crítica",
            color='#94a3b8', fontsize=10, ha='center', va='center')

    # Definición de Nodos del Grafo
    nodos = [
        {"id": "START", "label": "START\nInicio", "desc": "Prompt pericial o\nexpediente activo", "x": 1.2, "y": 6.8, "w": 1.6, "h": 1.1, "color": "#1e293b", "border": "#64748b"},
        {"id": "SUPERVISOR", "label": "Supervisor Agent", "desc": "Inicializa expediente\nValida contexto base", "x": 3.7, "y": 6.8, "w": 2.2, "h": 1.25, "color": "#831843", "border": "#f43f5e"},
        {"id": "CONTEXT", "label": "Context Agent", "desc": "Carga metadatos brecha\nActivos y tablas BD", "x": 6.8, "y": 6.8, "w": 2.2, "h": 1.25, "color": "#1e3a8a", "border": "#3b82f6"},
        {"id": "PROFILER", "label": "Data Profiler Agent", "desc": "Clasifica PII y sensibilidad\nReglas regex & columnas", "x": 9.9, "y": 6.8, "w": 2.2, "h": 1.25, "color": "#065f46", "border": "#10b981"},
        {"id": "DSPM", "label": "DSPM Risk Engine", "desc": "Correlación R-001..R-007\nCálculo de multa UIT", "x": 13.0, "y": 6.8, "w": 2.2, "h": 1.25, "color": "#854d0e", "border": "#eab308"},
        
        # Fila inferior
        {"id": "NORMATIVE", "label": "Normative & ANPD", "desc": "ISO 27701 (A.3.X)\nLey 29733 & A2A UNSA", "x": 13.0, "y": 3.4, "w": 2.2, "h": 1.25, "color": "#581c87", "border": "#a855f7"},
        {"id": "COACH", "label": "Forensic Coach\n(GPT-6 Luna)", "desc": "Dictamen pericial forense\nParche SQL y DPA", "x": 9.0, "y": 3.4, "w": 2.4, "h": 1.25, "color": "#991b1b", "border": "#ef4444"},
        {"id": "REFLECTION", "label": "Senior Quality Critic\n(Reflection)", "desc": "Evaluación de rigor\nCálculo de confianza", "x": 5.0, "y": 3.4, "w": 2.4, "h": 1.25, "color": "#0f766e", "border": "#14b8a6"},
        {"id": "END", "label": "END\nDictamen Final", "desc": "Respuesta estructurada\nTrazabilidad multi-agente", "x": 1.2, "y": 3.4, "w": 1.8, "h": 1.1, "color": "#1e293b", "border": "#10b981"}
    ]

    # Dibujar Cajas de Nodos
    for n in nodos:
        box = patches.FancyBboxPatch(
            (n["x"] - n["w"]/2, n["y"] - n["h"]/2), n["w"], n["h"],
            boxstyle="round,pad=0.1,rounding_size=0.15",
            facecolor=n["color"], edgecolor=n["border"], linewidth=2.0
        )
        ax.add_patch(box)
        ax.text(n["x"], n["y"] + 0.15, n["label"], color='#ffffff', fontsize=10, fontweight='bold', ha='center', va='center')
        ax.text(n["x"], n["y"] - 0.28, n["desc"], color='#cbd5e1', fontsize=7.5, ha='center', va='center')

    # Función para flechas rectas
    def arrow(x1, y1, x2, y2, color="#94a3b8", label=""):
        ax.annotate(
            "", xy=(x2, y2), xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", color=color, lw=2.2, mutation_scale=16)
        )
        if label:
            mx, my = (x1 + x2)/2, (y1 + y2)/2
            ax.text(mx, my + 0.18, label, color=color, fontsize=8, fontweight='bold', ha='center', va='center')

    # Conexiones Fila Superior: START -> SUPERVISOR -> CONTEXT -> PROFILER -> DSPM
    arrow(2.0, 6.8, 2.6, 6.8, "#38bdf8")
    arrow(4.8, 6.8, 5.7, 6.8, "#38bdf8")
    arrow(7.9, 6.8, 8.8, 6.8, "#38bdf8")
    arrow(11.0, 6.8, 11.9, 6.8, "#38bdf8")

    # Transición Vertical: DSPM -> NORMATIVE
    arrow(13.0, 6.15, 13.0, 4.05, "#38bdf8")

    # Conexiones Fila Inferior: NORMATIVE -> COACH -> REFLECTION
    arrow(11.9, 3.4, 10.2, 3.4, "#38bdf8")
    arrow(7.8, 3.4, 6.2, 3.4, "#38bdf8")

    # Decisión de Reflexión (Condicional LangGraph)
    # 1. Éxito: REFLECTION -> END
    arrow(3.8, 3.4, 2.1, 3.4, "#22c55e", "Calidad Aprobada\n(Score >= 0.85)")

    # 2. Bucle de Refinamiento: REFLECTION -> COACH (Curvado hacia arriba)
    ax.annotate(
        "", xy=(9.0, 4.05), xytext=(5.0, 4.05),
        arrowprops=dict(arrowstyle="->", color="#f59e0b", lw=2.2, mutation_scale=16,
                        connectionstyle="arc3,rad=-0.42", ls="--")
    )
    ax.text(7.0, 5.1, "Refinamiento Requerido (Score < 0.85) • Loop Pericial",
            color="#fbbf24", fontsize=8.5, fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.2", facecolor='#1e293b', edgecolor='#f59e0b', lw=1.2))

    # Trazabilidad StateGraph (Caja inferior de estado compartido)
    state_box = patches.FancyBboxPatch(
        (1.2, 0.7), 13.6, 1.3,
        boxstyle="round,pad=0.1,rounding_size=0.15",
        facecolor="#1e293b", edgecolor="#475569", linewidth=1.5
    )
    ax.add_patch(state_box)
    ax.text(1.5, 1.6, "ESTADO COMPARTIDO (AuditState TypedDict):", color='#f8fafc', fontsize=9, fontweight='bold')
    state_items = (
        "• contexto_brecha: Dict (sistema, elemento, activo, evidencia)   "
        "• trazabilidad: List[Dict] (nodos ejecutados, tiempos, status)\n"
        "• clasificacion_pii: List[Dict] (sensibilidad LPDP, candados)   "
        "• regla_canonica: Dict (R-001..R-007, ISO 27701, Ley 29733, UIT)\n"
        "• dictamen_forense: Dict (nexo causal, fundamentación pericial)   "
        "• parche_remediacion: Dict (script SQL transaccional, cláusula DPA)"
    )
    ax.text(1.5, 1.15, state_items, color='#94a3b8', fontsize=8, va='center', linespacing=1.4)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[OK] Diagrama LangGraph generado en: {output_path}")


def generar_diagrama_arquitectura(output_path: str):
    """Genera el diagrama formal de arquitectura en 5 capas del sistema integral PIMS UNSA."""
    fig, ax = plt.subplots(figsize=(16, 12), dpi=300)
    fig.patch.set_facecolor('#0f172a')  # Fondo Slate 900
    ax.set_facecolor('#0f172a')
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.axis('off')

    # Título
    ax.text(8, 11.4, "ARQUITECTURA INTEGRAL DEL SISTEMA PIMS & GESTOR DE BRECHAS UNSA",
            color='#ffffff', fontsize=15, fontweight='bold', ha='center', va='center')
    ax.text(8, 11.0, "Capa Pericial Multi-Agente • ISO/IEC 27701:2025 • Ley N° 29733 • Precedentes ANPD",
            color='#94a3b8', fontsize=10, ha='center', va='center')

    # 5 Capas Principales
    capas = [
        {
            "num": "CAPA 1", "nombre": "PRESENTACIÓN & EXPERIENCIA PERICIAL (FRONTEND SPA)",
            "y": 9.1, "h": 1.5, "color": "#1e293b", "border": "#38bdf8",
            "modulos": [
                ("Gestor de Cédulas & Nexo", "Visualizador de Brechas,\nCuantías UIT y Precedentes"),
                ("Repositorio de Custodia (21)", "Previsualización PDF y\nAnalizador de Esquemas DDL"),
                ("Consultor DPO (Sidebar)", "Chatbot Pericial, Citas Normativas\ny Visor de Flujo de Nodos"),
                ("Temas Sillar Claro", "Lacre Cardenal UNSA,\nCobalto Pericial, Terracota")
            ]
        },
        {
            "num": "CAPA 2", "nombre": "EXPOSICIÓN API GATEWAY & ENRUTAMIENTO (FASTAPI)",
            "y": 7.2, "h": 1.4, "color": "#1e293b", "border": "#818cf8",
            "modulos": [
                ("Middlewares de Seguridad", "Basic Auth Producción,\nCORS Dinámico, No-Cache"),
                ("/api/incidents", "Expedientes periciales,\nestado y cédulas jurídicas"),
                ("/api/chat & /api/audit", "Orquestación pericial,\nconsultas y parches SQL"),
                ("/api/files & /api/legal-reference", "PyMuPDF, RapidOCR y\ncorpus ISO/Ley 29733")
            ]
        },
        {
            "num": "CAPA 3", "nombre": "INTELIGENCIA & ORQUESTADOR MULTI-AGENTE (LANGGRAPH)",
            "y": 5.2, "h": 1.5, "color": "#1e293b", "border": "#ec4899",
            "modulos": [
                ("Supervisor & Context", "Planificación de nodos y\ncarga de contexto brecha"),
                ("Profiler & DSPM Engine", "Detección PII sensible y\ncorrelación R-001..R-007"),
                ("Forensic Coach & A2A", "GPT-6 Luna (OpenRouter) y\nprotocolo A2A UNSA"),
                ("Critic / Reflection", "Validación determinista,\nconsistencia y loop pericial")
            ]
        },
        {
            "num": "CAPA 4", "nombre": "DOMINIO PERICIAL, REGLAS & INGESTIÓN MULTIDIMENSIONAL",
            "y": 3.2, "h": 1.4, "color": "#1e293b", "border": "#34d399",
            "modulos": [
                ("Catálogo Canónico (7 Reglas)", "ISO 27701 (A.3.X), Ley 29733,\nISO 29100 y escalas UIT"),
                ("Analizador AST SQL", "Parsing con SQLGlot,\ndetección DDL/DML riesgoso"),
                ("Procesador Documental", "PyMuPDF para PDFs nativos,\nRapidOCR para escaneados"),
                ("Grafo de Conocimiento", "NetworkX: relaciones PIMS,\ncláusulas y controles")
            ]
        },
        {
            "num": "CAPA 5", "nombre": "INFRAESTRUCTURA & PERSISTENCIA HÍBRIDA (RESILIENTE)",
            "y": 1.1, "h": 1.5, "color": "#1e293b", "border": "#f59e0b",
            "modulos": [
                ("PostgreSQL Institucional", "Base de datos unsa_pims_db\n(Servidor de producción UNSA)"),
                ("Fallback SQLite Local", "empresa_conocimiento.db\nAutosemilla en VPS/Docker"),
                ("Almacén Documental", "fuentes_normativas_pdf/\ny media/ en disco local"),
                ("Despliegue Contenerizado", "Docker, docker-compose.prod,\nHealthchecks y CI/CD Actions")
            ]
        }
    ]

    for c in capas:
        # Contenedor de la Capa
        box = patches.FancyBboxPatch(
            (0.8, c["y"]), 14.4, c["h"],
            boxstyle="round,pad=0.08,rounding_size=0.12",
            facecolor=c["color"], edgecolor=c["border"], linewidth=1.8
        )
        ax.add_patch(box)

        # Encabezado de la Capa
        header_text = f"{c['num']} • {c['nombre']}"
        ax.text(1.1, c["y"] + c["h"] - 0.22, header_text, color=c["border"], fontsize=9.5, fontweight='bold')

        # Submódulos internos en 4 columnas
        col_w = 3.3
        col_gap = 0.25
        sub_y = c["y"] + 0.15
        sub_h = c["h"] - 0.45

        for idx, (m_title, m_desc) in enumerate(c["modulos"]):
            sub_x = 1.1 + idx * (col_w + col_gap)
            sub_box = patches.FancyBboxPatch(
                (sub_x, sub_y), col_w, sub_h,
                boxstyle="round,pad=0.05,rounding_size=0.08",
                facecolor="#0f172a", edgecolor="#334155", linewidth=1.2
            )
            ax.add_patch(sub_box)
            ax.text(sub_x + col_w/2, sub_y + sub_h - 0.25, m_title, color='#ffffff', fontsize=8.5, fontweight='bold', ha='center')
            ax.text(sub_x + col_w/2, sub_y + sub_h/2 - 0.12, m_desc, color='#94a3b8', fontsize=7.2, ha='center', va='center')

    # Flechas de conexión bidireccional entre capas
    def conn_layer(y_top, y_bottom):
        ax.annotate(
            "", xy=(8.0, y_bottom), xytext=(8.0, y_top),
            arrowprops=dict(arrowstyle="<->", color="#64748b", lw=2.0, mutation_scale=14)
        )

    conn_layer(9.1, 8.6)
    conn_layer(7.2, 6.7)
    conn_layer(5.2, 4.6)
    conn_layer(3.2, 2.6)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[OK] Diagrama de Arquitectura generado en: {output_path}")


if __name__ == "__main__":
    os.makedirs("docs/img", exist_ok=True)
    langgraph_img = os.path.join("docs", "img", "diagrama_flujo_agentes_langgraph.png")
    arch_img = os.path.join("docs", "img", "diagrama_arquitectura_sistema.png")

    generar_diagrama_langgraph(langgraph_img)
    generar_diagrama_arquitectura(arch_img)

    # Copiar también al directorio de artefactos si existe
    artifact_dir = r"C:\Users\Rafael\.gemini\antigravity\brain\55a387ad-f9c4-4493-8385-6f4184d13b30"
    if os.path.exists(artifact_dir):
        shutil.copy2(langgraph_img, os.path.join(artifact_dir, "diagrama_flujo_agentes_langgraph.png"))
        shutil.copy2(arch_img, os.path.join(artifact_dir, "diagrama_arquitectura_sistema.png"))
        print(f"[OK] Diagramas copiados a la carpeta de artefactos: {artifact_dir}")

