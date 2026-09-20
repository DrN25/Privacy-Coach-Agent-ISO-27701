# Datasets Normativos y Bases de Conocimiento

Este directorio almacena los grafos de conocimiento y datasets estructurados utilizados por el motor DSPM y el Privacy Coach Agent.

---

## Contenido

| Archivo | Formato | Registros / Nodos | Descripción |
|---|---|---|---|
| `iso27701_2025_graph.json` | JSON Graph | 78 nodos, 78 aristas | Grafo estructurado de los 78 controles de la norma **ISO/IEC 27701:2025** (31 Controles de Responsables - Anexo A, 18 Controles de Encargados - Anexo B y 29 Controles de Seguridad Aplicada). |
| `anpd_sanciones_dataset.json` | JSON Dataset | 588 resoluciones | Precedentes sancionadores de la **Autoridad Nacional de Protección de Datos Personales (ANPD / MINJUSDH)**, con tipificación de infracciones y cálculo de multas en UIT. |
| `iso29100_2024_principles.json` | JSON Dataset | 11 principios | Marco de principios de privacidad de la norma **ISO/IEC 29100:2024**. |
| `ley_29733_articulos.json` | JSON Dataset | 45 artículos | Régimen normativo de la **Ley N.° 29733** y el reglamento **D.S. 016-2024-JUS**. |

---

## Nota sobre Documentos Fuente (PDF)

Los documentos PDF oficiales (normas ISO y gacetas legales del diario oficial El Peruano) se mantienen excluidos del control de versiones (`.gitignore`) para evitar sobrepeso en el repositorio y respetar los derechos de autor de las normas internacionales. El sistema opera al 100% en tiempo de ejecución utilizando exclusivamente las bases de conocimiento estructuradas en JSON.
