"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.WebSocketService = void 0;
const socket_io_1 = require("socket.io");
class WebSocketService {
    constructor(httpServer) {
        this.connections = new Map();
        this.io = new socket_io_1.Server(httpServer, {
            cors: {
                origin: process.env.CLIENT_URL || 'http://localhost:5173',
                methods: ['GET', 'POST'],
                credentials: true
            },
            pingTimeout: 60000,
            pingInterval: 25000
        });
        this.initialize();
        this.startHealthMonitoring();
    }
    initialize() {
        this.io.on('connection', (socket) => {
            console.log(`Client connected: ${socket.id}`);
            this.connections.set(socket.id, {
                isConnected: true,
                reconnectAttempts: 0,
                lastPingTime: Date.now(),
                quality: 'excellent'
            });
            this.setupSocketEvents(socket);
            socket.emit('connection:status', 'connected');
        });
    }
    setupSocketEvents(socket) {
        socket.on('audio:start', () => {
            console.log(`Audio session started: ${socket.id}`);
        });
        socket.on('audio:chunk', (chunk) => {
            this.updateConnectionQuality(socket.id);
            socket.broadcast.emit('audio:processing', { socketId: socket.id, chunk });
        });
        socket.on('audio:end', () => {
            console.log(`Audio session ended: ${socket.id}`);
        });
        socket.on('disconnect', (reason) => {
            console.log(`Client disconnected: ${socket.id}, reason: ${reason}`);
            this.connections.delete(socket.id);
        });
        socket.on('pong', () => {
            const state = this.connections.get(socket.id);
            if (state) {
                state.lastPingTime = Date.now();
                this.connections.set(socket.id, state);
            }
        });
        socket.on('error', (error) => {
            console.error(`Socket error for ${socket.id}:`, error);
            this.handleSocketError(socket.id, error);
        });
    }
    startHealthMonitoring() {
        this.pingInterval = setInterval(() => {
            this.io.sockets.sockets.forEach((socket) => {
                const state = this.connections.get(socket.id);
                if (state) {
                    socket.ping();
                    const timeSinceLastPing = Date.now() - state.lastPingTime;
                    if (timeSinceLastPing > 30000) {
                        state.quality = 'poor';
                    }
                    else if (timeSinceLastPing > 15000) {
                        state.quality = 'good';
                    }
                    else {
                        state.quality = 'excellent';
                    }
                    this.connections.set(socket.id, state);
                    socket.emit('connection:status', state.quality);
                }
            });
        }, 10000);
    }
    updateConnectionQuality(socketId) {
        const state = this.connections.get(socketId);
        if (state) {
            state.lastPingTime = Date.now();
            state.quality = 'excellent';
            this.connections.set(socketId, state);
        }
    }
    handleSocketError(socketId, error) {
        const socket = this.io.sockets.sockets.get(socketId);
        if (socket) {
            socket.emit('error', {
                message: 'Connection error occurred',
                code: 'WEBSOCKET_ERROR'
            });
        }
    }
    emitTranscription(socketId, result) {
        const socket = this.io.sockets.sockets.get(socketId);
        if (socket) {
            socket.emit('transcription', result);
        }
    }
    emitAIResponse(socketId, response) {
        const socket = this.io.sockets.sockets.get(socketId);
        if (socket) {
            socket.emit('ai:response', response);
        }
    }
    emitTTSAudio(socketId, audio) {
        const socket = this.io.sockets.sockets.get(socketId);
        if (socket) {
            socket.emit('tts:audio', audio);
        }
    }
    getConnectionState(socketId) {
        return this.connections.get(socketId);
    }
    getActiveConnections() {
        return this.connections.size;
    }
    cleanup() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
        }
        this.io.close();
    }
}
exports.WebSocketService = WebSocketService;
//# sourceMappingURL=websocketService.js.map