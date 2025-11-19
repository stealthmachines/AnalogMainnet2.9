#!/bin/bash
# Create Docker network if it doesn't exist
docker network create hdgl_network 2>/dev/null || true

# Start services
docker compose up -d