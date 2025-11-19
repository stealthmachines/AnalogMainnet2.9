from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import os
import threading
import time

app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
app.config['SECRET_KEY'] = 'hdgl_secret'
socketio = SocketIO(app)

# Load configuration
with open('config.json') as f:
    config = json.load(f)
    TAPE_SIZE = config['tm_tape_size']

def load_tape():
    try:
        with open('/app/data/tape.json') as f:
            return json.load(f)
    except:
        return [0] * TAPE_SIZE

def save_tape(tape):
    with open('/app/data/tape.json', 'w') as f:
        json.dump(tape, f)

@app.route('/')
def index():
    return app.send_static_file('program/index.html')

@app.route('/api/tape', methods=['GET'])
def get_tape():
    return jsonify(load_tape())

@app.route('/api/tape', methods=['POST'])
def set_tape():
    tape = request.json
    if len(tape) != TAPE_SIZE:
        return jsonify({'error': 'Invalid tape size'}), 400
    save_tape(tape)
    socketio.emit('tape_update', tape)
    return jsonify({'status': 'success'})

@app.route('/api/programs', methods=['GET'])
def list_programs():
    programs = []
    for f in os.listdir('/app/programs'):
        if f.endswith('.json'):
            programs.append(f[:-5])  # Remove .json extension
    return jsonify(programs)

@app.route('/api/programs/<name>', methods=['GET'])
def get_program(name):
    try:
        with open(f'/app/programs/{name}.json') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({'error': 'Program not found'}), 404

@app.route('/api/programs/<name>', methods=['POST'])
def save_program(name):
    program = request.json
    with open(f'/app/programs/{name}.json', 'w') as f:
        json.dump(program, f)
    return jsonify({'status': 'success'})

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

def monitor_tape():
    last_tape = None
    while True:
        time.sleep(1)
        try:
            current_tape = load_tape()
            if current_tape != last_tape:
                socketio.emit('tape_update', current_tape)
                last_tape = current_tape
        except Exception as e:
            print(f"Error monitoring tape: {e}")

if __name__ == '__main__':
    # Start background tasks
    threading.Thread(target=monitor_tape, daemon=True).start()

    # Start server
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)