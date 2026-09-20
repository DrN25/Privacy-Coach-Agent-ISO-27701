# Datasets Normativos y Bases de Conocimiento

Bases de conocimiento estructuradas en JSON utilizadas por el motor DSPM y el Privacy Coach Agent. 

---

## 1. Repositorio de Documentos Fuente en Google Drive

Los documentos oficiales originales (normas ISO y resoluciones de la gaceta oficial) se almacenan en la siguiente carpeta compartida de Google Drive para evitar sobrepeso en el repositorio y respetar los derechos de autor:

> [!NOTE]
> **Carpeta de Descarga:** [Google Drive — Fuentes Normativas Oficiales en PDF](URL_GOOGLE_DRIVE_AQUI)  
> Contiene los 5 archivos originales: la norma ISO/IEC 27701:2025 (PIMS), la Ley N.º 29733, el D.S. 003-2013-JUS, la Directiva de Seguridad R.D. 019-2013-JUS y el registro consolidado de sanciones de la ANPD.

---

## 2. Trazabilidad: De Documentos PDF a Datasets JSON

La siguiente matriz detalla el mapeo exacto entre los archivos PDF fuente, el script ETL de extracción y el dataset JSON resultante consumido por el sistema:

| Documento Fuente (Drive / PDF) | Dataset Estructurado (Repo / JSON) | Script ETL de Ingesta | Función en el Sistema |
|---|---|---|---|
| `01_ISO_IEC_27701_2025_PIMS_Standard.pdf` | `iso27701_2025_graph.json` | `scripts/build_datasets.py` | Grafo dirigido (`networkx`) con los 78 controles de privacidad de ISO/IEC 27701:2025 (31 Responsables, 18 Encargados, 29 Seguridad). |
| `02_Ley_29733_Proteccion_Datos_Personales_Peru.pdf`<br>`03_DS_003_2013_JUS_Reglamento_Ley_29733.pdf` | `ley_29733_articulos.json` | `scripts/build_datasets.py` | Catálogo de artículos, definiciones y obligaciones legales del régimen de privacidad de Perú. |
| `04_Directiva_Seguridad_RD_019_2013_JUS.pdf` | Integrado en reglas DSPM | `src/backend/dspm_engine.py` | Parámetros técnicos de medidas de seguridad (cifrado en reposo, longitud de claves, controles de acceso y almacenamiento de contraseñas). |
| `05_ANPD_Registro_Oficial_Sanciones_Impuestas.pdf` | `anpd_sanciones_dataset.json` | `scripts/parse_advanced_sanctions.py` | 588 resoluciones sancionadoras de la ANPD con cálculo de multas en UIT y tipificación de faltas (Leve, Grave, Muy Grave). |
| Estándar Internacional ISO/IEC 29100:2024 | `iso29100_2024_principles.json` | `scripts/build_datasets.py` | 11 principios universales de protección de datos personales vinculados a cada hallazgo. |

---

## 3. Pipeline de Actualización Normativa

Si la autoridad reguladora (ANPD / MINJUSDH) emite nuevas resoluciones sancionadoras o si se promulga una actualización normativa, el procedimiento de actualización se ejecuta en tres pasos:

```bash
# Paso 1: Colocar el nuevo archivo PDF o gaceta oficial en Material/ (o fuentes_normativas_pdf/)
cp /ruta/al/nuevo_documento.pdf Material/

# Paso 2: Ejecutar el pipeline de extracción ETL correspondiente
python scripts/parse_advanced_sanctions.py   # Si se actualizan sanciones ANPD
python scripts/build_datasets.py            # Si se actualiza el catálogo normativo o controles

# Paso 3: Validar la consistencia del grafo normativo
python scripts/graph_engine.py
```

El servidor web y el Privacy Coach Agent consumen directamente los JSON resultantes sin requerir cambios en el código de backend ni reinicio de base de datos.
