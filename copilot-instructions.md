# Copilot instructions for HDGL Analog Mainnet (V2.6 / V3.6)

This file contains concise, project-specific guidance for working in this workspace.

## Core Architecture
- Simulation engine: `hdgl_analog_v26.c` — C implementation of analog lattice with RK4 integrator
- Bridge service: `hdgl_bridge_v36.py` — Python orchestration, high-precision math, IPFS/Ethereum integration
- Web services:
  - `explorer_server.py` + `static/explorer/*` — Network state explorer
  - `program_server.py` + `static/program/*` — Program editor interface
  - `visualizer_server.js` + `static/visualizer/*` — 3D network visualization
  - `stats_server.js` + `static/stats/*` — Network statistics dashboard
- Configuration: `config.json` — Runtime parameters and service endpoints

When making changes, ensure C constants and Python constants remain semantically synced (e.g., GAMMA, K_COUPLING, CONSENSUS_EPS, CHECKPOINT_INTERVAL).

## Critical developer workflows (commands you can run / update)
- Build C (single-node):
  - `gcc -o hdgl_analog hdgl_analog_v26.c -lm -O3`
  - With RTC: `gcc -o hdgl_analog hdgl_analog_v26.c -lm -li2c -DUSE_DS3231 -O3`
  - Distributed (MPI stub -> real MPI): `mpicc -o hdgl_analog hdgl_analog_v26.c -lm -DMPI_REAL=1 -O3`
- Python: install runtime deps and run bridge:
  - `pip install ipfshttpclient web3 mpmath smbus2 numpy`
  - `python hdgl_bridge_v36.py` (requires `config.json` and running IPFS/Ethereum services for full feature set)
- Docker: follow Dockerfile and docker-compose snippets in the integration guide — Python service expects `config.json` and environment variable `ETH_PRIVATE_KEY`.

Note on Docker + hardware I2C:
- The repository now provides an opt-in Compose override `docker-compose.i2c.yml` which maps `/dev/i2c-1` into the `hdgl-bridge` container for Linux hosts.
- Do NOT map `/dev/i2c-1` on Windows or macOS: it will fail with "not a device node". Example (Linux):
  - `docker compose -f docker-compose.yml -f docker-compose.i2c.yml up`

## Project-specific conventions & important patterns
- Deterministic RNG: both files use `det_rand(seed)` (Python) / `det_rand(uint64_t)` (C) — prefer using these for seeded experiments rather than `random`/`rand()` directly.
- High-precision math: Python uses `mpmath` and `Decimal` extensively; avoid converting to native float unless intentionally lossy.
- State encoding: dimension 7 (index 7) is used to encode the tape/program; changes to tape encoding must update both `encode_tape`/`decode_tape` in `hdgl_bridge_v36.py` and any C-side consumers.
- Consensus logic: `CONSENSUS_EPS` and `CONSENSUS_N` control locking; unit changes to these affect when `HDGLState.memory['locked']` is set — search for these constants before modifying behavior.
- Snapshot/Checkpoint policy: `CheckpointManager` uses geometric decay (`SNAPSHOT_DECAY`) and `SNAPSHOT_MAX` — pruning logic expects weight math; keep semantics intact when refactoring.

## Integration points & external dependencies
- Ethereum/Web3: `hdgl_bridge_v36.py` calls Web3.keccak and expects an Ethereum RPC reachable via `config.json.eth_rpc` and an `ETH_PRIVATE_KEY` in env.
- IPFS: `ipfshttpclient` used for snapshot storage; ensure local `go-ipfs` or remote node is available for integration tests.
- RTC (optional): DS3231 via `smbus2` (`USE_DS3231` in C and try/except probe in Python). Code must gracefully fallback to perf_counter / CLOCK_MONOTONIC.
- MPI: code contains an `MPI` stub; enabling multi-node requires compiling with `-DMPI_REAL=1` and running under `mpirun`.

## Concrete examples to reference when editing
- To change consensus behavior, edit `CONSENSUS_EPS` / `CONSENSUS_N` in both `hdgl_analog_v26.c` and `hdgl_bridge_v36.py` (they should remain aligned).
- To change tape capacity: update `tm_tape_size` in `config.json` and the `tape_size` param used when `HDGLState` is constructed in Python.
- To add commits to Ethereum: see `HDGLState.commitment_hash()` in `hdgl_bridge_v36.py` — it builds `state_bytes` from `dimensions` + `phases` and uses `Web3.keccak`.

## Safety checks and quick heuristics for code edits
- Preserve deterministic seeds and `det_rand` usage in experiments. If you replace RNG, add explicit seed propagation.
- Keep high-precision logic in Python inside `mpmath`/`Decimal` wrappers; only convert to bytes/ints when creating blockchain commitments.
- When touching checkpoint/pruning logic, run a short local evolution (e.g., 1k steps) and inspect `CheckpointManager.snapshots` weights to verify decay/prune behavior.

## If you need to add tests or CI
- Add smoke tests that run `python hdgl_bridge_v36.py --smoke` (implement flag if missing) to run ~100 integration steps without external services.
- For C, add a small test binary that initializes a lattice for N steps and prints phase variance; compile with `-DTEST_BUILD` to avoid changing production binary behavior.

## Files to open first (high-signal)
- `hdgl_analog_v26.c` (core numerical engine)
- `hdgl_bridge_v36.py` (orchestration, web3/ipfs integration)
- `config.json` (runtime knobs)
- `HDGL Analog Mainnet V2.6-3.6 Integration Guide.md` (design and commands)

---
If any of the above sections are unclear or you want more examples (small tests, CI snippets, or a smoke-run wrapper), tell me which area to expand and I will iterate.
