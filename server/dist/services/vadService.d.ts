import { VADResult } from '../types/shared';
export declare class VADService {
    private session;
    private isInitialized;
    private modelPath;
    private sampleRate;
    private windowSizeMs;
    private threshold;
    private conversationState;
    constructor(modelPath?: string);
    initialize(): Promise<void>;
    processAudio(audioBuffer: Buffer): Promise<VADResult>;
    private preprocessAudio;
    private fallbackVAD;
    private updateConversationState;
    getConversationState(): {
        isSpeaking: boolean;
        speechStartTime: number | null;
        silenceStartTime: number | null;
        speechDuration: number;
        silenceDuration: number;
    };
    resetConversationState(): void;
    isCurrentlySpeaking(): boolean;
    shouldEndSegment(): boolean;
    cleanup(): void;
}
//# sourceMappingURL=vadService.d.ts.map