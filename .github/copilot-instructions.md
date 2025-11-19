# Copilot Instructions for HDGL Analog Mainnet (V2.6 / V3.6)

## Project Overview
HDGL Analog Mainnet is a distributed computing system with an analog lattice simulation core, web services for visualization and control, and blockchain integration.

## Core Architecture
1. Simulation Engine (`hdgl_analog_v26.c`):
   - RK4 integrator for analog lattice simulation
   - MPI support for distributed computing
   - Optional RTC hardware support via I2C
   - Critical constants: `CONSENSUS_EPS`, `CONSENSUS_N`, `GAMMA`, `K_COUPLING`

2. Bridge Service (`hdgl_bridge_v36.py`):
   - High-precision math (mpmath/Decimal)
   - IPFS/Ethereum integration
   - Checkpoint management with geometric decay
   - State encoding in dimension 7 for tape/program

3. Web Services (`web_services.py`):
   - Combined Flask application for all web interfaces
   - Socket.IO v4.7.2 for real-time updates
   - Endpoints:
     - `/explorer` - Network state explorer
     - `/program` - Program editor interface
     - `/visualizer` - 3D network visualization
     - `/stats` - Network statistics dashboard

## Minimal File Structure
Essential source files that generate everything else:
```
source-10.16.25/
├── hdgl_analog_v26.c        # Core simulation
├── hdgl_bridge_v36.py       # Bridge and orchestration
├── web_services.py          # Combined web services
├── config.json              # Configuration
├── generate_static.js       # Generates all static files
├── requirements.txt         # Python dependencies
├── Dockerfile              # Multi-stage build for all services
├── docker-compose.yml      # Service orchestration with profiles
├── start.ps1              # Cross-platform startup script
├── shaders/               # WebGL shader files
│   ├── fragment.glsl
│   └── vertex.glsl
└── .github/
    └── copilot-instructions.md
```

Generated directories (created automatically):
- `templates/` - Web interface templates
- `static/` - Generated static files
- `data/` - IPFS storage

## Critical Dependencies
1. Python Packages (requirements.txt):
   - flask-socketio==5.3.6 (must match client version)
   - python-socketio==5.9.0
   - ipfshttpclient
   - web3
   - mpmath
   - smbus2
   - numpy

2. Node.js Packages:
   - socket.io-client v4.7.2 (must match server version)
   - three.js
   - chart.js
   - express

## Build and Deploy
1. Development Build:
```powershell
./start.ps1 -mode all -build
```

2. Production Build:
```powershell
gcc -o hdgl_analog hdgl_analog_v26.c -lm -O3  # Core simulation
docker compose up -d --build                   # All services
```

3. Special Builds:
   - With RTC: `gcc -o hdgl_analog hdgl_analog_v26.c -lm -li2c -DUSE_DS3231 -O3`
   - With MPI: `mpicc -o hdgl_analog hdgl_analog_v26.c -lm -DMPI_REAL=1 -O3`

## Docker Profiles
- `all`: Everything (bridge, web services, IPFS)
- `webhost`: Web services only
- `bridge`: Bridge service only
- `ipfs`: IPFS node only
- `i2c`: Hardware I2C support (Linux only)

## Integration Points
1. Ethereum:
   - RPC URL in `config.json`
   - Private key in `ETH_PRIVATE_KEY` env var
   - Commitment hash via `Web3.keccak`

2. IPFS:
   - Local or remote node
   - HTTP API fallback if client incompatible
   - Used for snapshot storage

3. Hardware:
   - Optional DS3231 RTC via I2C
   - Fallback to system time if unavailable

4. Network:
   - Socket.IO for real-time updates
   - MPI for distributed computation
   - IPFS for P2P data sharing

## Critical Constants Alignment
These constants must remain synchronized between C and Python:
```c
// hdgl_analog_v26.c
#define CONSENSUS_EPS 1e-6
#define CONSENSUS_N 100
#define GAMMA 0.02
#define K_COUPLING 1.0
```
```python
# hdgl_bridge_v36.py
CONSENSUS_EPS = Decimal('1e-6')
CONSENSUS_N = 100
GAMMA = Decimal('0.02')
K_COUPLING = Decimal('1.0')
```

## Safety Checks
1. Before Code Changes:
   - Run smoke test: `python hdgl_bridge_v36.py --smoke`
   - Verify Socket.IO versions match
   - Check constant alignment

2. After Code Changes:
   - Generate static files: `node generate_static.js`
   - Rebuild all services: `docker compose up -d --build`
   - Verify all web endpoints

3. RNG Usage:
   - Use `det_rand(seed)` in Python
   - Use `det_rand(uint64_t)` in C
   - Maintain deterministic seeding

## Common Issues
1. Socket.IO Version Mismatch:
   - Server: flask-socketio==5.3.6
   - Client: socket.io-client v4.7.2
   - Fix: Update CDN links in generated HTML

2. IPFS Connection:
   - Error: "Unsupported daemon version"
   - Solution: Falls back to HTTP API
   - Check: IPFS node accessibility

3. Build Dependencies:
   - Python: build-essential, libssl-dev
   - Node.js: required for static generation
   - Fix: Update Dockerfile dependencies

## Next Steps Guide
1. First Steps:
   - Read this document completely
   - Run smoke test for baseline
   - Check all services are accessible

2. Making Changes:
   - Update both C and Python constants
   - Generate static files after changes
   - Run full build and test cycle

3. Deployment:
   - Use profiles for targeted deployment
   - Verify all integration points
   - Monitor service logs for issues

4. Maintenance:
   - Keep dependencies in sync
   - Check for security updates
   - Monitor disk usage (IPFS storage)