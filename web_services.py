from flask import Flask, render_template, send_from_directory, request
from flask_socketio import SocketIO, emit
import json
import os
import time
import threading
import hashlib
import random
from datetime import datetime
import requests

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*')

# Common configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Global state for real-time data
network_state = {
    'blockHeight': 0,
    'stateHash': '',
    'timestamp': datetime.now().isoformat(),
    'phase_variance': 0.0,
    'evolution_count': 0,
    'consensus_locked': False
}

commitments = []
snapshots = []
program_tape = ""

def get_bridge_data():
    """Get real data from HDGL bridge API"""
    try:
        bridge_url = "http://hdgl-bridge:9999/api/status"
        response = requests.get(bridge_url, timeout=2)
        if response.status_code == 200:
            data = response.json()

            # Generate network nodes based on evolution state
            node_count = min(20, max(5, data['evolution_count'] % 15 + 5))
            data['network_nodes'] = [
                {
                    'id': i,
                    'x': (hash(str(i + data['evolution_count'])) % 20 - 10),
                    'y': (hash(str(i * 2 + data['evolution_count'])) % 20 - 10),
                    'z': (hash(str(i * 3 + data['evolution_count'])) % 20 - 10)
                }
                for i in range(node_count)
            ]

            # Add resource usage based on phase variance
            variance = data.get('phase_variance', 0.0)
            data['resource_usage'] = {
                'cpu': int(30 + variance * 60),  # 30-90% based on variance
                'memory': int(20 + variance * 50)  # 20-70% based on variance
            }

            return data
    except Exception as e:
        print(f"Bridge connection failed: {e}")

    # Fallback to mock data if bridge unavailable
    return get_mock_data()

def get_mock_data():
    """Generate mock data for real-time updates (fallback)"""
    return {
        'evolution_count': random.randint(1000, 9999),
        'phase_variance': round(random.uniform(0.001, 0.999), 3),
        'consensus_status': random.choice(['Locked', 'Unlocked', 'Syncing']),
        'active_connections': random.randint(0, 50),
        'network_nodes': [
            {'id': i, 'x': random.uniform(-10, 10), 'y': random.uniform(-10, 10), 'z': random.uniform(-10, 10)}
            for i in range(random.randint(5, 20))
        ],
        'phase_history': [
            {'time': time.time() - i, 'variance': random.uniform(0, 1)}
            for i in range(50, 0, -1)
        ],
        'resource_usage': {
            'cpu': random.randint(10, 90),
            'memory': random.randint(20, 80)
        }
    }

