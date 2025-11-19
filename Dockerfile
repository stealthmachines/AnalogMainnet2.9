# Multi-stage build for HDGL Analog Mainnet
FROM node:18-alpine AS static-builder

WORKDIR /app
COPY generate_static.js ./
RUN node generate_static.js

FROM python:3.9-slim AS runtime

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libi2c-dev \
    i2c-tools \
    gcc \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY hdgl_bridge_v36.py web_services.py config.json ./
COPY shaders/ ./shaders/
COPY --from=static-builder /app/static/ ./static/
COPY --from=static-builder /app/templates/ ./templates/

# Default command (can be overridden)
CMD ["python", "hdgl_bridge_v36.py"]