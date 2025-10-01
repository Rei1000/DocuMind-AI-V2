FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (layer caching)
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Copy contexts from parent directory
COPY contexts /app/contexts

# Set Python path
ENV PYTHONPATH=/app:/app/contexts

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Create startup script with database seeding
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🌱 Seeding database..."\n\
python3 seed_data.py || true\n\
echo "🚀 Starting server..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000' > /app/start.sh && chmod +x /app/start.sh

# Run application with seeding
CMD ["/app/start.sh"]
