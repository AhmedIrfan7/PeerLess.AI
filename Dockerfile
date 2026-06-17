FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/backend/ .

RUN pip install --no-cache-dir -e "."

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["sh", "-c", "python -m alembic upgrade head && python -m uvicorn peerless.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
