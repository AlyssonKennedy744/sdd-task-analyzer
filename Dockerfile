# Imagem de execução isolada do TaskAnalyzer (Fase 3).
# Base leve e imutável exigida pela spec: python:3.11-slim.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependências primeiro, para aproveitar o cache de camadas.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/
COPY tests/ tests/

# Execução sem privilégios de root.
RUN useradd --create-home --uid 1000 analyzer && chown -R analyzer:analyzer /app
USER analyzer

CMD ["pytest", "tests/test_harness.py", "-v"]
