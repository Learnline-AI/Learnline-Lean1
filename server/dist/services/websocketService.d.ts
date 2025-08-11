import { Server as HTTPServer } from 'http';
import { ConnectionState } from '../types/shared';
export declare class WebSocketService {
    private io;
    private connections;
    private pingInterval;
    constructor(httpServer: HTTPServer);
    private initialize;
    private setupSocketEvents;
    private startHealthMonitoring;
    private updateConnectionQuality;
    private handleSocketError;
    emitTranscription(socketId: string, result: any): void;
    emitAIResponse(socketId: string, response: any): void;
    emitTTSAudio(socketId: string, audio: any): void;
    getConnectionState(socketId: string): ConnectionState | undefined;
    getActiveConnections(): number;
    cleanup(): void;
}
//# sourceMappingURL=websocketService.d.ts.map