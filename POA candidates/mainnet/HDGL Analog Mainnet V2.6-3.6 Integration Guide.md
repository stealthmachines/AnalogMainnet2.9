# HDGL Analog Mainnet V2.6/3.6 Integration Guide

## Overview

This guide covers the refined, production-ready analog ledger system with full complex phase dynamics, geometric snapshot pruning, and enhanced consensus detection.

## Key Improvements from Previous Versions

### 1. **Full Complex Phase Dynamics**
- **C Implementation**: Separated `A_re`, `A_im` for complex amplitudes
- **Python Implementation**: Native `mp.mpc` complex support
- **Phase Tracking**: Added `phase`, `phase_vel` for instantaneous velocity
- **RK4 Integration**: Full 4-stage Runge-Kutta with complex derivatives

### 2. **Enhanced Consensus Detection**
- **Tighter Threshold**: `CONSENSUS_EPS = 0.005` (was 0.01)
- **Longer Lock**: `CONSENSUS_N = 10` steps (was 5)
- **Phase Wrapping**: Proper handling of ±π discontinuities
- **Domain Locking**: `APA_FLAG_CONSENSUS` freezes dynamics permanently

### 3. **Geometric Snapshot Pruning**
- **Weight-Based**: New snapshots start at weight 1.0
- **Decay**: Older snapshots decay by `SNAPSHOT_DECAY = 0.95` per new snapshot
- **Pruning**: Removes lowest-weight snapshot when at capacity
- **Benefits**: Naturally retains recent + high-importance checkpoints

### 4. **Precision RTC Integration**
- **DS3231 Support**: Hardware RTC with I²C (define `USE_DS3231`)
- **Fallback**: `CLOCK_MONOTONIC` (C) or `perf_counter_ns` (Python)
- **Synchronization**: `rtc_sleep_until()` for precise timing
- **Interval**: 30.517 μs per step (1/32768 s)

### 5. **Dynamic Coupling**
- **Amplitude-Dependent**: `K * exp(-|1 - A_j/A_i|)`
- **Complex Links**: Full `charge_re`, `charge_im` transmission
- **Von Neumann + Diagonal**: 8 neighbors per dimension

## Build Instructions

### C Version (V2.6)

```bash
# Basic build
gcc -o hdgl_analog hdgl_analog_v26.c -lm -O3

# With DS3231 RTC support
gcc -o hdgl_analog hdgl_analog_v26.c -lm -li2c -DUSE_DS3231 -O3

# With MPI (distributed)
mpicc -o hdgl_analog hdgl_analog_v26.c -lm -DMPI_REAL=1 -O3

# Full production build
mpicc -o hdgl_analog hdgl_analog_v26.c -lm -li2c -DUSE_DS3231 -DMPI_REAL=1 -O3 -march=native
```

### Python Version (V3.6)

```bash
# Install dependencies
pip install ipfshttpclient web3 mpmath smbus2 numpy

# Run tests
python hdgl_bridge_v36.py

# Production run (requires config.json + IPFS + Ethereum node)
# See Configuration section below
```

## Configuration

### C Configuration (compile-time)

Edit constants in `hdgl_analog_v26.c`:

```c
#define MAX_INSTANCES 8388608      // Max lattice size
#define CHECKPOINT_INTERVAL 100    // Steps between checkpoints
#define SNAPSHOT_MAX 10            // Max snapshots retained
#define CONSENSUS_EPS 0.005        // Phase variance threshold
#define CONSENSUS_N 10             // Steps to lock
#define K_COUPLING 0.15            // Coupling strength
```

### Python Configuration (runtime)

Create `config.json`:

```json
{
  "eth_rpc": "http://localhost:8545",
  "eth_contract": "0xYourContractAddress",
  "poll_interval": 30,
  "auto_evolve": true,
  "tm_tape_size": 5,
  "checkpoint_interval": 100
}
```

Set environment variable:
```bash
export ETH_PRIVATE_KEY="0x..."
```

## Docker Deployment

### Dockerfile

```dockerfile
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
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  hdgl-bridge:
    build: .
    volumes:
      - ./data:/app/data
      - /dev/i2c-1:/dev/i2c-1
    devices:
      - /dev/i2c-1
    environment:
      - ETH_PRIVATE_KEY=${ETH_PRIVATE_KEY}
    depends_on:
      - ipfs
      - eth-node
    restart: unless-stopped

  ipfs:
    image: ipfs/go-ipfs:latest
    ports:
      - "5001:5001"
      - "8080:8080"
    volumes:
      - ipfs-data:/data/ipfs

  eth-node:
    image: ethereum/client-go:latest
    command: --http --http.addr 0.0.0.0 --http.api eth,net,web3
    ports:
      - "8545:8545"
    volumes:
      - eth-data:/root/.ethereum

volumes:
  ipfs-data:
  eth-data:
```

## Usage Examples

### C: Basic Analog Evolution

```c
#include "hdgl_analog_v26.c"

int main() {
    srand(time(NULL));

    // Initialize lattice (4096 instances, 4 slots each)
    HDGLLattice *lat = lattice_init(4096, 4);
    CheckpointManager *ckpt_mgr = checkpoint_init();

    // Seed with 500 steps
    bootloader_init_lattice(lat, 500, ckpt_mgr);

    // Evolve to consensus
    for (int i = 0; i < 10000; i++) {
        lattice_integrate_rk4(lat, 1.0 / 32768.0);

        if (i % 1000 == 0) {
            printf("Step %d: var=%.6f consensus=%d\n",
                   i, lat->phase_var, lat->consensus_steps);
        }
    }

    // Cleanup
    checkpoint_free(ckpt_mgr);
    lattice_free(lat);
    return 0;
}
```

### Python: Checkpointed Evolution

```python
from hdgl_bridge_v36 import *

# Initialize
ckpt_mgr = CheckpointManager()

# Evolve to target with checkpointing
state = derive_state_at_evo(
    seed=42,
    evo=100000,
    tape_size=5,
    checkpoint_mgr=ckpt_mgr
)

# Check consensus
print(f"Evolution: {state.memory['evolution_count']}")
print(f"Phase var: {float(state.memory['phase_var']):.6f}")
print(f"Locked: {state.memory['locked']}")

# Commit to Ethereum
eth = EthereumAdapter(rpc_url, contract_addr, private_key)
commitment = state.commitment_hash()
tx_hash = eth.submit_commitment(commitment, state.memory['evolution_count'])
print(f"Committed: {tx_hash}")
```