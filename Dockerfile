# --- Stage 1: Frontend Builder ---
FROM node:20-slim AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# --- Stage 2: Python Builder (Install dependencies) ---
FROM python:3.11-slim AS python-builder
WORKDIR /build/backend
RUN apt-get update && apt-get install -y build-essential
COPY backend/requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# --- Stage 3: Runtime ---
FROM python:3.11-slim
WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed python packages from builder
COPY --from=python-builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copy backend code
COPY backend/ .

# Copy built frontend from frontend-builder
COPY --from=frontend-builder /build/frontend/out/ static/

# Ensure static directory permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Healthcheck for Cloud Run (documented practice)
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
