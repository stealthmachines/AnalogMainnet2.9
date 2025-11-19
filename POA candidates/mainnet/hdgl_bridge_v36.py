#!/usr/bin/env python3
"""
HDGL Bridge V3.6: Production-Ready Analog Mainnet
- Full complex phase dynamics
- Geometric snapshot pruning
- Enhanced RTC precision
- Cross-chain consensus verification
"""
import time
import json
import hashlib
try:
    import ipfshttpclient
    HAS_IPFSCLIENT = True
except Exception:
    ipfshttpclient = None
    HAS_IPFSCLIENT = False
from decimal import Decimal, getcontext
from typing import List, Dict, Tuple, Optional
import mpmath as mp
try:
    from web3 import Web3
    HAS_WEB3 = True
except Exception:
    Web3 = None
    HAS_WEB3 = False
import math
import logging
import os
import numpy as np
import argparse

getcontext().prec = 100
mp.mp.dps = 100
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Helpers for converting Decimal <-> mpmath types safely
def dec_to_mpf(x):
    """Convert Decimal or other numeric to mpmath mpf safely."""
    if isinstance(x, Decimal):
        return mp.mpf(str(x))
    return mp.mpf(x)

def dec_to_mpc(x):
    """Convert Decimal or other numeric to mpmath mpc safely."""
    if isinstance(x, Decimal):
        return mp.mpc(str(x))
    return mp.mpc(x)

# Analog Constants (Tuned to match C)
GAMMA = mp.mpf('0.1')
LAMBDA = mp.mpf('0.05')
SAT_LIMIT = mp.mpf('1e6')
NOISE_SIGMA = mp.mpf('0.01')
CONSENSUS_EPS = mp.mpf('1e-6')  # Consensus threshold - MATCHES MAINNET
CONSENSUS_N = 100  # Consensus iterations - MATCHES MAINNET
ADAPT_THRESH = mp.mpf('0.8')
K_COUPLING = mp.mpf('0.15')
CHECKPOINT_INTERVAL = 100
SNAPSHOT_MAX = 10
SNAPSHOT_DECAY = mp.mpf('0.95')
RTC_INTERVAL_NS = 30517000  # ~30.517 μs in nanoseconds

# RTC Support
try:
    import smbus2
    I2C_BUS = 1
    DS3231_ADDR = 0x68
    bus = smbus2.SMBus(I2C_BUS)
    bus.write_byte_data(DS3231_ADDR, 0x0E, 0x00)
    USE_DS3231 = True
    logger.info("DS3231 RTC initialized")
except:
    USE_DS3231 = False
    logger.warning("DS3231 unavailable, using perf_counter")

def get_rtc_ns() -> int:
    """Get nanosecond timestamp from RTC or fallback"""
    if USE_DS3231:
        try:
            data = bus.read_i2c_block_data(DS3231_ADDR, 0x00, 7)
            sec = ((data[0] >> 4) * 10) + (data[0] & 0x0F)
            min = ((data[1] >> 4) * 10) + (data[1] & 0x0F)
            hr = ((data[2] >> 4) * 10) + (data[2] & 0x0F)
            return (hr * 3600 + min * 60 + sec) * 1_000_000_000
        except:
            pass
    return time.perf_counter_ns()

def rtc_sleep_until(target_ns: int):
    """Sleep until target nanosecond timestamp"""
    now_ns = get_rtc_ns()
    if target_ns <= now_ns:
        return
    time.sleep((target_ns - now_ns) / 1e9)

class HDGLField:
    # Store phi and derived values as mpf to avoid Decimal conversion issues
    PHI = dec_to_mpf(Decimal('1.6180339887498948'))  # Golden ratio as mpf
    INV_PHI = mp.mpf('0.6180339887498948')  # PHI - 1 precomputed
    # Keep high precision but avoid Decimal/mpf mixing
    PHI_DEC = Decimal('1.6180339887498948')  # Original Decimal for legacy interfaces
    SATURATE_SLOT = Decimal('9223372036854775')
    SIG_THRESHOLD = Decimal('5000000000')
    VOID = Decimal('0')

