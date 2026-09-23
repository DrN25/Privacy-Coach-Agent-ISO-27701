# Privacy-Coach-Agent-ISO-27701

> Motor DSPM y auditoría automatizada de privacidad. Alineado a ISO/IEC 27701:2025 y Ley Peruana N.º 29733 (ANPD).

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek%20Flash-4E75F6.svg?style=for-the-badge)](https://openrouter.ai/)
[![MCP](https://img.shields.io/badge/Protocol-MCP-purple.svg?style=for-the-badge)](https://modelcontextprotocol.io/)

---

## Qué hace

Audita bases de datos y contratos contra la normativa peruana de protección de datos personales. Detecta brechas de privacidad, calcula la exposición económica en UIT y genera scripts SQL de remediación.

**Componentes:**

| Componente | Función |
|---|---|
| Motor DSPM | Analiza esquemas SQL (DDL via `sqlglot`) y contratos/SLA (PDF/TXT via `PyMuPDF`). Detecta datos sensibles sin cifrar, hashes débiles, CVV almacenados, consentimiento tácito, retención indefinida, flujos transfronterizos sin registro y trabas ARCO. |
| Knowledge Bridge | Grafo dirigido (`networkx`) con 78 controles ISO/IEC 27701:2025, principios ISO/IEC 29100 y 588 precedentes sancionadores de la ANPD. Comprime +150k tokens de documentación regulatoria a ~850 tokens de contexto. |
| Privacy Coach Agent | Agente pericial (`deepseek/deepseek-v4.1-flash` via OpenRouter). Emite dictámenes técnicos con fundamentación legal, cálculo de multas y parches SQL listos para producción. |
| Servidor MCP | 10 herramientas expuestas via Model Context Protocol para integración con IDEs y agentes externos. |

---

## Arquitectura

```mermaid
flowchart TD
    subgraph INGESTA["1. Ingesta"]
        A1["Esquemas SQL (.sql)"] --> B1["AST Parser (sqlglot)"]
        A2["Contratos / SLAs (.pdf, .md, .txt)"] --> B2["Extractor (PyMuPDF)"]
    end

    subgraph DSPM["2. Motor DSPM"]
        B1 --> C1["Clasificador de Columnas (Ley 29733)"]
        B2 --> C2["Evaluador de Cláusulas"]
        C1 --> D1["Motor de Reglas (R-001 a R-007)"]
        C2 --> D1
        D1 --> E1["Inventario (SQLite)"]
        D1 --> E2["Hallazgos de No Conformidad"]
    end

    subgraph KNOWLEDGE["3. Knowledge Bridge"]
        KB1[("ISO/IEC 27701:2025\n78 Controles")] --> F1["Subgrafo Normativo"]
        KB2[("Dataset ANPD Perú\n588 Resoluciones")] --> F1
        E2 --> F1
        F1 --> G1["Payload (~850 tokens)"]
    end

    subgraph AGENT["4. Privacy Coach Agent"]
        G1 --> H1["OpenRouter"]
        H1 --> H2["DeepSeek v4.1 Flash"]
        H2 --> I1["Dictamen en Markdown"]
        H2 --> I2["Parche SQL de Remediación"]
    end

    subgraph UI["5. Interfaz"]
        I1 --> J1["Dashboard React 18"]
        I2 --> J1
        E1 --> J1
        E2 --> J1
        J2["Servidor MCP (10 Tools)"] -.->|IDE / Agentes| E1
    end
```

---

## Estructura del Repositorio

```text
Privacy-Coach-Agent-ISO-27701/
├ .env.example              # Plantilla de variables de entorno
├ .env.production.example   # Plantilla de secretos para la VPS
├ .github/workflows/        # CI y despliegue automatizado por SSH
├ .gitignore
├ docker-compose.prod.yml   # Build y ejecución productiva en VPS
├ Dockerfile                # Imagen de la API y frontend
├ requirements.txt
├ README.md
│
├ docs/                     # Documentación técnica y académica (TIF UNSA)
│   ├ README.md              # Índice temático de los 9 documentos
│   └ ...
│
├ knowledge_base/           # Dominio normativo estructurado (ISO 27701 y Ley 29733)
│   ├ README.md              # Enlace a Google Drive (fuentes PDF) y matriz de trazabilidad
│   ├ datasets/              # Grafos y datasets JSON procesados
│   │   ├ iso27701_2025_graph.json
│   │   ├ anpd_sanciones_dataset.json
│   │   ├ iso29100_2024_principles.json
│   │   └ ley_29733_articulos.json
│   └ pipelines/             # Pipelines ETL de extracción y compilación
│       ├ build_datasets.py
│       └ parse_advanced_sanctions.py
│
└ src/                      # Código fuente de la aplicación
    ├ backend/
    │   ├ app.py             # API REST FastAPI
    │   ├ coach_agent.py     # Privacy Coach Agent (DeepSeek)
    │   ├ db.py              # Esquema SQLite
    │   ├ dspm_engine.py     # Motor de reglas deterministas
    │   ├ graph_engine.py    # Motor de consulta GraphRAG (NetworkX)
    │   ├ ingestion.py       # Parser DDL y contratos
    │   ├ knowledge_bridge.py# Puente semántico normativo
    │   ├ profiler.py        # Clasificador de columnas
    │   └ router.py          # Enrutador normativo
    ├ data/                  # Almacén SQLite local
    ├ frontend/
    │   ├ index.html         # Shell HTML y Tailwind
    │   ├ css/style.css      # Estilos y tema oscuro
    │   ├ js/app.jsx         # Dashboard interactivo React 18
    │   └ js/marked.min.js   # Parser Markdown local
    ├ mockups/               # Caso de prueba: Clínica SaludTotal
    ├ mcp_server.py          # Servidor Model Context Protocol (10 tools)
    └ run.py                 # Punto de entrada unificado
```

---

## Instalación

### Requisitos
- Python 3.10+
- API key de [OpenRouter](https://openrouter.ai/)

### Pasos

```bash
git clone https://github.com/TU_USUARIO/Privacy-Coach-Agent-ISO-27701.git
cd Privacy-Coach-Agent-ISO-27701

python -m venv .venv
# Windows:
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Editar .env con tu API key de OpenRouter

python src/run.py
```

El servidor inicia en `http://127.0.0.1:8000`.

### Docker

```bash
docker build -t privacy-coach:local .
docker volume create privacy-coach-data
docker run --rm -p 8000:8000 \
  --env-file .env \
  -e DATABASE_PATH=/var/data/empresa_conocimiento.db \
  -v privacy-coach-data:/var/data \
  privacy-coach:local
```

Comprobar el contenedor:

```bash
curl --fail http://127.0.0.1:8000/api/status
```

---

## CI/CD y VPS

El pipeline de `.github/workflows/ci.yml` ejecuta compilación, Ruff, Pytest, `pip-audit`, Bandit y el build de la imagen Docker. Las pruebas usan SQLite temporal y simulan el Coach, por lo que no consumen créditos de OpenRouter.

Después de un CI exitoso sobre `main`, el mismo workflow comprime el código, lo copia por SCP y ejecuta `docker compose build/up` dentro de la VPS. No usa registry ni publica imágenes.

- FastAPI en `127.0.0.1:8000`, accesible solo desde la propia VPS.
- SQLite en un volumen Docker persistente.
- Contenedores con reinicio automático, health checks y logs rotados.
- Aplicación con filesystem de solo lectura y directorios temporales limitados.
- Una sola imagen local `privacy-coach:local`; imágenes anteriores no usadas se eliminan.

### Preparación de la VPS

Requisitos: Docker Engine, plugin Docker Compose y usuario SSH con acceso a Docker. Un Nginx/Caddy externo puede publicar `127.0.0.1:8000`; también puede accederse mediante túnel SSH sin exponer puertos adicionales.

```bash
mkdir -p ~/privacy-coach
cd ~/privacy-coach
# Crear este archivo desde la plantilla del repositorio:
nano .env.production
chmod 600 .env.production
```

Contenido basado en `.env.production.example`. `APP_PASSWORD`, `OPENROUTER_API_KEY` y `CORS_ORIGINS` deben tener valores reales. No copiar este archivo al repositorio.

### Secretos de GitHub Actions

Crear en **Settings > Secrets and variables > Actions**:

| Secreto | Valor |
|---|---|
| `VPS_HOST` | IP o hostname SSH de la VPS |
| `VPS_PORT` | Puerto SSH, normalmente `22` |
| `VPS_USER` | Usuario con permiso para ejecutar Docker |
| `VPS_SSH_KEY` | Clave privada SSH dedicada al despliegue |
| `VPS_KNOWN_HOSTS` | Clave pública de host SSH verificada de la VPS |

La llave pública correspondiente a `VPS_SSH_KEY` debe estar en `~/.ssh/authorized_keys` del usuario remoto. Se recomienda proteger el environment de GitHub `production` con aprobación manual.

### Flujo

Cada push a `main` sigue `CI -> SCP -> docker compose build/up -> health check`. Los secretos permanecen solo en `.env.production` dentro de la VPS. Docker conserva únicamente la imagen local en ejecución; las anteriores se eliminan tras un despliegue exitoso.

Acceso interno desde una computadora:

```bash
ssh -L 8000:127.0.0.1:8000 usuario@IP_VPS
# Abrir http://127.0.0.1:8000
```

En producción, toda la interfaz y API usan HTTP Basic con `APP_USERNAME` y `APP_PASSWORD`. Solo `/api/status` permanece público para health checks. SQLite es apropiado para una sola instancia; para escalado horizontal debe reemplazarse por PostgreSQL.

Comandos de verificación local equivalentes a CI:

```bash
pip install -r requirements-dev.txt
python -m compileall -q src knowledge_base tests
ruff check src knowledge_base tests
pytest
pip-audit -r requirements.txt
bandit -q -r src -x tests
docker build -t privacy-coach:ci .
```

---

## Servidor MCP

`src/mcp_server.py` expone 10 herramientas via Model Context Protocol:

| Herramienta | Descripción |
|---|---|
| `dspm_get_status` | Estado de la base de datos y conteo de activos. |
| `dspm_audit_repository` | Auditoría completa sobre esquemas y contratos cargados. |
| `dspm_classify_column` | Clasifica un campo SQL bajo categorías de la Ley 29733. |
| `graphrag_query_normative` | Consulta el subgrafo ISO 27701 / ISO 29100 / Ley 29733. |
| `anpd_search_sanctions` | Busca en 588 resoluciones sancionadoras de la ANPD. |
| `coach_consult` | Dictamen técnico con parche SQL via DeepSeek Flash. |
| `dspm_apply_remediation` | Aplica parches SQL o marca hallazgos como subsanados. |
| `dspm_load_demo_case` | Carga el caso de prueba de Clínica SaludTotal. |
| `dspm_reset_repository` | Reinicia el repositorio a estado cero. |
| `dspm_ingest_file` | Carga nuevos esquemas SQL o contratos. |

### Configuración MCP

```json
{
  "mcpServers": {
    "privacy-dspm": {
      "command": "python",
      "args": ["-X", "utf8", "C:/ruta/a/Privacy-Coach-Agent-ISO-27701/src/mcp_server.py"]
    }
  }
}
```

---

## Créditos

- **Universidad Nacional de San Agustín de Arequipa (UNSA)**
- Escuela Profesional de Ingeniería de Sistemas
- Auditoría de Sistemas — Trabajo de Investigación Formativa (TIF), Semestre 2026-B

## Licencia

MIT. Ver archivo `LICENSE`.
