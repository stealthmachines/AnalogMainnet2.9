const express = require('express');
const app = express();
const http = require('http').createServer(app);
const io = require('socket.io')(http);
const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');

// Serve static files
app.use(express.static('static'));
app.use(express.json());

// Store metrics history
let metricsHistory = [];
const MAX_HISTORY = 1000;

// Get HDGL metrics from shared volume
function getHDGLMetrics() {
    try {
        const data = fs.readFileSync('/app/data/metrics.json');
        return JSON.parse(data);
    } catch (err) {
        console.error('Error reading metrics:', err);
        return {};
    }
}

// Socket.IO connection handling
io.on('connection', (socket) => {
    console.log('Client connected');

    // Send initial history
    socket.emit('history', metricsHistory);

    socket.on('disconnect', () => {
        console.log('Client disconnected');
    });
});

// Update metrics every second
setInterval(() => {
    const metrics = getHDGLMetrics();

    // Add timestamp
    metrics.timestamp = Date.now();

    // Add to history
    metricsHistory.push(metrics);
    if (metricsHistory.length > MAX_HISTORY) {
        metricsHistory.shift();
    }

    // Broadcast to all clients
    io.emit('metrics', metrics);
}, 1000);

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'templates', 'stats', 'index.html'));
});

app.get('/api/metrics', (req, res) => {
    res.json(getHDGLMetrics());
});

app.get('/api/history', (req, res) => {
    res.json(metricsHistory);
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy' });
});

// Start server
const PORT = process.env.PORT || 8080;
http.listen(PORT, () => {
    console.log(`Stats server listening on port ${PORT}`);
});