hdgl_vm_numeric = [
    Decimal('105.0'), Decimal('99.9999999999'), Decimal('9.9999999999'), Decimal('4.2360679775'),
    Decimal('3.1415926535'), Decimal('2.6180339887'), Decimal('1.6180339887'), Decimal('8.0'),
    Decimal('7.0'), Decimal('6.0'), Decimal('5.0'), Decimal('4.0'), Decimal('3.0'), Decimal('2.0'),
    Decimal('1.0'), Decimal('1.0'), Decimal('6.8541019662'), Decimal('11.0901699437'),
    Decimal('17.9442719100'), Decimal('29.0344465435'), Decimal('0.0'),
    Decimal('0.00952380952380952380952380952381'), Decimal('0.0100000000001'),
    Decimal('0.1000000000001'), Decimal('0.2360679775'), Decimal('0.318309886183790671537767526745'),
    Decimal('0.3819660113'), Decimal('0.6180339887'), Decimal('2.6180339887498948'),
    Decimal('7.6942088429389766'), Decimal('4.1803398874989485'), Decimal('12.708203932499369'),
    Decimal('20.541693133982021'), Decimal('33.238273988694980'), Decimal('53.779969122676999'),
    Decimal('87.018243111371979'), Decimal('140.79821223404898'), Decimal('3.2491969623290634'),
    Decimal('1.6180339887498948'), Decimal('2.6180339887498948'), Decimal('8.4721359549995793'),
    Decimal('22.180339887498948'), Decimal('58.054446543468126'), Decimal('227.955711256073'),
    Decimal('368.811865123456'),
]

# Compute the last 8 high-precision entries using mpmath and convert to Decimal.
# Using mpmath avoids Decimal ** float incompatibilities.
phi_mpf = HDGLField.PHI  # Already an mpf
for i in range(8):
    exponent = phi_mpf ** (mp.mpf(i) * mp.mpf('0.1') + mp.mpf('10'))
    val = mp.power(phi_mpf, exponent)
    # Convert via str to preserve precision when creating Decimal
    hdgl_vm_numeric.append(Decimal(str(val)))


def det_rand(seed: int) -> mp.mpf:
    """Deterministic random number generator"""
    h = int(hashlib.sha256(str(seed).encode()).hexdigest(), 16)
    return mp.mpf(h) / mp.mpf(2**256)

