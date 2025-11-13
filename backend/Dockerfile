FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (curl für Health Check, gcc für Python-Packages)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Layer Caching: Dependencies ändern sich seltener als Code)
COPY backend/requirements.txt .

# Install Python dependencies (separate Layer für besseres Caching)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (separate Layer: Code ändert sich häufiger)
COPY backend/ .

# Copy contexts from parent directory (separate Layer)
COPY contexts /app/contexts

# Set Python path
ENV PYTHONPATH=/app:/app/contexts

# Expose port
EXPOSE 8000

# Health check (verwendet curl statt Python requests - schneller)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Create startup script with database initialization
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🌱 Initializing database..."\n\
python3 init_database.py || true\n\
echo "🚀 Starting server..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000' > /app/start.sh && chmod +x /app/start.sh

# Run application with database initialization
CMD ["/app/start.sh"]