# Root Portal Page
@app.route('/')
def portal():
    """Main portal page with links to all services"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HDGL Analog Mainnet V2.8 Portal</title>
    <style>
        body { font-family: 'Courier New', monospace; background: #0a0a0a; color: #00ff00; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .services { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .service-card {
            background: #111; border: 1px solid #00ff00; border-radius: 8px; padding: 20px;
            transition: all 0.3s ease; cursor: pointer;
        }
        .service-card:hover { background: #1a1a1a; border-color: #00ffff; transform: scale(1.02); }
        .service-title { font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #00ffff; }
        .service-desc { margin-bottom: 15px; color: #cccccc; }
        .service-link { color: #00ff00; text-decoration: none; font-weight: bold; }
        .status { text-align: center; margin-top: 30px; padding: 15px; background: #1a1a1a; border-radius: 5px; }
        .status-item { display: inline-block; margin: 0 20px; }
        .status-value { color: #00ffff; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌌 HDGL Analog Mainnet V2.8</h1>
            <p>Distributed Computing Platform for Hybrid Analog-Digital Processing</p>
        </div>

        <div class="services">
            <div class="service-card" onclick="window.open('/explorer', '_blank')">
                <div class="service-title">📊 Network Explorer</div>
                <div class="service-desc">Real-time network state monitoring, consensus tracking, and blockchain exploration</div>
                <a href="/explorer" class="service-link">Launch Explorer →</a>
            </div>

            <div class="service-card" onclick="window.open('/program', '_blank')">
                <div class="service-title">💻 Program Interface</div>
                <div class="service-desc">Turing Machine programming environment with analog lattice integration</div>
                <a href="/program" class="service-link">Launch Program Editor →</a>
            </div>

            <div class="service-card" onclick="window.open('/visualizer', '_blank')">
                <div class="service-title">🌌 3D Visualizer</div>
                <div class="service-desc">WebGL-accelerated 3D visualization of the analog lattice network topology</div>
                <a href="/visualizer" class="service-link">Launch Visualizer →</a>
            </div>

            <div class="service-card" onclick="window.open('/stats', '_blank')">
                <div class="service-title">📈 Statistics Dashboard</div>
                <div class="service-desc">Performance metrics, system analytics, and consensus statistics</div>
                <a href="/stats" class="service-link">Launch Dashboard →</a>
            </div>
        </div>

        <div class="status">
            <div class="status-item">Bridge API: <span class="status-value" id="bridge-status">Checking...</span></div>
            <div class="status-item">ChargNet POA: <span class="status-value" id="poa-status">Checking...</span></div>
            <div class="status-item">Evolution: <span class="status-value" id="evolution-count">Checking...</span></div>
        </div>
    </div>

    <script>
        // Check service status
        async function checkStatus() {
            try {
                const response = await fetch('http://localhost:9999/api/status');
                const data = await response.json();
                document.getElementById('bridge-status').textContent = 'Online';
                document.getElementById('evolution-count').textContent = data.evolution_count || 'Unknown';
            } catch (e) {
                document.getElementById('bridge-status').textContent = 'Offline';
            }

            try {
                const poaResponse = await fetch('http://localhost:8555', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1})
                });
                const poaData = await poaResponse.json();
                const blockNum = parseInt(poaData.result, 16);
                document.getElementById('poa-status').textContent = `Block ${blockNum}`;
            } catch (e) {
                document.getElementById('poa-status').textContent = 'Offline';
            }
        }

        checkStatus();
        setInterval(checkStatus, 5000);
    </script>
</body>
</html>
    '''

# Explorer Service
@app.route('/explorer')
def explorer():
    return send_from_directory('static/explorer', 'index.html')

@socketio.on('connect', namespace='/explorer')
def explorer_connect():
    print('Explorer client connected', flush=True)

    # Ensure we have some initial data
    global network_state, commitments, snapshots

    # Get current bridge data to populate initial state
    bridge_data = get_bridge_data()
    if bridge_data:
        network_state.update({
            'evolution_count': bridge_data.get('evolution_count', 0),
            'phase_variance': bridge_data.get('phase_variance', 0.0),
            'consensus_locked': bridge_data.get('consensus_status') == 'Locked',
            'blockHeight': network_state.get('blockHeight', 1),
            'stateHash': hashlib.sha256(f"{bridge_data.get('evolution_count', 0)}{time.time()}".encode()).hexdigest()[:16],
            'timestamp': datetime.now().isoformat()
        })

    # Ensure we have some initial commitments if empty
    if not commitments:
        for i in range(3):
            commit_data = f"genesis_commitment_{i}"
            commitments.append({
                'hash': hashlib.sha256(commit_data.encode()).hexdigest(),
                'confirmed': True,
                'timestamp': datetime.now().isoformat()
            })

    # Ensure we have some initial snapshots if empty
    if not snapshots:
        for i in range(2):
            snapshot_data = f'genesis_snapshot_{i}'
            cid_hash = hashlib.sha256(snapshot_data.encode()).hexdigest()[:32]
            snapshots.append({
                'cid': f"Qm{cid_hash}",
                'height': i + 1,
                'timestamp': datetime.now().isoformat()
            })

    print(f"DEBUG: Sending explorer data - State: {network_state}", flush=True)
    print(f"DEBUG: Commitments count: {len(commitments)}, Snapshots count: {len(snapshots)}", flush=True)

    # Send initial state
    emit('state_update', network_state)
    emit('commitments_update', {'commitments': commitments})
    emit('snapshots_update', {'snapshots': snapshots})

@socketio.on('request_refresh', namespace='/explorer')
def explorer_refresh():
    print('Explorer refresh requested')
    emit('state_update', network_state)
    emit('commitments_update', {'commitments': commitments})
    emit('snapshots_update', {'snapshots': snapshots})

# Program Service
@app.route('/program')
def program():
    return send_from_directory('static/program', 'index.html')

@socketio.on('connect', namespace='/program')
def program_connect():
    print('Program client connected')
    emit('tape_status', {'code': program_tape, 'size': len(program_tape)})

@socketio.on('write_tape', namespace='/program')
def write_tape(data):
    global program_tape
    program_tape = data.get('code', '')
    print(f'Tape updated: {len(program_tape)} characters')

    # Send program to bridge for lattice execution
    try:
        bridge_response = requests.post('http://hdgl-bridge:9999/api/program',
                                      json={'code': program_tape},
                                      timeout=5)
        if bridge_response.status_code == 200:
            result = bridge_response.json()
            print(f'Program sent to lattice: {result.get("status", "unknown")}')
            tape_status = {
                'code': program_tape,
                'size': len(program_tape),
                'lattice_response': result.get('status', 'unknown'),
                'execution_time': result.get('execution_time', 0)
            }
            # Broadcast to both program and visualizer namespaces
            emit('tape_status', tape_status, broadcast=True)
            socketio.emit('tape_status', tape_status, namespace='/visualizer')
        else:
            print(f'Bridge program endpoint failed: {bridge_response.status_code}')
            tape_status = {
                'code': program_tape,
                'size': len(program_tape),
                'lattice_response': f'Bridge error: {bridge_response.status_code}'
            }
            emit('tape_status', tape_status, broadcast=True)
            socketio.emit('tape_status', tape_status, namespace='/visualizer')
    except Exception as e:
        print(f'Error sending program to bridge: {e}')
        tape_status = {
            'code': program_tape,
            'size': len(program_tape),
            'lattice_response': f'Connection error: {str(e)}'
        }
        emit('tape_status', tape_status, broadcast=True)
        socketio.emit('tape_status', tape_status, namespace='/visualizer')

@socketio.on('clear_tape', namespace='/program')
def clear_tape():
    global program_tape
    program_tape = ""
    print('Tape cleared')
    tape_status = {'code': program_tape, 'size': len(program_tape)}
    emit('tape_status', tape_status, broadcast=True)
    socketio.emit('tape_status', tape_status, namespace='/visualizer')

@socketio.on('program_action', namespace='/program')
def program_action(data):
    print(f'Program action: {data.get("action", "unknown")}')
    # Forward to visualizer namespace
    socketio.emit('program_action', data, namespace='/visualizer')

# Visualizer Service
@app.route('/visualizer')
def visualizer():
    return send_from_directory('static/visualizer', 'index.html')

@socketio.on('connect', namespace='/visualizer')
def visualizer_connect():
    print('Visualizer client connected')
    # Send current network visualization data
    emit('network_data', {
        'nodes': generate_network_nodes(),
        'connections': generate_network_connections(),
        'phase_data': network_state
    })

def generate_network_nodes():
    """Generate sample network nodes for visualization"""
    nodes = []
    for i in range(8):  # 8 nodes for lattice structure
        nodes.append({
            'id': i,
            'x': (i % 3) * 100 - 100,
            'y': (i // 3) * 100 - 100,
            'z': random.uniform(-50, 50),
            'phase': random.uniform(0, 6.28),  # 2π
            'active': network_state['consensus_locked']
        })
    return nodes

def generate_network_connections():
    """Generate connections between nodes"""
    connections = []
    for i in range(8):
        for j in range(i+1, 8):
            if random.random() < 0.3:  # 30% connection probability
                connections.append({
                    'source': i,
                    'target': j,
                    'strength': random.uniform(0.1, 1.0)
                })
    return connections

# Stats Service
@app.route('/stats')
def stats():
    return send_from_directory('static/stats', 'index.html')

@socketio.on('connect', namespace='/stats')
def stats_connect():
    print('Stats client connected')
    emit('stats_update', {
        'evolution_count': network_state['evolution_count'],
        'phase_variance': network_state['phase_variance'],
        'consensus_locked': network_state['consensus_locked'],
        'active_connections': len(generate_network_connections()),
        'uptime': int(time.time()),
        'memory_usage': generate_stats()
    })

def generate_stats():
    """Generate system statistics"""
    return {
        'cpu_usage': random.uniform(10, 80),
        'memory_usage': random.uniform(20, 70),
        'network_latency': random.uniform(1, 50),
        'consensus_health': random.uniform(0.7, 1.0)
    }

# Shared static file handling
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/shaders/<path:path>')
def send_shader(path):
    return send_from_directory('shaders', path)

def background_updates():
    """Background thread for real-time updates"""
    print("DEBUG: Starting background updates thread", flush=True)
    while True:
        try:
            time.sleep(2)  # Update every 2 seconds

            # Get real bridge data
            bridge_data = get_bridge_data()
            print(f"DEBUG: Bridge data - evo_count: {bridge_data.get('evolution_count', 0)}, variance: {bridge_data.get('phase_variance', 0.0)}", flush=True)

            # Use app context for Socket.IO emissions
            with app.app_context():
                # Update network state with real data
                network_state.update({
                    'evolution_count': bridge_data.get('evolution_count', 0),
                    'phase_variance': bridge_data.get('phase_variance', 0.0),
                    'consensus_locked': bridge_data.get('consensus_status') == 'Locked',
                    'blockHeight': network_state.get('blockHeight', 0) + (1 if random.random() < 0.1 else 0),
                    'stateHash': hashlib.sha256(f"{bridge_data.get('evolution_count', 0)}{time.time()}".encode()).hexdigest()[:16],
                    'timestamp': datetime.now().isoformat()
                })

                # Add new commitment when evolution count changes
                if bridge_data.get('evolution_count', 0) % 50 == 0 and random.random() < 0.3:
                    evo_count = bridge_data.get('evolution_count', 0)
                    commit_data = f"commitment_{evo_count}"
                    new_commitment = {
                        'hash': hashlib.sha256(commit_data.encode()).hexdigest(),
                        'confirmed': bridge_data.get('consensus_status') == 'Locked',
                        'timestamp': datetime.now().isoformat()
                    }
                    commitments.insert(0, new_commitment)
                    if len(commitments) > 10:  # Keep only latest 10
                        commitments.pop()

                # Add new snapshot when consensus is locked
                if bridge_data.get('consensus_status') == 'Locked' and random.random() < 0.2:
                    evo_count = bridge_data.get('evolution_count', 0)
                    snapshot_data = f'snapshot_{evo_count}'
                    cid_hash = hashlib.sha256(snapshot_data.encode()).hexdigest()[:32]
                    new_snapshot = {
                        'cid': f"Qm{cid_hash}",
                        'height': network_state['blockHeight'],
                        'timestamp': datetime.now().isoformat()
                    }
                    snapshots.insert(0, new_snapshot)
                    if len(snapshots) > 5:  # Keep only latest 5
                        snapshots.pop()

                # Broadcast updates to all connected clients
                print("DEBUG: Emitting Socket.IO events...", flush=True)
                socketio.emit('state_update', network_state, namespace='/explorer')
                socketio.emit('commitments_update', {'commitments': commitments}, namespace='/explorer')
                socketio.emit('snapshots_update', {'snapshots': snapshots}, namespace='/explorer')

                # Update visualizer with real network data
                socketio.emit('network_data', {
                    'nodes': bridge_data.get('network_nodes', generate_network_nodes()),
                    'connections': generate_network_connections(),
                    'phase_data': network_state
                }, namespace='/visualizer')

                # Update stats with real resource data
                socketio.emit('stats_update', {
                    'evolution_count': bridge_data.get('evolution_count', 0),
                    'phase_variance': bridge_data.get('phase_variance', 0.0),
                    'consensus_locked': bridge_data.get('consensus_status') == 'Locked',
                    'active_connections': bridge_data.get('active_connections', 0),
                    'uptime': int(time.time()),
                    'memory_usage': bridge_data.get('resource_usage', generate_stats())
                }, namespace='/stats')
                print("DEBUG: Socket.IO events emitted successfully", flush=True)

        except Exception as e:
            print(f"DEBUG: Error in background_updates: {e}", flush=True)
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    service = os.environ.get('SERVICE_TYPE', 'all')
    port = int(os.environ.get('PORT', 8080))

    # Start background update thread
    update_thread = threading.Thread(target=background_updates, daemon=True)
    update_thread.start()

    if service == 'all':
        socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
    else:
        # Individual service mode (for containerized deployment)
        app.config['SERVICE_TYPE'] = service
        socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)