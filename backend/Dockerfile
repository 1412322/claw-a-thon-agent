FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (exclude chroma_db)
COPY app ./app
COPY static ./static

# Note: .env is provided by AgentBase Runtime at runtime via environment variables
# Do not COPY .env.example - it would override runtime env vars

# Create empty chroma_db directory (will be mounted as volume in production)
RUN mkdir -p /app/chroma_db && chmod 755 /app/chroma_db

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
