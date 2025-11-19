# POA Mainnet Candidates

This directory contains two complete POA mainnet deployment options for HDGL Analog integration.

## POA Candidate 1: mainnet/ - HDGL Analog V2.6-3.6 Integration

**Architecture**: Ethereum-centric with HDGL bridge integration
- **Primary Focus**: HDGL analog lattice system with Ethereum/IPFS integration
- **Chain**: Public Ethereum mainnet connection
- **Services**: hdgl-bridge, ipfs, eth-node

**Deployment**:
```bash
cd mainnet/
docker compose up -d
```

## POA Candidate 2: mainnet2/docker-charg1/ - Dedicated ChargNet POA

**Architecture**: Custom 3-node Proof-of-Authority blockchain
- **Primary Focus**: Dedicated private blockchain for HDGL operations
- **Chain**: Custom ChargNet (chainId: 22177)
- **Consensus**: Clique POA with 10-second block time

**Network Topology**:
- **rpc-node**: Public RPC interface (ports 8555/8556)
- **miner1**: POA validator (0x0c177edecb07acf3f4611f27e0449d75b3842c3a)
- **miner2**: POA validator (0x33110d0269afc50f2152211a86592bda5b7b779f)

**Deployment**:
```bash
cd mainnet2/docker-charg1/
docker compose up -d
```

**First Run**: The blockchain data will be generated automatically from genesis block.

## Integration with Main System

Both POA candidates integrate with the main HDGL system:
- Program interface connects to ChargNet POA (port 8555)
- Visualizer shows real-time POA block numbers
- Bridge can commit analog lattice state to POA

## Port Configuration

**Main System**:
- Bridge: 9999
- Web Services: 8080
- IPFS: 5001, 8081
- ETH Node: 8545

**ChargNet POA**:
- RPC Node: 8555, 8556
- Miner1: 8557
- Miner2: 8558

No port conflicts - both systems run simultaneously.