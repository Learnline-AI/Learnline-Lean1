import { AIProviderConfig } from '../types/shared';
export interface AIConfig {
    providers: {
        openai: {
            apiKey: string;
            models: string[];
            maxTokens: number;
            temperature: number;
        };
        gemini: {
            apiKey: string;
            models: string[];
            maxTokens: number;
            temperature: number;
        };
        claude: {
            apiKey: string;
            models: string[];
            maxTokens: number;
            temperature: number;
        };
    };
    defaultProvider: 'openai' | 'gemini' | 'claude';
    language: 'en' | 'hi' | 'auto';
    systemPrompts: {
        english: string;
        hindi: string;
        educational: string;
    };
}
export declare const aiConfig: AIConfig;
export declare function getAIProviderConfig(provider?: string): AIProviderConfig;
export declare function getSystemPrompt(language?: string): string;
export declare function validateAIConfig(): boolean;
//# sourceMappingURL=aiConfig.d.ts.map