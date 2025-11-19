from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import ipfshttpclient
from web3 import Web3
import json
import os
import threading
import time
try:
    import requests
except Exception:
    requests = None

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hdgl_secret'
socketio = SocketIO(app)


# Lightweight HTTP-based IPFS fallback wrapper. Only implements the parts we
# need (cat). It tries a list of HTTP API endpoints until one works.
class SimpleIPFS:
    def __init__(self, hosts):
        # hosts: list of base URLs, e.g. ['http://ipfs:5001', 'http://127.0.0.1:5001']
        self.hosts = hosts

    def cat(self, cid):
        last_exc = None
        for host in self.hosts:
            try:
                if requests is None:
                    raise Exception('requests library not available for HTTP IPFS fallback')
                url = host.rstrip('/') + '/api/v0/cat'
                # use a POST with params as the HTTP API expects
                resp = requests.post(url, params={'arg': cid}, timeout=10)
                resp.raise_for_status()
                return resp.content
            except Exception as e:
                last_exc = e
                continue
        raise Exception(f"HTTP IPFS cat failed for {cid}: {last_exc}")


# Connect to IPFS (with retry). If ipfshttpclient rejects the daemon version
# (for example older daemon 0.38.x), fall back to using the HTTP API wrapper
# which is more tolerant.
def connect_ipfs():
    while True:
        try:
            return ipfshttpclient.connect('/dns/ipfs/tcp/5001')
        except Exception as e:
            msg = str(e)
            # Detect the specific unsupported-daemon-version error and fall back
            if 'Unsupported daemon version' in msg or 'not in range' in msg:
                print(f"Failed to connect to IPFS via ipfshttpclient: {e}. Falling back to HTTP API.")
                # Try a few common API hosts - these can be adjusted if your
                # docker-compose service name for IPFS is different.
                hosts = ['http://ipfs:5001', 'http://127.0.0.1:5001', 'http://localhost:5001']
                return SimpleIPFS(hosts)
            else:
                print(f"Failed to connect to IPFS: {e}")
                time.sleep(5)


ipfs = connect_ipfs()

# Connect to Ethereum node
w3 = Web3(Web3.HTTPProvider('http://eth-node:8546'))

# Load contract ABI
with open('config.json') as f:
    config = json.load(f)
    contract_address = config['eth_contract']

def load_snapshots():
    try:
        with open('/app/data/snapshots.json') as f:
            return json.load(f)
    except:
        return []

@app.route('/')
def index():
    return render_template('explorer/index.html')

@app.route('/api/snapshots')
def get_snapshots():
    return jsonify(load_snapshots())

@app.route('/api/state/<snapshot_hash>')
def get_state(snapshot_hash):
    try:
        data = ipfs.cat(snapshot_hash)
        # ipfshttpclient returns bytes for cat; our HTTP fallback also returns bytes.
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        return jsonify(json.loads(data))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/commits')
def get_commits():
    # Get Ethereum commitments
    # Implementation depends on contract ABI
    commits = []
    return jsonify(commits)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

def update_snapshots():
    while True:
        time.sleep(10)
        try:
            # Get latest snapshots from IPFS
            snapshots = load_snapshots()
            socketio.emit('snapshots', snapshots)
        except Exception as e:
            print(f"Error updating snapshots: {e}")

if __name__ == '__main__':
    # Start background tasks
    threading.Thread(target=update_snapshots, daemon=True).start()

    # Start server
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port)