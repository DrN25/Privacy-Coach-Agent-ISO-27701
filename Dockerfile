FROM python:3.13-slim

LABEL org.opencontainers.image.title="privacy-coach"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    ENVIRONMENT=production \
    DATABASE_PATH=/var/data/empresa_conocimiento.db

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app src ./src
COPY --chown=app:app knowledge_base ./knowledge_base

RUN mkdir -p /var/data && chown app:app /var/data

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/api/status', timeout=3)"

CMD ["sh", "-c", "exec uvicorn backend.app:app --app-dir src --host 0.0.0.0 --port ${PORT}"]
