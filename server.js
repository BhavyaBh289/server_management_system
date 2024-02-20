const express = require('express');
const http = require('http');
const path = require('path');
const pty = require('node-pty');
const { Server } = require('ws');

const app = express();
const server = http.createServer(app);
const wss = new Server({ noServer: true });

// Serve static files
app.use(express.static(__dirname));

// WebSocket connection for PTY terminals
wss.on('connection', (ws) => {
    const term = pty.spawn('bash', [], {
        name: 'xterm-color',
        cols: 80,
        rows: 24,
        cwd: process.env.HOME,
        env: process.env,
    });

    term.on('data', (data) => ws.send(data));
    term.on('exit', () => ws.close());

    ws.on('message', (msg) => term.write(msg));
    ws.on('close', () => term.kill());
});

// Upgrade HTTP to WebSocket connection
server.on('upgrade', (request, socket, head) => {
    wss.handleUpgrade(request, socket, head, (ws) => {
        wss.emit('connection', ws, request);
    });
});

// Start HTTP server
const PORT = process.env.PORT || 3000;

// Handle other routes by serving the index.html file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname,  'index.html'));
});

server.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
