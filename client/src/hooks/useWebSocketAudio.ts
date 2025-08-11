import { useEffect, useRef, useCallback, useState } from 'react';
import { io, Socket } from 'socket.io-client';
import { useWebAudio } from './useWebAudio';
import { useAudioQueue } from './useAudioQueue';
import { TranscriptionResult, AIResponse, TTSResponse, AudioChunk } from '../../../shared/types';

export interface ConnectionState {
  status: 'connecting' | 'connected' | 'disconnected' | 'error';
  quality: 'excellent' | 'good' | 'poor' | 'disconnected';
  reconnectAttempts: number;
}

export interface UseWebSocketAudioReturn {
  connectionState: ConnectionState;
  isRecording: boolean;
  audioLevel: number;
  transcription: TranscriptionResult | null;
  aiResponse: AIResponse | null;
  startVoiceChat: () => Promise<void>;
  stopVoiceChat: () => void;
  clearHistory: () => void;
  audioQueue: ReturnType<typeof useAudioQueue>;
}

const SERVER_URL = import.meta.env.VITE_SERVER_URL || 'http://localhost:3001';

export const useWebSocketAudio = (): UseWebSocketAudioReturn => {
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    status: 'disconnected',
    quality: 'disconnected',
    reconnectAttempts: 0
  });

  const [transcription, setTranscription] = useState<TranscriptionResult | null>(null);
  const [aiResponse, setAIResponse] = useState<AIResponse | null>(null);

  const socketRef = useRef<Socket | null>(null);
  const audioChunkCounterRef = useRef(0);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const webAudio = useWebAudio();
  const audioQueue = useAudioQueue();

  useEffect(() => {
    initializeSocket();
    
    return () => {
      cleanup();
    };
  }, []);

  const initializeSocket = useCallback(() => {
    if (socketRef.current?.connected) {
      return;
    }

    console.log('🔗 Connecting to WebSocket server...');
    setConnectionState(prev => ({ ...prev, status: 'connecting' }));

    const socket = io(SERVER_URL, {
      transports: ['websocket'],
      upgrade: false,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      timeout: 10000
    });

    socketRef.current = socket;
    setupSocketEventHandlers(socket);
  }, []);

  const setupSocketEventHandlers = useCallback((socket: Socket) => {
    socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      setConnectionState(prev => ({ 
        ...prev, 
        status: 'connected',
        quality: 'excellent',
        reconnectAttempts: 0
      }));
      
      if (reconnectTimeoutRef.current !== null) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
    });

    socket.on('disconnect', (reason) => {
      console.log(`❌ WebSocket disconnected: ${reason}`);
      setConnectionState(prev => ({ 
        ...prev, 
        status: 'disconnected',
        quality: 'disconnected'
      }));
      
      if (webAudio.state.isRecording) {
        webAudio.stopRecording();
      }
    });

    socket.on('connect_error', (error) => {
      console.error('🔥 WebSocket connection error:', error);
      setConnectionState(prev => ({ 
        ...prev, 
        status: 'error',
        reconnectAttempts: prev.reconnectAttempts + 1
      }));
    });

    socket.on('reconnect_attempt', (attempt) => {
      console.log(`🔄 Reconnection attempt ${attempt}`);
      setConnectionState(prev => ({ 
        ...prev, 
        reconnectAttempts: attempt
      }));
    });

    socket.on('connection:status', (quality: 'excellent' | 'good' | 'poor' | 'disconnected') => {
      setConnectionState(prev => ({ ...prev, quality }));
    });

    socket.on('transcription', (result: TranscriptionResult) => {
      console.log('📝 Received transcription:', result.text);
      setTranscription(result);
    });

    socket.on('ai:response', (response: AIResponse) => {
      console.log('🤖 Received AI response:', response.text);
      setAIResponse(response);
    });

    socket.on('tts:audio', (audio: TTSResponse) => {
      console.log('🔊 Received TTS audio:', audio.audioData.byteLength, 'bytes');
      
      audioQueue.addToQueue({
        id: `tts-${Date.now()}`,
        data: audio.audioData,
        format: audio.format,
        contentType: audio.contentType,
        timestamp: Date.now()
      });
    });

    socket.on('error', (error: { message: string; code?: string }) => {
      console.error('🔥 Server error:', error);
    });
  }, [webAudio, audioQueue]);

  const startVoiceChat = useCallback(async (): Promise<void> => {
    try {
      if (!socketRef.current?.connected) {
        await new Promise<void>((resolve, reject) => {
          if (socketRef.current?.connected) {
            resolve();
            return;
          }

          const timeout = setTimeout(() => {
            reject(new Error('Connection timeout'));
          }, 5000);

          socketRef.current?.on('connect', () => {
            clearTimeout(timeout);
            resolve();
          });

          socketRef.current?.on('connect_error', (error) => {
            clearTimeout(timeout);
            reject(error);
          });
        });
      }

      console.log('🎤 Starting voice chat session...');
      
      socketRef.current!.emit('audio:start');
      
      webAudio.onAudioData((audioData: Float32Array) => {
        if (socketRef.current?.connected) {
          const pcmBuffer = new ArrayBuffer(audioData.length * 2);
          const view = new DataView(pcmBuffer);
          
          for (let i = 0; i < audioData.length; i++) {
            const sample = Math.max(-32768, Math.min(32767, audioData[i] * 32768));
            view.setInt16(i * 2, sample, true);
          }

          const chunk: AudioChunk = {
            data: pcmBuffer,
            format: 'pcm',
            sampleRate: 16000,
            channels: 1,
            timestamp: Date.now()
          };

          socketRef.current.emit('audio:chunk', chunk);
          audioChunkCounterRef.current++;
        }
      });

      await webAudio.startRecording();
      
      console.log('✅ Voice chat session started');
    } catch (error) {
      console.error('❌ Failed to start voice chat:', error);
      throw error;
    }
  }, [webAudio]);

  const stopVoiceChat = useCallback((): void => {
    try {
      console.log('🔇 Stopping voice chat session...');
      
      webAudio.stopRecording();
      
      if (socketRef.current?.connected) {
        socketRef.current.emit('audio:end');
      }
      
      console.log(`📊 Sent ${audioChunkCounterRef.current} audio chunks`);
      audioChunkCounterRef.current = 0;
      
      console.log('✅ Voice chat session stopped');
    } catch (error) {
      console.error('❌ Error stopping voice chat:', error);
    }
  }, [webAudio]);

  const clearHistory = useCallback((): void => {
    setTranscription(null);
    setAIResponse(null);
    audioQueue.clearQueue();
  }, [audioQueue]);

  const cleanup = useCallback(() => {
    if (webAudio.state.isRecording) {
      webAudio.stopRecording();
    }
    
    if (reconnectTimeoutRef.current !== null) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (socketRef.current && socketRef.current.connected) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    
    audioQueue.clearQueue();
  }, [webAudio, audioQueue]);

  return {
    connectionState,
    isRecording: webAudio.state.isRecording,
    audioLevel: webAudio.state.audioLevel,
    transcription,
    aiResponse,
    startVoiceChat,
    stopVoiceChat,
    clearHistory,
    audioQueue
  };
};