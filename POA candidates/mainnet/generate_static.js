const fs = require('fs');
const path = require('path');

// Create directories if they don't exist
function ensureDir(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
}
function generateProgramFiles() {
    const programHtml = `<!DOCTYPE html>
<html>
<head>
    <title>HDGL Program Interface</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.43.0/min/vs/editor/editor.main.min.css" rel="stylesheet">
    <script src="/socket.io/socket.io.js"></script>
    <style>
        body { margin: 0; display: flex; flex-direction: column; height: 100vh; }
        #editor { flex-grow: 1; border: none; }
        .controls {
            padding: 10px;
            background: #1e1e1e;
            display: flex;
            gap: 10px;
        }
        button {
            background: #0e639c;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover { background: #1177bb; }
    </style>
</head>
<body>
    <div class="controls">
        <button onclick="sendToTape()">Write to Tape</button>
        <button onclick="clearTape()">Clear Tape</button>
    </div>
    <div id="editor"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.43.0/min/vs/loader.min.js"></script>
    <script>
        require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.43.0/min/vs' }});
        require(['vs/editor/editor.main'], function() {
            window.editor = monaco.editor.create(document.getElementById('editor'), {
                value: '// Write your tape program here\\n',
                language: 'python',
                theme: 'vs-dark',
                automaticLayout: true
            });
        });

        const socket = io();

        function sendToTape() {
            const code = window.editor.getValue();
            socket.emit('write_tape', { code });
        }

        function clearTape() {
            socket.emit('clear_tape');
            window.editor.setValue('// Write your tape program here\\n');
        }

        socket.on('tape_status', function(data) {
            // Handle tape status updates
        });
    </script>
</body>
</html>`;

    ensureDir('static/program');
    fs.writeFileSync('static/program/index.html', programHtml);
}

// Generate templates
function generateTemplates() {
    ensureDir('templates/stats');
    ensureDir('templates/visualizer');
    ensureDir('templates/program');
}

// Generate explorer interface files
function generateExplorerFiles() {
    const explorerHtml = `<!DOCTYPE html>
<html>
<head>
    <title>HDGL Network Explorer</title>
    <script src="/socket.io/socket.io.js"></script>
    <script src="https://cdn.ethers.io/lib/ethers-5.7.2.umd.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f0f0f0;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .hash {
            font-family: monospace;
            word-break: break-all;
            background: #f5f5f5;
            padding: 8px;
            border-radius: 4px;
        }
        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        .status.confirmed { background: #e6ffe6; color: #006600; }
        .status.pending { background: #fff3e6; color: #cc7700; }
    </style>
</head>
<body>
    <h1>HDGL Network Explorer</h1>
    <div class="card">
        <h2>Latest State</h2>
        <div id="latestState">
            <p>Loading...</p>
        </div>
    </div>
    <div class="card">
        <h2>Recent Commitments</h2>
        <div id="commitments">
            <p>Loading...</p>
        </div>
    </div>
    <div class="card">
        <h2>IPFS Snapshots</h2>
        <div id="snapshots">
            <p>Loading...</p>
        </div>
    </div>
    <script>
        const socket = io();

        socket.on('state_update', function(data) {
            document.getElementById('latestState').innerHTML = \`
                <p><strong>Block Height:</strong> \${data.blockHeight}</p>
                <p><strong>State Hash:</strong> <span class="hash">\${data.stateHash}</span></p>
                <p><strong>Last Updated:</strong> \${new Date(data.timestamp).toLocaleString()}</p>
            \`;
        });

        socket.on('commitments_update', function(data) {
            document.getElementById('commitments').innerHTML = data.commitments
                .map(c => \`
                    <div style="margin-bottom: 15px;">
                        <p>
                            <span class="status \${c.confirmed ? 'confirmed' : 'pending'}">
                                \${c.confirmed ? 'Confirmed' : 'Pending'}
                            </span>
                        </p>
                        <p class="hash">\${c.hash}</p>
                        <small>\${new Date(c.timestamp).toLocaleString()}</small>
                    </div>
                \`).join('');
        });

        socket.on('snapshots_update', function(data) {
            document.getElementById('snapshots').innerHTML = data.snapshots
                .map(s => \`
                    <div style="margin-bottom: 15px;">
                        <p><strong>CID:</strong> <span class="hash">\${s.cid}</span></p>
                        <p><strong>Height:</strong> \${s.height}</p>
                        <small>\${new Date(s.timestamp).toLocaleString()}</small>
                    </div>
                \`).join('');
        });
    </script>
</body>
</html>`;

    ensureDir('static/explorer');
    fs.writeFileSync('static/explorer/index.html', explorerHtml);
}

// Run all generators
generateStatsFiles();
generateVisualizerFiles();
generateShaderFiles();
generateProgramFiles();
generateExplorerFiles();
generateTemplates();

// Generate stats dashboard
function generateStatsFiles() {
    const statsHtml = `<!DOCTYPE html>
<html>
<head>
    <title>HDGL Network Statistics</title>
    <script src="/socket.io/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .chart-container {
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <h1>HDGL Network Statistics</h1>
    <div class="chart-container">
        <canvas id="phaseChart"></canvas>
    </div>
    <div class="chart-container">
        <canvas id="consensusChart"></canvas>
    </div>
    <script>
        const socket = io();
        socket.on('stats_update', function(data) {
            // Chart update logic will be handled by stats_server.js
        });
    </script>
</body>
</html>`;

    ensureDir('static/stats');
    fs.writeFileSync('static/stats/index.html', statsHtml);
}

// Generate visualizer files
function generateVisualizerFiles() {
    const visualizerHtml = `<!DOCTYPE html>
<html>
<head>
    <title>HDGL Network Visualizer</title>
    <script src="/socket.io/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.137.0/build/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/gl-matrix@3.4.3/gl-matrix-min.js"></script>
    <style>
        body { margin: 0; overflow: hidden; }
        #container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
        }
    </style>
</head>
<body>
    <div id="container"></div>
    <script>
        const socket = io();
        let scene, camera, renderer;

        function init() {
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            renderer = new THREE.WebGLRenderer();
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById('container').appendChild(renderer.domElement);
        }

        socket.on('state_update', function(data) {
            // Visualization update logic will be handled by visualizer_server.js
        });

        init();
    </script>
</body>
</html>`;

    ensureDir('static/visualizer');
    fs.writeFileSync('static/visualizer/index.html', visualizerHtml);
}

// Generate basic shader files
function generateShaderFiles() {
    const vertexShader = `
uniform float time;
varying vec3 vColor;

void main() {
    vColor = vec3(position.x + 0.5, position.y + 0.5, sin(time) * 0.5 + 0.5);
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}`;

    const fragmentShader = `
varying vec3 vColor;

void main() {
    gl_FragColor = vec4(vColor, 1.0);
}`;

    ensureDir('shaders');
    fs.writeFileSync('shaders/vertex.glsl', vertexShader);
    fs.writeFileSync('shaders/fragment.glsl', fragmentShader);
}

// Create template directories
function generateTemplates() {
    ensureDir('templates/stats');
    ensureDir('templates/visualizer');
}

// Run all generators
generateStatsFiles();
generateVisualizerFiles();
generateShaderFiles();
generateTemplates();

console.log('Static files and templates generated successfully!');