#!/bin/bash

python manage.py collectstatic --noinput
python manage.py migrate --noinput
gunicorn web.core.wsgi:application --bind 0.0.0.0:8000 --log-level warning