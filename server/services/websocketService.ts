import { Server as SocketIOServer } from 'socket.io';
import { Server as HTTPServer } from 'http';
import { WebSocketEvents, ConnectionState, AudioChunk } from '../types/shared';

export class WebSocketService {
  private io: SocketIOServer;
  private connections: Map<string, ConnectionState> = new Map();
  private pingInterval: NodeJS.Timeout | undefined;

  constructor(httpServer: HTTPServer) {
    this.io = new SocketIOServer(httpServer, {
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

  private initialize() {
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

  private setupSocketEvents(socket: any) {
    socket.on('audio:start', () => {
      console.log(`Audio session started: ${socket.id}`);
    });

    socket.on('audio:chunk', (chunk: AudioChunk) => {
      this.updateConnectionQuality(socket.id);
      socket.broadcast.emit('audio:processing', { socketId: socket.id, chunk });
    });

    socket.on('audio:end', () => {
      console.log(`Audio session ended: ${socket.id}`);
    });

    socket.on('disconnect', (reason: string) => {
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

    socket.on('error', (error: Error) => {
      console.error(`Socket error for ${socket.id}:`, error);
      this.handleSocketError(socket.id, error);
    });
  }

  private startHealthMonitoring() {
    this.pingInterval = setInterval(() => {
      this.io.sockets.sockets.forEach((socket) => {
        const state = this.connections.get(socket.id);
        if (state) {
          (socket as any).ping();
          
          const timeSinceLastPing = Date.now() - state.lastPingTime;
          if (timeSinceLastPing > 30000) {
            state.quality = 'poor';
          } else if (timeSinceLastPing > 15000) {
            state.quality = 'good';
          } else {
            state.quality = 'excellent';
          }
          
          this.connections.set(socket.id, state);
          socket.emit('connection:status', state.quality);
        }
      });
    }, 10000);
  }

  private updateConnectionQuality(socketId: string) {
    const state = this.connections.get(socketId);
    if (state) {
      state.lastPingTime = Date.now();
      state.quality = 'excellent';
      this.connections.set(socketId, state);
    }
  }

  private handleSocketError(socketId: string, error: Error) {
    const socket = this.io.sockets.sockets.get(socketId);
    if (socket) {
      socket.emit('error', {
        message: 'Connection error occurred',
        code: 'WEBSOCKET_ERROR'
      });
    }
  }

  public emitTranscription(socketId: string, result: any) {
    const socket = this.io.sockets.sockets.get(socketId);
    if (socket) {
      socket.emit('transcription', result);
    }
  }

  public emitAIResponse(socketId: string, response: any) {
    const socket = this.io.sockets.sockets.get(socketId);
    if (socket) {
      socket.emit('ai:response', response);
    }
  }

  public emitTTSAudio(socketId: string, audio: any) {
    const socket = this.io.sockets.sockets.get(socketId);
    if (socket) {
      socket.emit('tts:audio', audio);
    }
  }

  public getConnectionState(socketId: string): ConnectionState | undefined {
    return this.connections.get(socketId);
  }

  public getActiveConnections(): number {
    return this.connections.size;
  }

  public cleanup() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
    }
    this.io.close();
  }
}