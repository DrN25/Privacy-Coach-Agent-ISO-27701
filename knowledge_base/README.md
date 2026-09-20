# Base de Conocimiento Normativa (Knowledge Base)

> Modelado estructurado en JSON de normativas de privacidad (ISO/IEC 27701:2025, ISO/IEC 29100 y Ley N.º 29733 de Perú) y pipelines de compilación ETL.

---

## 1. Repositorio Oficial en Google Drive (Fuentes PDF)

Los documentos PDF oficiales originales se mantienen centralizados en la siguiente carpeta compartida de Google Drive para evitar sobrepeso en el repositorio y proteger derechos de autor:

> [!NOTE]
> **Carpeta Oficial de Descarga:** [Google Drive — Fuentes Normativas Oficiales en PDF](https://drive.google.com/drive/folders/1q0zBogAUrXz6BFjq2PVYrD-xitxXIpfe?usp=sharing)  
> Contiene los 5 archivos base: la norma ISO/IEC 27701:2025 (PIMS), la Ley N.º 29733, el D.S. 003-2013-JUS, la Directiva de Seguridad R.D. 019-2013-JUS y el registro consolidado de sanciones de la ANPD.

---

## 2. Matriz de Trazabilidad: De PDF Fuente a Dataset JSON

| Documento Fuente (Drive / PDF) | Dataset Estructurado (`datasets/`) | Pipeline ETL (`pipelines/`) | Función en el Sistema |
|---|---|---|---|
| `01_ISO_IEC_27701_2025_PIMS_Standard.pdf` | `iso27701_2025_graph.json` | `build_datasets.py` | Grafo de 78 controles de privacidad ISO/IEC 27701:2025 (31 Responsables, 18 Encargados, 29 Seguridad). |
| `02_Ley_29733_Proteccion_Datos_Personales_Peru.pdf`<br>`03_DS_003_2013_JUS_Reglamento_Ley_29733.pdf` | `ley_29733_articulos.json` | `build_datasets.py` | Catálogo de artículos y obligaciones legales del régimen de privacidad de Perú. |
| `04_Directiva_Seguridad_RD_019_2013_JUS.pdf` | Integrado en reglas DSPM | `src/backend/dspm_engine.py` | Parámetros técnicos de medidas de seguridad (cifrado en reposo, longitud de claves y control de acceso). |
| `05_ANPD_Registro_Oficial_Sanciones_Impuestas.pdf` | `anpd_sanciones_dataset.json` | `parse_advanced_sanctions.py` | 588 resoluciones sancionadoras de la ANPD con cálculo de multas en UIT y tipificación de faltas. |
| Estándar Internacional ISO/IEC 29100:2024 | `iso29100_2024_principles.json` | `build_datasets.py` | 11 principios universales de protección de datos personales vinculados a cada hallazgo. |

---

## 3. Pipeline de Actualización Normativa

Si la autoridad reguladora (ANPD / MINJUSDH) emite nuevas resoluciones sancionadoras o se publica una actualización normativa:

```bash
# 1. Colocar el nuevo archivo PDF en fuentes_normativas_pdf/
cp /ruta/al/nuevo_documento.pdf fuentes_normativas_pdf/

# 2. Ejecutar el pipeline de extracción ETL correspondiente
python knowledge_base/pipelines/parse_advanced_sanctions.py   # Para nuevas sanciones ANPD
python knowledge_base/pipelines/build_datasets.py            # Para nuevos controles o artículos

# 3. La aplicación en src/backend/graph_engine.py asimila automáticamente los JSON actualizados
```
