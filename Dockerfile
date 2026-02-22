FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends libjpeg62-turbo-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Copy entrypoint script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Create non-root user
RUN addgroup --system app && adduser --system --ingroup app app && \
    chown -R app:app /app
USER app

# Persist data: mount a volume at /app/data and set env DJANGO_DB_PATH=/app/data/db.sqlite3
VOLUME /app/data

EXPOSE 8080

ENTRYPOINT ["/app/docker-entrypoint.sh"]
