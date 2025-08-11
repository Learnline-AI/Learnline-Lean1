import express from 'express';
import { createServer } from 'http';
import cors from 'cors';
import dotenv from 'dotenv';
import path from 'path';

import { WebSocketService } from './services/websocketService';
import { VADService } from './services/vadService';
import { SpectralGatingService } from './services/spectralGating';
import { STTWorker } from './workers/sttWorker';
import { AIService } from './services/aiService';
import { TTSService } from './services/ttsService';
import { AudioUtils } from './utils/audioUtils';
import { validateAIConfig } from './config/aiConfig';
import { AudioChunk } from './types/shared';

dotenv.config();

const app = express();
const server = createServer(app);
const PORT = process.env.PORT || 3001;

app.use(cors({
  origin: process.env.CLIENT_URL || 'http://localhost:5173',
  credentials: true
}));

app.use(express.json());
app.use(express.static(path.join(__dirname, '../../client/dist')));

class VoiceChatServer {
  private wsService: WebSocketService;
  private vadService: VADService;
  private spectralGating: SpectralGatingService;
  private sttWorker: STTWorker;
  private aiService: AIService;
  private ttsService: TTSService;
  private audioBuffer: Map<string, Buffer[]> = new Map();
  private conversationHistory: Map<string, string[]> = new Map();

  constructor() {
    this.wsService = new WebSocketService(server);
    this.vadService = new VADService();
    this.spectralGating = new SpectralGatingService();
    this.sttWorker = new STTWorker();
    this.aiService = new AIService();
    this.ttsService = new TTSService();
    
    this.initialize();
  }

  private async initialize() {
    console.log('🚀 Initializing Voice Chat Server...');
    
    if (!validateAIConfig()) {
      console.error('❌ AI configuration validation failed');
      process.exit(1);
    }

    await this.vadService.initialize();
    console.log('✅ VAD Service ready (fallback enabled if needed)');

    this.setupWebSocketHandlers();
    
    const ttsTest = await this.ttsService.testConnection();
    console.log(`✅ TTS Service: ${ttsTest ? 'Connected' : 'Failed (will continue without TTS)'}`);
    
    console.log('🎙️ Voice Chat Server ready!');
  }

  private setupWebSocketHandlers() {
    this.wsService['io'].on('connection', (socket: any) => {
      console.log(`🔗 Client connected: ${socket.id}`);
      
      this.audioBuffer.set(socket.id, []);
      this.conversationHistory.set(socket.id, []);

      socket.on('audio:start', () => {
        console.log(`🎤 Audio session started: ${socket.id}`);
        this.vadService.resetConversationState();
        this.audioBuffer.set(socket.id, []);
      });

      socket.on('audio:chunk', async (chunk: AudioChunk) => {
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

  private async processAudioChunk(socketId: string, chunk: AudioChunk) {
    try {
      const audioBuffer = AudioUtils.arrayBufferToBuffer(chunk.data);
      
      const vadResult = await this.vadService.processAudio(audioBuffer);
      
      if (vadResult.isSpeech) {
        const buffers = this.audioBuffer.get(socketId) || [];
        buffers.push(audioBuffer);
        this.audioBuffer.set(socketId, buffers);
        
        if (this.vadService.shouldEndSegment()) {
          await this.processCompleteAudio(socketId);
        }
      }
    } catch (error) {
      console.error(`Error processing audio chunk for ${socketId}:`, error);
      this.wsService.getConnectionState(socketId);
    }
  }

  private async processCompleteAudio(socketId: string) {
    const buffers = this.audioBuffer.get(socketId);
    if (!buffers || buffers.length === 0) {
      console.log(`No audio data to process for ${socketId}`);
      return;
    }

    try {
      console.log(`🎵 Processing complete audio for ${socketId} (${buffers.length} chunks)`);
      
      const combinedBuffer = Buffer.concat(buffers as Buffer[]);
      this.audioBuffer.set(socketId, []);

      let processedAudio: Buffer = combinedBuffer;
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

    } catch (error) {
      console.error(`Error processing audio for ${socketId}:`, error);
      this.wsService['io'].to(socketId).emit('error', {
        message: 'Audio processing failed',
        code: 'PROCESSING_ERROR'
      });
    }
  }

  private cleanup(socketId: string) {
    this.audioBuffer.delete(socketId);
    this.conversationHistory.delete(socketId);
  }

  public async shutdown() {
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
  res.sendFile(path.join(__dirname, '../../client/dist/index.html'));
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

export default app;