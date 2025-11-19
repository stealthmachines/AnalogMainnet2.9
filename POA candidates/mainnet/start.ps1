# Create Docker network if it doesn't exist
docker network create hdgl_network 2>$null
if (-not $?) {
    Write-Host "Network hdgl_network already exists or error occurred"
}

# Start services
docker compose up -d