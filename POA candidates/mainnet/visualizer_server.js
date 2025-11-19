const express = require('express');
const app = express();
const http = require('http').createServer(app);
const io = require('socket.io')(http);
const fs = require('fs');
const path = require('path');

// Serve static files from absolute paths
app.use(express.static(path.join(__dirname, 'static')));
app.use('/shaders', express.static(path.join(__dirname, 'shaders')));

// Serve index.html
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'static', 'visualizer', 'index.html'));
});

// Store lattice state
let currentState = null;

// Default state
const defaultState = {
    dimensions: [1,1,1,1,1,1,1,1],
    phases: [0,0,0,0,0,0,0,0],
    tape: [0,0,0,0,0,0,0,0],
    timestamp: 0
};

// Read state file
function readLatticeState() {
    try {
        const data = fs.readFileSync('/app/data/state.json', 'utf8');
        return JSON.parse(data);
    } catch (err) {
        console.error('Error reading state:', err);

        // Create default state file if it doesn't exist
        try {
            fs.writeFileSync('/app/data/state.json', JSON.stringify(defaultState), 'utf8');
            return defaultState;
        } catch (writeErr) {
            console.error('Error writing default state:', writeErr);
            return null;
        }
    }
}

// Socket.IO connection handling
io.on('connection', (socket) => {
    console.log('Client connected');

    // Send initial state
    if (currentState) {
        socket.emit('state', currentState);
    }

    socket.on('disconnect', () => {
        console.log('Client disconnected');
    });
});

// Update state every frame (~60fps)
setInterval(() => {
    const newState = readLatticeState();
    if (newState && JSON.stringify(newState) !== JSON.stringify(currentState)) {
        currentState = newState;
        io.emit('state', currentState);
    }
}, 16);

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'visualizer', 'index.html'));
});

app.get('/api/state', (req, res) => {
    const state = readLatticeState();
    if (state) {
        res.json(state);
    } else {
        res.status(500).json({ error: 'Could not read state' });
    }
});

// Shader routes
app.get('/api/shaders/vertex', (req, res) => {
    res.sendFile(path.join(__dirname, 'shaders', 'lattice.vert'));
});

app.get('/api/shaders/fragment', (req, res) => {
    res.sendFile(path.join(__dirname, 'shaders', 'lattice.frag'));
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

// Start server
const PORT = process.env.PORT || 8080;
http.listen(PORT, () => {
    console.log(`Visualizer server listening on port ${PORT}`);
});