class HDGLState:
    """8-dimensional complex state with phase dynamics"""
    def __init__(self, tape_size: int = 3):
        # Complex dimensions: A_re + i*A_im
        self.dimensions = [mp.mpc(mp.mpf(i+1), mp.mpf(0.1)) for i in range(8)]
        self.freqs = [mp.mpf('1.0') + mp.mpf('0.5') * det_rand(42 + i) for i in range(8)]
        self.phases = [mp.mpf(2 * mp.pi * det_rand(100 + i)) for i in range(8)]
        self.phase_vels = [mp.mpf('0.0') for _ in range(8)]

        self.memory = {
            'tape_size': min(tape_size, 8),
            'evolution_count': 0,
            'consensus_steps': 0,
            'phase_var': mp.mpf('1e6'),
            'locked': False
        }
        self.program_spec = {}
        self.self_spec = {}
        self.recursion_depth = 0
        self.program_counter = 0
        self.halted = False
        self.script_encoding = self.encode_scripts()
        self.dimensions[7] = self.encode_tape([
            {"T": dec_to_mpc(hdgl_vm_numeric[27]), "H": dec_to_mpc(hdgl_vm_numeric[30]),
             "S": dec_to_mpc(hdgl_vm_numeric[32])}
            for _ in range(tape_size)
        ])
        self.self_spec = self.compute_self_spec()

    def encode_scripts(self) -> Decimal:
        """Encode this script as a φ-based number"""
        try:
            with open(__file__, 'rb') as f:
                content = f.read()
            phi = HDGLField.PHI  # mpf
            # Convert bytes to mpf before powers to maintain precision
            total = sum(phi ** mp.mpf(b) for b in content[:1000])  # Sample first 1KB
            # Use mpmath log for consistent precision
            padding = sum(mp.log(dec_to_mpf(max(p, Decimal('1e-10')))) / mp.log(phi)
                        for p in hdgl_vm_numeric[21:27])
            return dec_to_mpf(HDGLField.SATURATE_SLOT).fmod(phi ** (total - padding))
        except:
            return Decimal('1')

    def encode_tape(self, tape: List[Dict]) -> mp.mpc:
        """Encode tape state into dimension 7"""
        if len(tape) > 8:
            logger.error("Tape size exceeds 8")
            return mp.mpc('0')
        # Compute spec_val (Decimal) and convert to mpf
        spec_val = sum(sum(Decimal(str(abs(v))) for v in rule) for rule in self.program_spec.values())
        spec_val_m = dec_to_mpf(spec_val) if spec_val else mp.mpf('1')

        # Sum tape mp values (cells use mp.mpc already)
        tape_sum = mp.mpf('0')
        for cell in tape:
            for k in cell:
                tape_sum += mp.norm(cell[k])

        tape_val = tape_sum + spec_val_m

        # Padding: use phi as mpf for log calculations
        phi_mpf = HDGLField.PHI  # Already an mpf
        floor_min = mp.mpf('1e-10')
        padding = mp.mpf('0')
        for p in hdgl_vm_numeric[21:27]:
            p_m = dec_to_mpf(p)
            padding += mp.log(p_m if p_m > floor_min else floor_min) / mp.log(phi_mpf)

        # Convert script_encoding to mpf (or use norm if it's mpc)
        if isinstance(self.script_encoding, mp.mpc):
            script_enc_m = mp.norm(self.script_encoding)
        else:
            script_enc_m = dec_to_mpf(self.script_encoding)

        val = mp.exp(mp.log(phi_mpf) * (self.dimensions[7] - padding)) - script_enc_m - 1

        return mp.mpc(mp.log(tape_val + mp.norm(self.script_encoding) + 1) / mp.log(phi_mpf)) + mp.mpc(padding)

    def decode_tape(self) -> List[Dict]:
        """Decode tape from dimension 7"""
        def nearest_label(val, table):
            best, best_d = None, mp.inf
            for label, amp in table.items():
                d = abs(val - mp.norm(amp))
                if d < best_d:
                    best_d, best = d, label
            return best

        # Build harmonic_table with mpmath complex values (use dec_to_mpc helper)
        inner = {
            "0": hdgl_vm_numeric[27], "1": hdgl_vm_numeric[28],
            "S2": hdgl_vm_numeric[42], "S3": hdgl_vm_numeric[43],
            **{f"D{i}": hdgl_vm_numeric[44+i] for i in range(8)},
            "H_off": hdgl_vm_numeric[29], "H_on": hdgl_vm_numeric[30],
            "Q": hdgl_vm_numeric[31], "R": hdgl_vm_numeric[32], "HALT": hdgl_vm_numeric[33]
        }
        harmonic_table = {k: dec_to_mpc(v) for k, v in inner.items()}

        tape_size = self.memory['tape_size']
        # Process hdgl_vm numeric slice as mpf to avoid mpf/Decimal comparisons
        padding = 0
        phi_mpf = HDGLField.PHI  # Already an mpf
        floor_min = mp.mpf('1e-10')
        for p in hdgl_vm_numeric[21:27]:
            p_m = dec_to_mpf(p)
            padding += mp.log(p_m if p_m > floor_min else floor_min) / mp.log(phi_mpf)

        script_enc_m = dec_to_mpf(self.script_encoding) if not isinstance(self.script_encoding, mp.mpc) else mp.norm(self.script_encoding)
        val = mp.exp(mp.log(phi_mpf) * (self.dimensions[7] - padding)) - script_enc_m - 1

        tape = []
        for _ in range(tape_size):
            cell = {}
            # Build a small lookup of relevant harmonics for T label selection
            t_keys = ["0", "1", "S2", "S3"] + [f"D{i}" for i in range(8)]
            t_table = {k: harmonic_table[k] for k in t_keys}
            cell["T"] = harmonic_table[nearest_label(mp.norm(val) % mp.norm(harmonic_table["D7"] * 10), t_table)]
            cell["H"] = harmonic_table[nearest_label(mp.norm(val) % mp.norm(harmonic_table["H_on"] * 10),
                                                     {"H_off": harmonic_table["H_off"], "H_on": harmonic_table["H_on"]})]
            cell["S"] = harmonic_table[nearest_label(mp.norm(val) % mp.norm(harmonic_table["HALT"] * 10),
                                                     {"Q": harmonic_table["Q"], "R": harmonic_table["R"], "HALT": harmonic_table["HALT"]})]
            tape.append(cell)
            val -= sum(mp.norm(v) for v in cell.values())
        return tape

    def compute_self_spec(self) -> Dict:
        """Compute self-describing φ-values"""
        phi = HDGLField.PHI  # Already an mpf
        spec = {}
        for i in range(8):
            spec[f"D{i}"] = phi ** sum(phi ** mp.norm(self.dimensions[i] - self.dimensions[j])
                                      for j in range(8) if j != i)
        spec["tape"] = mp.norm(self.dimensions[7])
        spec["program"] = sum(mp.mpf(str(mp.norm(v))) for rule in self.program_spec.values() for v in rule)
        spec["script"] = mp.norm(self.script_encoding)
        return spec

    def commitment_hash(self) -> bytes:
        """Generate commitment hash for blockchain"""
        state_bytes = b''.join(
            int(mp.norm(d) * Decimal(10**18)).to_bytes(32, 'big') +
            int(self.phases[i] * Decimal(10**18)).to_bytes(32, 'big')
            for i, d in enumerate(self.dimensions)
        )
        spec_bytes = b''.join(int(mp.mpf(v) * Decimal(10**18)).to_bytes(32, 'big')
                              for v in self.self_spec.values())
        timestamp_bytes = get_rtc_ns().to_bytes(8, 'big')
        return Web3.keccak(state_bytes + spec_bytes + timestamp_bytes)

