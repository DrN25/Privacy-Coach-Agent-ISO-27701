"""
Servicio de Exportación de Dictámenes y Reportes Periciales.
Genera informes consolidados en Markdown conforme a ISO/IEC 27701 y Ley 29733.
"""

from datetime import datetime
from typing import Dict, Any, List

from ..infrastructure.repository import repository


class ExportService:
    def __init__(self, repo=repository):
        self.repo = repo

    def generar_reporte_consolidado_markdown(self) -> str:
        data = self.repo.obtener_vista_completa_base_datos()
        hallazgos = data["hallazgos"]
        archivos = data["archivos"]

        total_uit = sum(h.get("multa_estimada_uit", 0.0) for h in hallazgos)
        total_pen = sum(h.get("multa_estimada_pen", 0.0) for h in hallazgos)

        lineas = [
            "# INFORME TÉCNICO PERICIAL DE AUDITORÍA DE PRIVACIDAD",
            "## Cumplimiento ISO/IEC 27701:2025, ISO 29100 y Ley Peruana N.° 29733",
            f"**Fecha de Emisión:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Total de Hallazgos Críticos/Altos:** {len(hallazgos)}  ",
            f"**Riesgo Sancionador Consolidado:** {total_uit:.1f} UIT (S/ {total_pen:,.2f})  ",
            "\n---\n",
            "### 1. ALCANCE DE LOS ACTIVOS AUDITADOS",
            f"- Archivos analizados: {len(archivos)}",
            f"- Columnas en inventario: {len(data['inventario'])}",
            f"- Cláusulas contractuales: {len(data['clausulas'])}",
            "\n### 2. MATRIZ DE HALLAZGOS Y GRADUACIÓN DE SANCIONES\n",
            "| Código | Hallazgo | Elemento Afectado | Control ISO 27701 | Ley 29733 | Multa UIT | Multa Soles | Estado |",
            "|---|---|---|---|---|---|---|---|"
        ]

        for h in hallazgos:
            lineas.append(
                f"| **{h['codigo_regla']}** | {h['titulo']} | `{h['elemento_afectado']}` | {h['control_iso27701']} | {h['articulo_ley29733'][:25]} | {h['multa_estimada_uit']} UIT | S/ {h['multa_estimada_pen']:,.2f} | {h.get('estado', 'PENDIENTE')} |"
            )

        lineas.extend([
            "\n### 3. PRECEDENTES VINCULANTES DE LA ANPD CITADOS",
            "- Resoluciones Directorales analizadas desde la base de 588 expedientes del MINJUSDH.",
            "\n### 4. PLAN DE REMEDIACIÓN RECOMENDADO"
        ])

        if hallazgos:
            for idx, h in enumerate(hallazgos, 1):
                lineas.append(
                    f"{idx}. **[{h['codigo_regla']}] {h['titulo']}:** {h['descripcion']} (Control {h['control_iso27701']})"
                )
        else:
            lineas.append("- No se registraron no conformidades activas en el inventario auditado.")

        return "\n".join(lineas)


export_service = ExportService()
