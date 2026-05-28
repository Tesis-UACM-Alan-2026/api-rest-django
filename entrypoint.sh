#!/bin/sh
set -e

python manage.py check

python manage.py collectstatic --noinput

gunicorn HIMFG.wsgi:application --bind 0.0.0.0:8001