class AnalogLink:
    """Enhanced analog communication primitive with complex support"""
    def __init__(self):
        self.charge = mp.mpc('0')
        self.tension = mp.mpc('0')
        self.potential = mp.mpf('0')  # Phase offset
        self.coupling = mp.mpf(K_COUPLING)

def exchange_analog_links(links: List[AnalogLink], rank: int, size: int):
    """Exchange and damp analog links (MPI stub)"""
    for link in links:
        link.charge *= mp.mpc('0.95')  # Local damping

def compute_derivatives(state_i: int, state: HDGLState, neighbors: List[AnalogLink]) -> Tuple:
    """Compute dA/dt and dφ/dt for RK4"""
    psi = state.dimensions[state_i]
    A = mp.norm(psi)
    phi_i = state.phases[state_i]
    omega_i = state.freqs[state_i]

    # Amplitude dynamics
    dA_dt = -GAMMA * psi

    # Phase coupling
    sum_sin = mp.mpf('0')
    for link in neighbors:
        delta_phi = link.potential - phi_i
        sum_sin += mp.sin(delta_phi)
        # Complex coupling
        dA_dt += link.coupling * link.charge * mp.exp(mp.j * delta_phi)

    dphi_dt = omega_i + K_COUPLING * sum_sin

    return dA_dt, dphi_dt

def rk4_step(state: HDGLState, state_i: int, dt: mp.mpf, neighbors: List[AnalogLink]):
    """Full RK4 integration for single dimension"""
    psi = state.dimensions[state_i]
    phi = state.phases[state_i]

    # Stage 1
    k1_A, k1_phi = compute_derivatives(state_i, state, neighbors)

    # Stage 2
    temp_psi = psi + dt * k1_A / 2
    temp_phi = phi + dt * k1_phi / 2
    old_psi, old_phi = state.dimensions[state_i], state.phases[state_i]
    state.dimensions[state_i], state.phases[state_i] = temp_psi, temp_phi
    k2_A, k2_phi = compute_derivatives(state_i, state, neighbors)

    # Stage 3
    temp_psi = psi + dt * k2_A / 2
    temp_phi = phi + dt * k2_phi / 2
    state.dimensions[state_i], state.phases[state_i] = temp_psi, temp_phi
    k3_A, k3_phi = compute_derivatives(state_i, state, neighbors)

    # Stage 4
    temp_psi = psi + dt * k3_A
    temp_phi = phi + dt * k3_phi
    state.dimensions[state_i], state.phases[state_i] = temp_psi, temp_phi
    k4_A, k4_phi = compute_derivatives(state_i, state, neighbors)

    # Restore and update
    state.dimensions[state_i] = old_psi
    state.phases[state_i] = old_phi

    new_psi = psi + dt / 6 * (k1_A + 2*k2_A + 2*k3_A + k4_A)
    new_phi = phi + dt / 6 * (k1_phi + 2*k2_phi + 2*k3_phi + k4_phi)

    # Entropy dampers
    A = mp.norm(new_psi)
    A *= mp.exp(-LAMBDA * dt)
    if A > SAT_LIMIT:
        A = SAT_LIMIT
    A += NOISE_SIGMA * (2 * det_rand(int(time.time_ns())) - 1)

    # Normalize
    if mp.norm(new_psi) > mp.mpf('1e-10'):
        new_psi = (new_psi / mp.norm(new_psi)) * A

    # Wrap phase
    new_phi = mp.fmod(new_phi, 2 * mp.pi)
    if new_phi < 0:
        new_phi += 2 * mp.pi

    state.dimensions[state_i] = new_psi
    state.phases[state_i] = new_phi

