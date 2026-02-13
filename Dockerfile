# UltraShop — run on server (e.g. HELPIO.IR)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# Install dependencies + gosu (for entrypoint to run migrate as root then drop to appuser)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gosu \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files at build (no DB needed)
RUN python manage.py collectstatic --noinput --clear

# Entrypoint: migrate then run command
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Data dir and non-root user (entrypoint runs as root, then gosu to appuser)
RUN mkdir -p /app/data && useradd --create-home appuser && chown -R appuser:appuser /app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "2"]
