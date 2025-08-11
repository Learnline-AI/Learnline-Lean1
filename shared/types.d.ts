export interface AudioChunk {
    data: ArrayBuffer;
    format: 'pcm' | 'wav' | 'mp3';
    sampleRate: number;
    channels: number;
    timestamp: number;
}
export interface TranscriptionResult {
    text: string;
    language: string;
    confidence: number;
    duration: number;
}
export interface AIResponse {
    text: string;
    language: string;
    provider: string;
    model: string;
    timestamp: number;
}
export interface TTSResponse {
    audioData: ArrayBuffer;
    format: 'mp3' | 'wav';
    contentType: string;
    duration?: number;
}
export interface WebSocketEvents {
    'audio:start': () => void;
    'audio:chunk': (chunk: AudioChunk) => void;
    'audio:end': () => void;
    'transcription': (result: TranscriptionResult) => void;
    'ai:response': (response: AIResponse) => void;
    'tts:audio': (audio: TTSResponse) => void;
    'error': (error: {
        message: string;
        code?: string;
    }) => void;
    'connection:status': (status: 'connected' | 'disconnected' | 'reconnecting') => void;
}
export interface VADResult {
    isSpeech: boolean;
    confidence: number;
    timestamp: number;
}
export interface ConnectionState {
    isConnected: boolean;
    reconnectAttempts: number;
    lastPingTime: number;
    quality: 'excellent' | 'good' | 'poor' | 'disconnected';
}
export interface AudioProcessingConfig {
    sampleRate: number;
    channels: number;
    bitDepth: number;
    chunkSize: number;
    enableVAD: boolean;
    enableSpectralGating: boolean;
}
export interface AIProviderConfig {
    provider: 'openai' | 'gemini' | 'claude';
    model: string;
    language: 'en' | 'hi' | 'auto';
    maxTokens: number;
    temperature: number;
}
export interface TTSProviderConfig {
    provider: 'elevenlabs';
    voiceId: string;
    model: string;
    stability: number;
    similarityBoost: number;
    outputFormat: 'mp3' | 'wav';
}
//# sourceMappingURL=types.d.ts.map