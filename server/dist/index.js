"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const http_1 = require("http");
const cors_1 = __importDefault(require("cors"));
const dotenv_1 = __importDefault(require("dotenv"));
const path_1 = __importDefault(require("path"));
const websocketService_1 = require("./services/websocketService");
const vadService_1 = require("./services/vadService");
const spectralGating_1 = require("./services/spectralGating");
const sttWorker_1 = require("./workers/sttWorker");
const aiService_1 = require("./services/aiService");
const ttsService_1 = require("./services/ttsService");
const audioUtils_1 = require("./utils/audioUtils");
const aiConfig_1 = require("./config/aiConfig");
dotenv_1.default.config();
const app = (0, express_1.default)();
const server = (0, http_1.createServer)(app);
const PORT = process.env.PORT || 3001;
app.use((0, cors_1.default)({
    origin: process.env.CLIENT_URL || 'http://localhost:5173',
    credentials: true
}));
app.use(express_1.default.json());
app.use(express_1.default.static(path_1.default.join(__dirname, '../../client/dist')));
class VoiceChatServer {
    constructor() {
        this.audioBuffer = new Map();
        this.conversationHistory = new Map();
        this.wsService = new websocketService_1.WebSocketService(server);
        this.vadService = new vadService_1.VADService();
        this.spectralGating = new spectralGating_1.SpectralGatingService();
        this.sttWorker = new sttWorker_1.STTWorker();
        this.aiService = new aiService_1.AIService();
        this.ttsService = new ttsService_1.TTSService();
        this.initialize();
    }
    async initialize() {
        console.log('🚀 Initializing Voice Chat Server...');
        if (!(0, aiConfig_1.validateAIConfig)()) {
            console.error('❌ AI configuration validation failed');
            process.exit(1);
        }
        try {
            await this.vadService.initialize();
            console.log('✅ VAD Service initialized');
        }
        catch (error) {
            console.warn('⚠️ VAD initialization failed, using fallback:', error);
        }
        this.setupWebSocketHandlers();
        const ttsTest = await this.ttsService.testConnection();
        console.log(`✅ TTS Service: ${ttsTest ? 'Connected' : 'Failed (will continue without TTS)'}`);
        console.log('🎙️ Voice Chat Server ready!');
    }
    setupWebSocketHandlers() {
        this.wsService['io'].on('connection', (socket) => {
            console.log(`🔗 Client connected: ${socket.id}`);
            this.audioBuffer.set(socket.id, []);
            this.conversationHistory.set(socket.id, []);
            socket.on('audio:start', () => {
                console.log(`🎤 Audio session started: ${socket.id}`);
                this.vadService.resetConversationState();
                this.audioBuffer.set(socket.id, []);
            });
            socket.on('audio:chunk', async (chunk) => {
                await this.processAudioChunk(socket.id, chunk);
            });
            socket.on('audio:end', async () => {
                console.log(`🔇 Audio session ended: ${socket.id}`);
                await this.processCompleteAudio(socket.id);
            });
            socket.on('disconnect', () => {
                console.log(`🔌 Client disconnected: ${socket.id}`);
                this.cleanup(socket.id);
            });
        });
    }
    async processAudioChunk(socketId, chunk) {
        try {
            const audioBuffer = audioUtils_1.AudioUtils.arrayBufferToBuffer(chunk.data);
            const vadResult = await this.vadService.processAudio(audioBuffer);
            if (vadResult.isSpeech) {
                const buffers = this.audioBuffer.get(socketId) || [];
                buffers.push(audioBuffer);
                this.audioBuffer.set(socketId, buffers);
                if (this.vadService.shouldEndSegment()) {
                    await this.processCompleteAudio(socketId);
                }
            }
        }
        catch (error) {
            console.error(`Error processing audio chunk for ${socketId}:`, error);
            this.wsService.getConnectionState(socketId);
        }
    }
    async processCompleteAudio(socketId) {
        const buffers = this.audioBuffer.get(socketId);
        if (!buffers || buffers.length === 0) {
            console.log(`No audio data to process for ${socketId}`);
            return;
        }
        try {
            console.log(`🎵 Processing complete audio for ${socketId} (${buffers.length} chunks)`);
            const combinedBuffer = Buffer.concat(buffers);
            this.audioBuffer.set(socketId, []);
            let processedAudio = combinedBuffer;
            if (this.spectralGating.isSpectralGatingEnabled()) {
                console.log('🔊 Applying spectral gating...');
                processedAudio = await this.spectralGating.processAudio(combinedBuffer);
            }
            console.log('🗣️ Starting speech-to-text...');
            const transcription = await this.sttWorker.transcribeAudio(processedAudio);
            if (!transcription.text.trim()) {
                console.log('Empty transcription, skipping...');
                return;
            }
            console.log(`📝 Transcription: "${transcription.text}"`);
            this.wsService.emitTranscription(socketId, transcription);
            const history = this.conversationHistory.get(socketId) || [];
            history.push(transcription.text);
            console.log('🤖 Generating AI response...');
            const aiResponse = await this.aiService.generateResponse(transcription, history);
            console.log(`💬 AI Response: "${aiResponse.text}"`);
            history.push(aiResponse.text);
            this.conversationHistory.set(socketId, history.slice(-20));
            this.wsService.emitAIResponse(socketId, aiResponse);
            console.log('🔊 Generating TTS audio...');
            const ttsResponse = await this.ttsService.generateTTS(aiResponse);
            console.log(`🎵 TTS generated: ${ttsResponse.audioData.byteLength} bytes`);
            this.wsService.emitTTSAudio(socketId, ttsResponse);
        }
        catch (error) {
            console.error(`Error processing audio for ${socketId}:`, error);
            this.wsService['io'].to(socketId).emit('error', {
                message: 'Audio processing failed',
                code: 'PROCESSING_ERROR'
            });
        }
    }
    cleanup(socketId) {
        this.audioBuffer.delete(socketId);
        this.conversationHistory.delete(socketId);
    }
    async shutdown() {
        console.log('🛑 Shutting down server...');
        this.wsService.cleanup();
        this.vadService.cleanup();
        this.spectralGating.cleanup();
        this.sttWorker.cleanup();
        this.ttsService.cleanup();
        server.close(() => {
            console.log('✅ Server shut down gracefully');
            process.exit(0);
        });
    }
}
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        services: {
            websocket: 'running',
            vad: 'running',
            stt: 'running',
            ai: 'running',
            tts: 'running'
        }
    });
});
app.get('*', (req, res) => {
    res.sendFile(path_1.default.join(__dirname, '../../client/dist/index.html'));
});
const voiceChatServer = new VoiceChatServer();
process.on('SIGINT', () => {
    console.log('\n🛑 Received SIGINT, shutting down gracefully...');
    voiceChatServer.shutdown();
});
process.on('SIGTERM', () => {
    console.log('\n🛑 Received SIGTERM, shutting down gracefully...');
    voiceChatServer.shutdown();
});
server.listen(PORT, () => {
    console.log(`🌟 Voice Chat Server running on port ${PORT}`);
    console.log(`🌐 WebSocket endpoint: ws://localhost:${PORT}`);
    console.log(`🔗 Client URL: ${process.env.CLIENT_URL || 'http://localhost:5173'}`);
});
exports.default = app;
//# sourceMappingURL=index.js.map