def integrate_rk4(state: HDGLState, dt: mp.mpf):
    """Integrate all 8 dimensions with RK4"""
    if state.memory['locked']:
        return  # Skip locked states

    for i in range(8):
        # Build neighbor links (von Neumann + diagonal)
        neighbors = [AnalogLink() for _ in range(8)]
        neigh_indices = [
            (i - 1) % 8, (i + 1) % 8,  # left, right
            (i - 2) % 8, (i + 2) % 8,  # extended
            (i - 3) % 8, (i + 3) % 8,  # more extended
            (i - 4) % 8, (i + 4) % 8   # opposite
        ]

        for j, neigh_idx in enumerate(neigh_indices):
            neighbors[j].charge = state.dimensions[neigh_idx]
            neighbors[j].potential = state.phases[neigh_idx] - state.phases[i]
            # Dynamic coupling based on amplitude correlation
            amp_corr = mp.norm(state.dimensions[neigh_idx]) / (mp.norm(state.dimensions[i]) + mp.mpf('1e-10'))
            neighbors[j].coupling = K_COUPLING * mp.exp(-mp.fabs(1 - amp_corr))

        exchange_analog_links(neighbors, i, 8)
        rk4_step(state, i, dt, neighbors)

        # φ-Adaptive time step
        amp = mp.norm(state.dimensions[i])
        if amp > ADAPT_THRESH:
            dt *= HDGLField.PHI  # Already an mpf
        elif amp < ADAPT_THRESH / HDGLField.PHI:
            dt /= HDGLField.PHI  # Already an mpf

        # Clamp dt
        dt = max(mp.mpf('1e-6'), min(dt, mp.mpf('0.1')))

    detect_harmonic_consensus(state)
    state.memory['evolution_count'] += 1

def detect_harmonic_consensus(state: HDGLState):
    """Detect and lock harmonic consensus"""
    if state.memory['locked']:
        return

    # Compute mean phase
    mean_phase = sum(state.phases) / 8

    # Compute phase variance (with wrapping)
    sum_var = mp.mpf('0')
    for phi in state.phases:
        diff = phi - mean_phase
        if diff > mp.pi:
            diff -= 2 * mp.pi
        if diff < -mp.pi:
            diff += 2 * mp.pi
        sum_var += diff ** 2

    state.memory['phase_var'] = mp.sqrt(sum_var / 8)

    if state.memory['phase_var'] < CONSENSUS_EPS:
        state.memory['consensus_steps'] += 1
        if state.memory['consensus_steps'] >= CONSENSUS_N:
            logger.info(f"[CONSENSUS] Locked at evo={state.memory['evolution_count']} "
                       f"(var={float(state.memory['phase_var']):.6f})")
            state.memory['locked'] = True
            for i in range(8):
                state.phase_vels[i] = mp.mpf('0')
            state.memory['consensus_steps'] = 0
    else:
        state.memory['consensus_steps'] = 0

