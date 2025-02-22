FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE 'web.core.settings'

WORKDIR /app

COPY ./pyproject.toml pyproject.toml
RUN mkdir -p /app/web/static/ && \
    mkdir -p /app/web/media/  &&  \
    pip install --upgrade pip && \
    pip install 'poetry>=1.4.2' && \
    poetry config virtualenvs.create false && \
    poetry install --no-root

COPY . .

EXPOSE 8000

COPY ./entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
