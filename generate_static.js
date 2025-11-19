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
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
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
                value: \`# HDGL Lattice Demo Script
# Demonstrates lattice field effects using golden ratio mathematics

import math
import time

def lattice_harmonic_demo():
    """Generate harmonic pattern that affects the analog lattice"""
    t = time.time()
    phi = 1.618033988749895  # Golden ratio

    # Create golden spiral pattern
    nodes = []
    for i in range(8):
        angle = i * 2 * math.pi / phi
        radius = math.sqrt(i + 1) * phi

        # Harmonic oscillation
        amplitude = math.sin(angle + t * phi) * math.exp(-radius / 20)

        node_energy = amplitude * phi
        nodes.append(node_energy)

    # Calculate total lattice effect
    total_effect = sum(nodes) * 0.1

    print(f"Lattice nodes: {len(nodes)}")
    print(f"Golden ratio: {phi:.6f}")
    print(f"Lattice effect: {total_effect:.6f}")

    return total_effect

# Execute the demo
result = lattice_harmonic_demo()
print(f"Demo completed with effect: {result:.6f}")
\`,
                language: 'python',
                theme: 'vs-dark',
                automaticLayout: true
            });
        });

        const socket = io('/program');

        function sendToTape() {
            const code = window.editor.getValue();
            console.log('Sending to tape:', code.length, 'characters');
            socket.emit('write_tape', { code });
        }

        function clearTape() {
            socket.emit('clear_tape');
            window.editor.setValue(\`# HDGL Lattice Demo Script
# Demonstrates lattice field effects using golden ratio mathematics

import math
import time

def lattice_harmonic_demo():
    """Generate harmonic pattern that affects the analog lattice"""
    t = time.time()
    phi = 1.618033988749895  # Golden ratio

    # Create golden spiral pattern
    nodes = []
    for i in range(8):
        angle = i * 2 * math.pi / phi
        radius = math.sqrt(i + 1) * phi

        # Harmonic oscillation
        amplitude = math.sin(angle + t * phi) * math.exp(-radius / 20)

        node_energy = amplitude * phi
        nodes.append(node_energy)

    # Calculate total lattice effect
    total_effect = sum(nodes) * 0.1

    print(f"Lattice nodes: {len(nodes)}")
    print(f"Golden ratio: {phi:.6f}")
    print(f"Lattice effect: {total_effect:.6f}")

    return total_effect

# Execute the demo
result = lattice_harmonic_demo()
print(f"Demo completed with effect: {result:.6f}")
\`);
        }

        socket.on('connect', function() {
            console.log('Program interface connected');
        });

        socket.on('tape_status', function(data) {
            console.log('Tape status:', data);
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
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
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
        const socket = io('/explorer');

        socket.on('connect', function() {
            console.log('Explorer connected to /explorer namespace');
        });

        socket.on('state_update', function(data) {
            console.log('State update received:', data);
            document.getElementById('latestState').innerHTML = \`
                <p><strong>Block Height:</strong> \${data.blockHeight}</p>
                <p><strong>State Hash:</strong> <span class="hash">\${data.stateHash}</span></p>
                <p><strong>Evolution Count:</strong> \${data.evolution_count || 0}</p>
                <p><strong>Phase Variance:</strong> \${(data.phase_variance || 0).toFixed(6)}</p>
                <p><strong>Consensus:</strong> \${data.consensus_locked ? 'Locked' : 'Unlocked'}</p>
                <p><strong>Last Updated:</strong> \${new Date(data.timestamp).toLocaleString()}</p>
            \`;
        });

        socket.on('commitments_update', function(data) {
            console.log('Commitments update received:', data);
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
            console.log('Snapshots update received:', data);
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
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
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
    <div id="stats-data">
        <p>Evolution Count: <span id="evolution-count">Connecting...</span></p>
        <p>Phase Variance: <span id="phase-variance">Connecting...</span></p>
        <p>Consensus Status: <span id="consensus-status">Connecting...</span></p>
        <p>Active Connections: <span id="active-connections">Connecting...</span></p>
        <p>Last Update: <span id="last-update">Connecting...</span></p>
    </div>

    <script>
        const socket = io('/stats');

        // Update stats in real-time
        socket.on('stats_update', function(data) {
            console.log('Stats update received:', data);

            document.getElementById('evolution-count').textContent = data.evolution_count || 'N/A';
            document.getElementById('phase-variance').textContent = data.phase_variance ? data.phase_variance.toFixed(8) : 'N/A';
            document.getElementById('consensus-status').textContent = data.consensus_locked ? 'Locked' : 'Unlocked';
            document.getElementById('active-connections').textContent = data.active_connections || '0';
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString();

            // Update page title with current evolution
            document.title = \`HDGL Stats - Evolution \${data.evolution_count || 0}\`;
        });

        socket.on('connect', function() {
            console.log('Socket.IO connected to stats!');
        });

        socket.on('disconnect', function() {
            console.log('Socket.IO disconnected from stats');
            document.getElementById('evolution-count').textContent = 'Disconnected';
            document.getElementById('phase-variance').textContent = 'Disconnected';
            document.getElementById('consensus-status').textContent = 'Disconnected';
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
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌟 HDGL Lattice Field Visualizer 🌟</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e, #16213e);
            color: #ffffff;
            font-family: 'Courier New', monospace;
            overflow: hidden;
            height: 100vh;
        }

        .header {
            position: absolute;
            top: 15px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 100;
            color: #ffd700;
            text-shadow: 0 0 20px #ffd700;
            font-size: 1.8em;
            font-weight: bold;
        }

        .controls {
            position: absolute;
            top: 60px;
            left: 20px;
            z-index: 100;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: rgba(0, 0, 0, 0.7);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255, 215, 0, 0.3);
        }

        .status-panel {
            position: absolute;
            top: 60px;
            right: 20px;
            z-index: 100;
            background: rgba(0, 0, 0, 0.8);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255, 215, 0, 0.5);
            min-width: 200px;
        }

        .lattice-canvas {
            width: 100vw;
            height: 100vh;
            cursor: move;
            background: radial-gradient(circle at 50% 50%, #001122, #000000);
        }

        button {
            background: linear-gradient(135deg, #ffd700, #ffed4e);
            color: #000;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(255, 215, 0, 0.3);
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 215, 0, 0.5);
        }

        select {
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 215, 0, 0.5);
            color: white;
            padding: 8px;
            border-radius: 5px;
        }

        .status-item {
            color: #ffd700;
            margin: 5px 0;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">🌟 HDGL Lattice Field Visualizer 🌟</div>

    <div class="controls">
        <button onclick="resetView()">Reset View</button>
        <select id="visualMode" onchange="changeMode()">
            <option value="lattice">Lattice Network</option>
            <option value="orbital">Orbital Mechanics</option>
            <option value="breathing">Breathing Field</option>
        </select>
        <button onclick="toggleAnimation()">Toggle Animation</button>
    </div>

    <div class="status-panel">
        <div class="status-item">Evolution: <span id="evolution">0</span></div>
        <div class="status-item">Variance: <span id="variance">0.000000</span></div>
        <div class="status-item">Nodes: <span id="nodeCount">0</span></div>
        <div class="status-item">Phase: <span id="phase">0.000</span></div>
        <div class="status-item">Mode: <span id="currentMode">Lattice</span></div>
    </div>

    <canvas id="latticeCanvas" class="lattice-canvas"></canvas>

    <script>
        const socket = io('/visualizer');

        // Constants inspired by enhanced_pot_visualizer2.html
        const PHI = 1.618033988749895;
        const INV_PHI = 1 / PHI;
        const GOLDEN_ANGLE = 2 * Math.PI * INV_PHI;

        class HDGLLatticeVisualizer {
            constructor() {
                this.canvas = document.getElementById('latticeCanvas');
                this.ctx = this.canvas.getContext('2d');
                this.setupCanvas();

                this.transform = { scale: 1, translateX: 0, translateY: 0, rotation: 0 };
                this.animationPhase = 0;
                this.isAnimating = true;
                this.visualMode = 'lattice';
                this.networkData = { nodes: [], phase_data: {} };
                this.selectedNode = null;
                this.glyphData = [];

                // DNA mapping system inspired by enhanced_pot_visualizer2.html
                this.DNA_MAP = ['A', 'G', 'T', 'C'];
                this.ternaryStates = [-1, 0, 1]; // Ternary system

                this.setupEventListeners();
                this.generateInitialGlyphs();
                this.animate();
            }            setupCanvas() {
                this.canvas.width = window.innerWidth * devicePixelRatio;
                this.canvas.height = window.innerHeight * devicePixelRatio;
                this.ctx.scale(devicePixelRatio, devicePixelRatio);
                this.canvasWidth = window.innerWidth;
                this.canvasHeight = window.innerHeight;
            }

            setupEventListeners() {
                let isDragging = false;
                let lastX, lastY;

                this.canvas.addEventListener('mousedown', (e) => {
                    isDragging = true;
                    lastX = e.clientX;
                    lastY = e.clientY;

                    // Check for node selection
                    const rect = this.canvas.getBoundingClientRect();
                    const mouseX = ((e.clientX - rect.left) - this.canvasWidth/2 - this.transform.translateX) / this.transform.scale;
                    const mouseY = ((e.clientY - rect.top) - this.canvasHeight/2 - this.transform.translateY) / this.transform.scale;

                    this.selectedNode = this.findNodeAt(mouseX, mouseY);
                    if (this.selectedNode) {
                        this.displayNodeInfo(this.selectedNode);
                    }
                });

                this.canvas.addEventListener('mousemove', (e) => {
                    if (isDragging && !this.selectedNode) {
                        const dx = (e.clientX - lastX) / this.transform.scale;
                        const dy = (e.clientY - lastY) / this.transform.scale;
                        this.transform.translateX += dx;
                        this.transform.translateY += dy;
                        lastX = e.clientX;
                        lastY = e.clientY;
                    }
                });

                this.canvas.addEventListener('mouseup', () => {
                    isDragging = false;
                    this.selectedNode = null;
                });

                this.canvas.addEventListener('wheel', (e) => {
                    e.preventDefault();
                    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
                    this.transform.scale *= zoomFactor;
                    this.transform.scale = Math.max(0.1, Math.min(5, this.transform.scale));
                });

                window.addEventListener('resize', () => this.setupCanvas());
            }            updateNetworkData(data) {
                this.networkData = data;
                if (data.phase_data) {
                    document.getElementById('evolution').textContent = data.phase_data.evolution_count || 0;
                    document.getElementById('variance').textContent = (data.phase_data.phase_variance || 0).toFixed(6);
                    document.getElementById('phase').textContent = ((data.phase_data.phase_variance || 0) % 1).toFixed(3);
                }
                document.getElementById('nodeCount').textContent = (data.nodes || []).length;

                // Regenerate glyphs when data changes significantly
                if (this.glyphData.length === 0 ||
                    Math.abs((data.phase_data?.evolution_count || 0) - this.lastEvolutionCount) > 10) {
                    this.generateInitialGlyphs();
                    this.lastEvolutionCount = data.phase_data?.evolution_count || 0;
                }
            }

            // Advanced glyph generation inspired by enhanced_pot_visualizer2.html
            async generateEphemeralDNA64(seed, opId, idx, length) {
                const data = seed.toString() + opId + idx + "DNA64";
                const encoder = new TextEncoder();
                const hashBuffer = await crypto.subtle.digest('SHA-256', encoder.encode(data));
                const hashArray = new Uint8Array(hashBuffer);

                let dna = '';
                for (let i = 0; dna.length < length && i < hashArray.length; i++) {
                    const b = hashArray[i];
                    dna += this.DNA_MAP[b & 0x03];
                    dna += this.DNA_MAP[(b >> 2) & 0x03];
                    dna += this.DNA_MAP[(b >> 4) & 0x03];
                    dna += this.DNA_MAP[(b >> 6) & 0x03];
                }
                return dna.substring(0, length);
            }

            generateInitialGlyphs() {
                this.glyphData = [];
                const evolution = this.networkData.phase_data?.evolution_count || 0;
                const variance = this.networkData.phase_data?.phase_variance || 1.123;

                // Generate glyphs using golden ratio spacing
                const glyphCount = 21; // Fibonacci number
                for (let i = 0; i < glyphCount; i++) {
                    const angle = i * GOLDEN_ANGLE;
                    const radius = Math.sqrt(i + 1) * 25;
                    const phase = (evolution + i * variance) % (2 * Math.PI);
                    const ternary = this.ternaryStates[Math.floor(phase % 3)];

                    this.glyphData.push({
                        id: i,
                        x: Math.cos(angle) * radius,
                        y: Math.sin(angle) * radius,
                        angle: angle,
                        radius: radius,
                        phase: phase,
                        ternary: ternary,
                        energy: PHI ** (i % 3),
                        dna64: '', // Will be generated async
                        selected: false
                    });
                }

                // Generate DNA sequences asynchronously
                this.generateDNASequences();
            }

            async generateDNASequences() {
                const evolution = this.networkData.phase_data?.evolution_count || 0;
                for (let i = 0; i < this.glyphData.length; i++) {
                    this.glyphData[i].dna64 = await this.generateEphemeralDNA64(evolution, 'lattice', i, 64);
                }
            }

            findNodeAt(x, y) {
                for (let glyph of this.glyphData) {
                    const dx = x - glyph.x;
                    const dy = y - glyph.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    if (distance < 15) { // Hit radius
                        return glyph;
                    }
                }
                return null;
            }

            displayNodeInfo(glyph) {
                // Update status panel with glyph information
                const statusPanel = document.querySelector('.status-panel');
                statusPanel.innerHTML = \`
                    <div class="status-item">Glyph ID: \${glyph.id}</div>
                    <div class="status-item">Ternary: \${glyph.ternary}</div>
                    <div class="status-item">Phase: \${glyph.phase.toFixed(3)}</div>
                    <div class="status-item">Energy: \${glyph.energy.toFixed(3)}</div>
                    <div class="status-item">DNA: \${glyph.dna64.substring(0, 8)}...</div>
                    <div class="status-item">Radius: \${glyph.radius.toFixed(1)}</div>
                \`;
                glyph.selected = true;
                setTimeout(() => glyph.selected = false, 2000); // Clear selection after 2s
            }

            animate() {
                if (this.isAnimating) {
                    this.animationPhase += 0.02;
                }

                this.render();
                requestAnimationFrame(() => this.animate());
            }

            render() {
                this.ctx.clearRect(0, 0, this.canvasWidth, this.canvasHeight);

                // Apply transformations
                this.ctx.save();
                this.ctx.translate(this.canvasWidth / 2, this.canvasHeight / 2);
                this.ctx.scale(this.transform.scale, this.transform.scale);
                this.ctx.translate(this.transform.translateX, this.transform.translateY);
                this.ctx.rotate(this.transform.rotation);

                switch (this.visualMode) {
                    case 'lattice':
                        this.renderLatticeNetwork();
                        break;
                    case 'orbital':
                        this.renderOrbitalMechanics();
                        break;
                    case 'breathing':
                        this.renderBreathingField();
                        break;
                }

                this.ctx.restore();
            }

            renderLatticeNetwork() {
                const centerX = 0, centerY = 0;
                const evolution = this.networkData.phase_data?.evolution_count || 0;
                const variance = this.networkData.phase_data?.phase_variance || 1.123;

                // Draw central hub with breathing effect
                const hubRadius = 15 + 5 * Math.sin(this.animationPhase * 0.618);
                const hubColor = this.networkData.phase_data?.consensus_locked ? '#00ff88' : '#ff6b6b';

                this.ctx.fillStyle = hubColor;
                this.ctx.strokeStyle = '#ffd700';
                this.ctx.lineWidth = 2;
                this.ctx.beginPath();
                this.ctx.arc(centerX, centerY, hubRadius, 0, 2 * Math.PI);
                this.ctx.fill();
                this.ctx.stroke();

                // Render advanced glyphs with DNA and ternary systems
                this.glyphData.forEach((glyph, i) => {
                    // Update glyph position with breathing
                    const breathingFactor = 1 + 0.2 * Math.sin(this.animationPhase * 0.5 + glyph.phase);
                    const glyphX = glyph.x * breathingFactor;
                    const glyphY = glyph.y * breathingFactor;

                    // Ternary-based color selection
                    let glyphColor;
                    switch (glyph.ternary) {
                        case -1: glyphColor = '#ff4757'; break; // Red
                        case 0:  glyphColor = '#2ed573'; break; // Green
                        case 1:  glyphColor = '#3742fa'; break; // Blue
                        default: glyphColor = '#ffd700'; break; // Gold
                    }

                    // Glyph radius based on energy and breathing
                    const glyphRadius = (5 + glyph.energy * 2) * breathingFactor;

                    // Draw connection to center with DNA-influenced opacity
                    const dnaInfluence = glyph.dna64.length > 0 ?
                        (glyph.dna64.charCodeAt(0) % 100) / 100 : 0.5;
                    this.ctx.strokeStyle = \`\${glyphColor}\${Math.floor(dnaInfluence * 255).toString(16).padStart(2, '0')}\`;
                    this.ctx.lineWidth = 1 + dnaInfluence;
                    this.ctx.beginPath();
                    this.ctx.moveTo(centerX, centerY);
                    this.ctx.lineTo(glyphX, glyphY);
                    this.ctx.stroke();

                    // Draw main glyph with selection highlighting
                    if (glyph.selected) {
                        // Selection highlight
                        this.ctx.fillStyle = 'rgba(255, 215, 0, 0.3)';
                        this.ctx.strokeStyle = '#ffd700';
                        this.ctx.lineWidth = 3;
                        this.ctx.beginPath();
                        this.ctx.arc(glyphX, glyphY, glyphRadius * 1.5, 0, 2 * Math.PI);
                        this.ctx.fill();
                        this.ctx.stroke();
                    }

                    // Main glyph body
                    this.ctx.fillStyle = glyphColor;
                    this.ctx.beginPath();
                    this.ctx.arc(glyphX, glyphY, glyphRadius, 0, 2 * Math.PI);
                    this.ctx.fill();

                    // DNA pattern overlay - draw nucleotide dots
                    if (glyph.dna64.length > 0) {
                        const nucleotides = glyph.dna64.substring(0, 8);
                        for (let n = 0; n < nucleotides.length; n++) {
                            const nucleotide = nucleotides[n];
                            const dotAngle = (n / nucleotides.length) * 2 * Math.PI;
                            const dotRadius = glyphRadius * 0.7;
                            const dotX = glyphX + Math.cos(dotAngle) * dotRadius;
                            const dotY = glyphY + Math.sin(dotAngle) * dotRadius;

                            // DNA color coding
                            let nucleotideColor;
                            switch (nucleotide) {
                                case 'A': nucleotideColor = '#ff6b35'; break; // Adenine - Orange
                                case 'T': nucleotideColor = '#3742fa'; break; // Thymine - Blue
                                case 'G': nucleotideColor = '#2ed573'; break; // Guanine - Green
                                case 'C': nucleotideColor = '#ff3838'; break; // Cytosine - Red
                                default:  nucleotideColor = '#ffffff'; break;
                            }

                            this.ctx.fillStyle = nucleotideColor;
                            this.ctx.beginPath();
                            this.ctx.arc(dotX, dotY, 2, 0, 2 * Math.PI);
                            this.ctx.fill();
                        }
                    }

                    // Ternary state indicator
                    this.ctx.fillStyle = '#ffffff';
                    this.ctx.font = '12px monospace';
                    this.ctx.textAlign = 'center';
                    this.ctx.fillText(glyph.ternary.toString(), glyphX, glyphY + 4);

                    // Glow effect
                    const gradient = this.ctx.createRadialGradient(glyphX, glyphY, 0, glyphX, glyphY, glyphRadius * 3);
                    gradient.addColorStop(0, \`\${glyphColor}44\`);
                    gradient.addColorStop(1, 'transparent');
                    this.ctx.fillStyle = gradient;
                    this.ctx.beginPath();
                    this.ctx.arc(glyphX, glyphY, glyphRadius * 3, 0, 2 * Math.PI);
                    this.ctx.fill();
                });
            }

            renderOrbitalMechanics() {
                const nodes = this.networkData.nodes || [];
                const evolution = this.networkData.phase_data?.evolution_count || 0;
                const variance = this.networkData.phase_data?.phase_variance || 1.123;

                // Multiple orbital rings
                const rings = 5;
                for (let ring = 0; ring < rings; ring++) {
                    const ringRadius = 50 + ring * 40;
                    const nodesInRing = Math.max(1, Math.floor(nodes.length / rings));
                    const ringSpeed = (ring + 1) * 0.005 * (variance - 1);

                    for (let n = 0; n < nodesInRing && ring * nodesInRing + n < nodes.length; n++) {
                        const angle = (n / nodesInRing) * 2 * Math.PI + this.animationPhase * ringSpeed;
                        const x = Math.cos(angle) * ringRadius;
                        const y = Math.sin(angle) * ringRadius;

                        const nodeIndex = ring * nodesInRing + n;
                        const nodeRadius = 3 + (nodeIndex % 5);
                        const orbitalBreathe = 1 + 0.2 * Math.sin(this.animationPhase + nodeIndex);

                        // Draw orbital trail
                        this.ctx.strokeStyle = \`hsl(\${ring * 60 + 30}, 50%, 40%)\`;
                        this.ctx.lineWidth = 0.5;
                        this.ctx.beginPath();
                        this.ctx.arc(0, 0, ringRadius, 0, 2 * Math.PI);
                        this.ctx.stroke();

                        // Draw orbiting node
                        this.ctx.fillStyle = \`hsl(\${ring * 60 + 30}, 70%, 60%)\`;
                        this.ctx.beginPath();
                        this.ctx.arc(x, y, nodeRadius * orbitalBreathe, 0, 2 * Math.PI);
                        this.ctx.fill();
                    }
                }
            }

            renderBreathingField() {
                const nodes = this.networkData.nodes || [];
                const variance = this.networkData.phase_data?.phase_variance || 1.123;

                // Global breathing rhythm
                const globalBreathe = 1 + 0.4 * Math.sin(this.animationPhase * 0.618);

                // Create breathing hexagonal grid
                const gridSize = 40;
                const rows = 15;
                const cols = 20;

                for (let row = -rows/2; row < rows/2; row++) {
                    for (let col = -cols/2; col < cols/2; col++) {
                        const x = col * gridSize + (row % 2) * (gridSize/2);
                        const y = row * gridSize * 0.866; // hexagonal spacing

                        const distance = Math.sqrt(x*x + y*y);
                        const wave = Math.sin(distance * 0.01 - this.animationPhase * 0.1);
                        const localBreathe = globalBreathe * (1 + 0.3 * wave);

                        const cellRadius = 8 * localBreathe;
                        const intensity = Math.max(0, 1 - distance / 400);

                        if (intensity > 0) {
                            // Breathing cell with variance-influenced color
                            const hue = (variance * 100 + wave * 30) % 360;
                            this.ctx.fillStyle = \`hsla(\${hue}, 60%, 50%, \${intensity * 0.6})\`;
                            this.ctx.beginPath();
                            this.ctx.arc(x, y, cellRadius, 0, 2 * Math.PI);
                            this.ctx.fill();
                        }
                    }
                }
            }
        }

        // Global functions
        let visualizer;

        function resetView() {
            if (visualizer) {
                visualizer.transform = { scale: 1, translateX: 0, translateY: 0, rotation: 0 };
            }
        }

        function changeMode() {
            const mode = document.getElementById('visualMode').value;
            if (visualizer) {
                visualizer.visualMode = mode;
                document.getElementById('currentMode').textContent = mode.charAt(0).toUpperCase() + mode.slice(1);
            }
        }

        function toggleAnimation() {
            if (visualizer) {
                visualizer.isAnimating = !visualizer.isAnimating;
            }
        }

        // Socket.IO connections
        socket.on('connect', function() {
            console.log('HDGL Lattice Visualizer connected!');
        });

        socket.on('network_data', function(data) {
            console.log('Lattice data received:', data);
            if (visualizer) {
                visualizer.updateNetworkData(data);
            }
        });

        // Initialize visualizer
        document.addEventListener('DOMContentLoaded', function() {
            visualizer = new HDGLLatticeVisualizer();
        });
    </script>
</body>
</html>`;

    ensureDir('static/visualizer');
    fs.writeFileSync('static/visualizer/index.html', visualizerHtml);
}// Generate basic shader files
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