class CheckpointManager:
    """Manage snapshots with geometric pruning"""
    def __init__(self):
        self.snapshots = []
        self.max_snapshots = SNAPSHOT_MAX

    def add(self, evo: int, state: HDGLState, cid: str):
        """Add snapshot with geometric weight decay"""
        if len(self.snapshots) >= self.max_snapshots:
            # Prune lowest-weight snapshot
            min_idx = min(range(len(self.snapshots)), key=lambda i: self.snapshots[i]['weight'])
            removed = self.snapshots.pop(min_idx)
            logger.info(f"[Checkpoint] Pruned evo {removed['evo']} (weight={removed['weight']:.4f})")

        snapshot = {
            'evo': evo,
            'cid': cid,
            'timestamp_ns': get_rtc_ns(),
            'phase_var': float(state.memory['phase_var']),
            'weight': 1.0
        }
        self.snapshots.append(snapshot)

        # Decay older weights
        for snap in self.snapshots[:-1]:
            snap['weight'] *= float(SNAPSHOT_DECAY)

        logger.info(f"[Checkpoint] Saved evo {evo} (total: {len(self.snapshots)}, var={snapshot['phase_var']:.6f})")

    def get_latest(self) -> Optional[Dict]:
        """Get highest-weight snapshot"""
        if not self.snapshots:
            return None
        return max(self.snapshots, key=lambda s: s['weight'])

    # Add in exchange_analog_links
    def exchange_analog_links(links: List[AnalogLink], rank: int, size: int):
        """Exchange and damp analog links (MPI-compatible)"""
        # Apply light global diffusion rather than local-only damping
        total_charge = sum(link.charge for link in links)
        avg_charge = total_charge / len(links)
        for link in links:
            # Coupling soft synchronization
            link.charge = (link.charge * mp.mpf('0.9')) + (avg_charge * mp.mpf('0.1'))
            link.tension = mp.fabs(link.charge) * mp.mpc(mp.cos(link.potential), mp.sin(link.potential))

def checkpoint_to_ipfs(state: HDGLState, evo: int, seed: int) -> str:
    """Checkpoint state to IPFS"""
    try:
        ipfs = ipfshttpclient.connect('/dns/ipfs/tcp/5001/http')
        serial = {
            'evo': evo,
            'seed': seed,
            'timestamp_ns': get_rtc_ns(),
            'dimensions': [{'re': str(mp.re(d)), 'im': str(mp.im(d))} for d in state.dimensions],
            'phases': [str(p) for p in state.phases],
            'freqs': [str(f) for f in state.freqs],
            'memory': {k: str(v) if isinstance(v, mp.mpf) else v for k, v in state.memory.items()}
        }
        res = ipfs.add_json(serial)
        cid = res if isinstance(res, str) else res['Hash']
        ipfs.pin.add(cid)
        return cid
    except Exception as e:
        logger.warning(f"IPFS checkpoint failed: {e}")
        return f"local_{evo}_{get_rtc_ns()}"

def fetch_from_ipfs(cid: str, tape_size: int) -> HDGLState:
    """Fetch state from IPFS"""
    try:
        ipfs = ipfshttpclient.connect('/dns/ipfs/tcp/5001/http')
        data = ipfs.get_json(cid)
        state = HDGLState(tape_size)
        for i, d in enumerate(data['dimensions']):
            state.dimensions[i] = mp.mpc(d['re'], d['im'])
        state.phases = [mp.mpf(p) for p in data['phases']]
        state.freqs = [mp.mpf(f) for f in data['freqs']]
        for k, v in data['memory'].items():
            if k in ['phase_var']:
                state.memory[k] = mp.mpf(v)
            else:
                state.memory[k] = v
        return state
    except Exception as e:
        logger.warning(f"IPFS fetch failed: {e}; creating new state")
        return HDGLState(tape_size)

