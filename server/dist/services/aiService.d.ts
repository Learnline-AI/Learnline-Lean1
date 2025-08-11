import { AIResponse, TranscriptionResult } from '../types/shared';
export declare class AIService {
    private openai;
    private providers;
    constructor();
    private initializeProviders;
    generateResponse(transcription: TranscriptionResult, conversationHistory?: string[]): Promise<AIResponse>;
    private callProvider;
    private callOpenAI;
    private callGemini;
    private callClaude;
    getAvailableProviders(): string[];
    detectLanguage(text: string): 'en' | 'hi' | 'mixed';
}
//# sourceMappingURL=aiService.d.ts.map