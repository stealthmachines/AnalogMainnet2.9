"""
HDGL Ethereum Smart Contract Integration
Handles interaction with the HDGLLatticeContract for proof of authority and state synchronization
"""

import json
import time
import hashlib
from web3 import Web3
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class HDGLEthereumIntegration:
    def __init__(self, config):
        self.web3 = None
        self.contract = None
        self.account = None
        self.config = config
        self.last_sync_time = 0
        self.sync_interval = 30  # Sync every 30 seconds

        self._initialize_connection()

    def _initialize_connection(self):
        """Initialize Web3 connection and contract"""
        try:
            # Connect to Ethereum node
            eth_url = self.config.get('eth_rpc_url', 'http://localhost:8545')
            self.web3 = Web3(Web3.HTTPProvider(eth_url))

            if not self.web3.is_connected():
                logger.warning("Ethereum node not connected, running in standalone mode")
                return

            # Load contract ABI and address
            contract_address = self.config.get('hdgl_contract_address')
            if not contract_address:
                logger.warning("No HDGL contract address configured")
                return

            # Simple ABI for the functions we need
            contract_abi = [
                {
                    "inputs": [{"type": "string", "name": "scriptContent"}, {"type": "uint256", "name": "latticeEffect"}],
                    "name": "executeLatticeScript",
                    "outputs": [{"type": "string", "name": "scriptHash"}],
                    "type": "function"
                },
                {
                    "inputs": [{"type": "bytes32", "name": "commitmentHash"}],
                    "name": "makeCommitment",
                    "outputs": [],
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "currentState",
                    "outputs": [
                        {"type": "uint256", "name": "evolutionCount"},
                        {"type": "uint256", "name": "phaseVariance"},
                        {"type": "bytes32", "name": "stateHash"},
                        {"type": "uint256", "name": "timestamp"},
                        {"type": "bool", "name": "consensusLocked"}
                    ],
                    "type": "function"
                },
                {
                    "inputs": [],
                    "name": "getNetworkStats",
                    "outputs": [
                        {"type": "uint256", "name": "totalScripts"},
                        {"type": "uint256", "name": "totalCommitments"},
                        {"type": "uint256", "name": "confirmedCommitments"},
                        {"type": "bool", "name": "consensusStatus"}
                    ],
                    "type": "function"
                }
            ]

            self.contract = self.web3.eth.contract(
                address=contract_address,
                abi=contract_abi
            )

            # Setup account from private key
            private_key = self.config.get('eth_private_key')
            if private_key:
                self.account = self.web3.eth.account.from_key(private_key)
                logger.info(f"Ethereum integration initialized with account: {self.account.address}")
            else:
                logger.warning("No private key configured for Ethereum transactions")

        except Exception as e:
            logger.error(f"Failed to initialize Ethereum connection: {e}")
            self.web3 = None
            self.contract = None

    def is_connected(self):
        """Check if Ethereum integration is active"""
        return self.web3 is not None and self.web3.is_connected() and self.contract is not None

    def submit_lattice_script(self, script_content, lattice_effect):
        """Submit a lattice script to the smart contract"""
        if not self.is_connected() or not self.account:
            logger.warning("Cannot submit script - Ethereum not connected or no account")
            return None

        try:
            # Convert lattice effect to fixed-point (6 decimal places)
            lattice_effect_fixed = int(float(lattice_effect) * 1_000_000)

            # Build transaction
            tx = self.contract.functions.executeLatticeScript(
                script_content,
                lattice_effect_fixed
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': 300000,
                'gasPrice': self.web3.to_wei('20', 'gwei')
            })

            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            logger.info(f"Lattice script submitted to blockchain: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Failed to submit lattice script: {e}")
            return None

    def make_commitment(self, evolution_count, phase_variance, state_data):
        """Make a commitment to the current lattice state"""
        if not self.is_connected() or not self.account:
            return None

        try:
            # Generate commitment hash
            commitment_data = f"{evolution_count}:{phase_variance}:{state_data}"
            commitment_hash = hashlib.sha256(commitment_data.encode()).digest()

            # Build transaction
            tx = self.contract.functions.makeCommitment(
                commitment_hash
            ).build_transaction({
                'from': self.account.address,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gas': 150000,
                'gasPrice': self.web3.to_wei('20', 'gwei')
            })

            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            logger.info(f"Commitment made to blockchain: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Failed to make commitment: {e}")
            return None

    def get_contract_state(self):
        """Get current state from the smart contract"""
        if not self.is_connected():
            return None

        try:
            # Get current lattice state
            state = self.contract.functions.currentState().call()

            # Get network statistics
            stats = self.contract.functions.getNetworkStats().call()

            return {
                'evolution_count': state[0],
                'phase_variance': state[1] / 1_000_000,  # Convert from fixed-point
                'state_hash': state[2].hex(),
                'timestamp': state[3],
                'consensus_locked': state[4],
                'total_scripts': stats[0],
                'total_commitments': stats[1],
                'confirmed_commitments': stats[2],
                'consensus_status': stats[3]
            }

        except Exception as e:
            logger.error(f"Failed to get contract state: {e}")
            return None

    def sync_with_contract(self, local_evolution_count, local_phase_variance):
        """Synchronize local state with smart contract"""
        current_time = time.time()

        # Check if it's time to sync
        if current_time - self.last_sync_time < self.sync_interval:
            return None

        self.last_sync_time = current_time

        if not self.is_connected():
            return None

        try:
            contract_state = self.get_contract_state()
            if not contract_state:
                return None

            # Check if we need to make a commitment
            evolution_diff = abs(local_evolution_count - contract_state['evolution_count'])
            variance_diff = abs(float(local_phase_variance) - contract_state['phase_variance'])

            # Make commitment if significant difference or periodic commitment
            if evolution_diff > 10 or variance_diff > 0.01 or (local_evolution_count % 100 == 0):
                state_data = f"local_evo_{local_evolution_count}_var_{local_phase_variance}"
                commitment_tx = self.make_commitment(
                    local_evolution_count,
                    local_phase_variance,
                    state_data
                )

                if commitment_tx:
                    contract_state['last_commitment_tx'] = commitment_tx

            return contract_state

        except Exception as e:
            logger.error(f"Failed to sync with contract: {e}")
            return None

def create_hdgl_ethereum_integration(config):
    """Factory function to create HDGL Ethereum integration"""
    return HDGLEthereumIntegration(config)