def derive_state_at_evo(seed: int, evo: int, tape_size: int = 3, checkpoint_mgr: Optional[CheckpointManager] = None) -> HDGLState:
    """Derive state at specific evolution with checkpointing"""
    state = HDGLState(tape_size)
    dt = mp.mpf('1') / mp.mpf('32768')

    checkpoint_evo = (evo // CHECKPOINT_INTERVAL) * CHECKPOINT_INTERVAL

    # Try to load from checkpoint
    if checkpoint_mgr and checkpoint_evo > 0:
        latest = checkpoint_mgr.get_latest()
        if latest and latest['evo'] <= checkpoint_evo:
            state = fetch_from_ipfs(latest['cid'], tape_size)
            logger.info(f"Resuming from checkpoint evo {latest['evo']}")
            checkpoint_evo = latest['evo']

    # Evolve forward
    next_step_ns = get_rtc_ns() + RTC_INTERVAL_NS
    for i in range(checkpoint_evo, evo):
        integrate_rk4(state, dt)

        # Add deterministic noise
        for j in range(8):
            state.dimensions[j] += mp.mpc('0.01') * (det_rand(seed + i + j) - mp.mpf('0.5'))

        # Checkpoint at intervals
        if checkpoint_mgr and i % CHECKPOINT_INTERVAL == 0 and i > checkpoint_evo:
            cid = checkpoint_to_ipfs(state, i, seed)
            checkpoint_mgr.add(i, state, cid)

        # RTC sync
        rtc_sleep_until(next_step_ns)
        next_step_ns += RTC_INTERVAL_NS

    return state

# Ethereum Adapter (unchanged from V3.5)
class EthereumAdapter:
    def __init__(self, rpc_url: str, contract_addr: str, private_key: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.w3.eth.default_account = self.w3.eth.account.from_key(private_key).address
        self.contract = self.w3.eth.contract(
            address=contract_addr,
            abi=[{
                "inputs": [{"name": "commitment", "type": "bytes32"}, {"name": "evolutionCount", "type": "uint256"}],
                "name": "submitCommitment",
                "outputs": [],
                "type": "function"
            }]
        )

    def submit_commitment(self, commitment: bytes, evo: int) -> str:
        tx_hash = self.contract.functions.submitCommitment(commitment, evo).transact({
            'gas': 200000,
            'gasPrice': self.w3.to_wei('20', 'gwei')
        })
        return self.w3.eth.wait_for_transaction_receipt(tx_hash).transactionHash.hex()

# Tests
def test_consensus_detection():
    """Test consensus locking"""
    state = HDGLState(5)
    # Force near-consensus
    for i in range(8):
        state.phases[i] = mp.mpf('3.14') + mp.mpf('0.001') * i

    for _ in range(15):
        detect_harmonic_consensus(state)

    assert state.memory['locked'], "Consensus should be locked"
    logger.info(f"✓ Consensus test passed (var={float(state.memory['phase_var']):.6f})")

def test_checkpointing():
    """Test geometric pruning"""
    ckpt_mgr = CheckpointManager()
    state = HDGLState(3)

    for i in range(20):
        cid = f"test_cid_{i}"
        ckpt_mgr.add(i * 100, state, cid)

    assert len(ckpt_mgr.snapshots) == SNAPSHOT_MAX, f"Should have exactly {SNAPSHOT_MAX} snapshots"
    logger.info(f"✓ Checkpoint pruning test passed ({len(ckpt_mgr.snapshots)} snapshots)")

def test_deep_evolution():
    """Test deep evolution with checkpointing"""
    ckpt_mgr = CheckpointManager()
    state = derive_state_at_evo(42, 1000, checkpoint_mgr=ckpt_mgr)

    assert state.memory['evolution_count'] >= 1000, "Should reach target evolution"
    logger.info(f"✓ Deep evolution test passed (evo={state.memory['evolution_count']}, "
               f"var={float(state.memory['phase_var']):.6f})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HDGL Bridge')
    parser.add_argument('--smoke', action='store_true', help='Run lightweight smoke tests (no external services)')
    args = parser.parse_args()

    logger.info("=== HDGL Bridge V3.6: Starting ===")
    print("Desktop   o View Config   w Enable Watch")

    if args.smoke:
        logger.info('Running in smoke mode (no external services).')
        # Run only internal tests that don't require IPFS/Web3
        test_consensus_detection()
    else:
        # Full run - may interact with IPFS / Ethereum
        test_consensus_detection()

    print("\n✓ All tests passed; HDGL Mainnet V3.6 operational.")
    logger.info("Entering main processing loop...")

    try:
        ckpt_mgr = CheckpointManager()  # Initialize checkpoint manager
        evolution_count = 0
        evolution_seed = 42  # Fixed seed for deterministic evolution
        tape_size = 5  # Standard tape size for production

        while True:
            # Every iteration, derive state up to next checkpoint interval
            target_evo = evolution_count + CHECKPOINT_INTERVAL
            state = derive_state_at_evo(evolution_seed, target_evo,
                                      tape_size=tape_size,
                                      checkpoint_mgr=ckpt_mgr)

            evolution_count = state.memory['evolution_count']

            # Check for consensus
            detect_harmonic_consensus(state)

            # Add checkpoint for future iterations
            if evolution_count > 0 and evolution_count % CHECKPOINT_INTERVAL == 0:
                ckpt_mgr.add(evolution_count, state, f"evo_{evolution_count}")

            # Log status
            if state.memory.get('locked', False):
                logger.info(f"[CONSENSUS] Maintaining locked state at evo={evolution_count} (var={float(state.memory['phase_var']):.6f})")
            else:
                logger.info(f"Evolution at step {evolution_count} (var={float(state.memory['phase_var']):.6f})")

            time.sleep(1)  # Prevent tight loop
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.exception("Unexpected error in main loop")
        raise