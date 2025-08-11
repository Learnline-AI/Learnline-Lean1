import { TTSResponse, AIResponse } from '../types/shared';
export declare class TTSService {
    private elevenlabsApiKey;
    private voiceId;
    private model;
    private provider;
    constructor();
    generateTTS(aiResponse: AIResponse): Promise<TTSResponse>;
    private generateElevenLabsTTS;
    private estimateAudioDuration;
    testConnection(): Promise<boolean>;
    getAvailableVoices(): string[];
    setVoice(voiceId: string): void;
    detectLanguageForTTS(text: string): 'en' | 'hi' | 'auto';
    cleanup(): void;
}
//# sourceMappingURL=ttsService.d.ts.map