# Use a lightweight Python image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install essential system packages
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    ffmpeg \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# ✅ Create supervisor directory and configuration
RUN mkdir -p /etc/supervisor/conf.d && \
    echo '[supervisord]' > /etc/supervisor/conf.d/supervisord.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:fastapi]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=uvicorn backend.main:app --host 0.0.0.0 --port 8000' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'directory=/app' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo '[program:celery]' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'command=celery -A backend.core.celery_app worker --loglevel=info --queues=ai_tasks --pool=solo' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'directory=/app' >> /etc/supervisor/conf.d/supervisord.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/supervisord.conf

# Expose FastAPI port
EXPOSE 8000

# Run supervisor as the container’s main process
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
