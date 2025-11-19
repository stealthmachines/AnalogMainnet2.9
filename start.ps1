#!/usr/bin/env pwsh

# Cross-platform startup script for HDGL Analog Mainnet
param (
    [string]$mode = "all",
    [switch]$i2c,
    [switch]$build
)

$ErrorActionPreference = "Stop"

# Function to check if running on Linux
function Test-Linux {
    return $PSVersionTable.Platform -eq "Unix"
}

# Base docker-compose command
$dockerCompose = "docker compose -f docker-compose.yml"

# Add profiles based on mode
switch ($mode) {
    "webhost" { $dockerCompose += " --profile webhost" }
    "bridge" { $dockerCompose += " --profile bridge" }
    "ipfs" { $dockerCompose += " --profile ipfs" }
    default { $dockerCompose += " --profile all" }
}

# Add I2C support if requested and on Linux
if ($i2c -and (Test-Linux)) {
    Write-Host "Enabling I2C support"
    $dockerCompose += " -f docker-compose.i2c.yml"
}

# Build if requested
if ($build) {
    Write-Host "Building containers..."
    Invoke-Expression "$dockerCompose build"
}

# Start services
Write-Host "Starting services in $mode mode..."
Invoke-Expression "$dockerCompose up -d"