FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY dev-requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip

RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --no-cache-dir --wheel-dir /wheels -r dev-requirements.txt

COPY . .

FROM python:3.12-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dev-requirements.txt .
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /app/dev-requirements.txt \
    && rm -rf /wheels

COPY --from=builder /app /app 

RUN adduser --disabled-password --gecos '' appuser \
    && mkdir -p /app/staticfiles/ \
    && chown -R appuser:appuser /app \
    && chmod +x /app/entrypoint.sh

#USER appuser

EXPOSE 8001

ENTRYPOINT [ "/app/entrypoint.sh" ]