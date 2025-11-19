FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libi2c-dev \
    i2c-tools \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY hdgl_bridge_v36.py config.json ./
CMD ["python", "hdgl_bridge_v36.py"]