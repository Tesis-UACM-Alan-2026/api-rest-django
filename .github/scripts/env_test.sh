#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

ENV_FILE=".env"

# Crea un archivo .env para test
{
    echo "DJANGO_ENV=development"
    echo "SECRET_KEY='$1'"
    echo "SUPERUSER_EMAIL=user@test.com"
    echo "SUPERUSER_PASSWORD=Passw0rd."
    echo "ACCESS_TOKEN_LIFETIME_MINUTES=60"
    echo "REFRESH_TOKEN_LIFETIME_DAYS=1"
    echo "DEBUG=TRUE"
    echo "DEVELOPMENT_ORIGINS=http://127.0.0.1:8000,http://localhost:8000"
    echo "ALLOWED_HOSTS_DEVELOPMENT_ORIGINS=localhost"
    echo "PRIVATE_KEY_PATH=keys/private.pem"
    echo "PUBLIC_KEY_PATH=keys/public.pem"
    echo "DATABASE_ENGINE=django.db.backends.postgresql"
    echo "DATABASE_NAME=test"
    echo "DATABASE_USER=postgres"
    echo "DATABASE_PASSWORD=12345678"
    echo "DATABASE_HOST=localhost"
    echo "DATABASE_PORT=5432"
} >> "$ENV_FILE"