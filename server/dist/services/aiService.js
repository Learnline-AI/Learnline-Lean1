"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AIService = void 0;
const openai_1 = require("openai");
const axios_1 = __importDefault(require("axios"));
const aiConfig_1 = require("../config/aiConfig");
class AIService {
    constructor() {
        this.providers = [];
        this.openai = new openai_1.OpenAI({
            apiKey: process.env.OPENAI_API_KEY || ''
        });
        this.initializeProviders();
    }
    initializeProviders() {
        if (process.env.OPENAI_API_KEY) {
            this.providers.push('openai');
        }
        if (process.env.GEMINI_API_KEY) {
            this.providers.push('gemini');
        }
        if (process.env.CLAUDE_API_KEY) {
            this.providers.push('claude');
        }
        if (this.providers.length === 0) {
            throw new Error('No AI providers configured. Please set at least one API key.');
        }
        console.log(`AI Service initialized with providers: ${this.providers.join(', ')}`);
    }
    async generateResponse(transcription, conversationHistory = []) {
        const config = (0, aiConfig_1.getAIProviderConfig)();
        const systemPrompt = (0, aiConfig_1.getSystemPrompt)(transcription.language);
        for (const provider of this.providers) {
            try {
                console.log(`Attempting to generate response using ${provider}`);
                const response = await this.callProvider(provider, transcription.text, systemPrompt, conversationHistory, config);
                return {
                    text: response,
                    language: transcription.language,
                    provider,
                    model: config.model,
                    timestamp: Date.now()
                };
            }
            catch (error) {
                console.error(`Provider ${provider} failed:`, error);
                if (provider === this.providers[this.providers.length - 1]) {
                    throw new Error(`All AI providers failed. Last error: ${error instanceof Error ? error.message : 'Unknown error'}`);
                }
            }
        }
        throw new Error('No AI providers available');
    }
    async callProvider(provider, userMessage, systemPrompt, conversationHistory, config) {
        switch (provider) {
            case 'openai':
                return this.callOpenAI(userMessage, systemPrompt, conversationHistory, config);
            case 'gemini':
                return this.callGemini(userMessage, systemPrompt, conversationHistory, config);
            case 'claude':
                return this.callClaude(userMessage, systemPrompt, conversationHistory, config);
            default:
                throw new Error(`Unsupported provider: ${provider}`);
        }
    }
    async callOpenAI(userMessage, systemPrompt, conversationHistory, config) {
        const messages = [
            { role: 'system', content: systemPrompt }
        ];
        conversationHistory.slice(-10).forEach((msg, index) => {
            const role = index % 2 === 0 ? 'user' : 'assistant';
            messages.push({ role, content: msg });
        });
        messages.push({ role: 'user', content: userMessage });
        const completion = await this.openai.chat.completions.create({
            model: config.model,
            messages,
            max_tokens: config.maxTokens,
            temperature: config.temperature,
        });
        return completion.choices[0]?.message?.content || '';
    }
    async callGemini(userMessage, systemPrompt, conversationHistory, config) {
        const url = `https://generativelanguage.googleapis.com/v1beta/models/${config.model}:generateContent?key=${process.env.GEMINI_API_KEY}`;
        const prompt = `${systemPrompt}\n\nConversation History:\n${conversationHistory.slice(-10).join('\n')}\n\nUser: ${userMessage}\n\nAssistant:`;
        const response = await axios_1.default.post(url, {
            contents: [{
                    parts: [{ text: prompt }]
                }],
            generationConfig: {
                maxOutputTokens: config.maxTokens,
                temperature: config.temperature
            }
        });
        return response.data.candidates?.[0]?.content?.parts?.[0]?.text || '';
    }
    async callClaude(userMessage, systemPrompt, conversationHistory, config) {
        const url = 'https://api.anthropic.com/v1/messages';
        const messages = [];
        conversationHistory.slice(-10).forEach((msg, index) => {
            const role = index % 2 === 0 ? 'user' : 'assistant';
            messages.push({ role, content: msg });
        });
        messages.push({ role: 'user', content: userMessage });
        const response = await axios_1.default.post(url, {
            model: config.model,
            max_tokens: config.maxTokens,
            temperature: config.temperature,
            system: systemPrompt,
            messages
        }, {
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': process.env.CLAUDE_API_KEY,
                'anthropic-version': '2023-06-01'
            }
        });
        return response.data.content?.[0]?.text || '';
    }
    getAvailableProviders() {
        return [...this.providers];
    }
    detectLanguage(text) {
        const hindiRegex = /[\u0900-\u097F]/;
        const englishRegex = /[a-zA-Z]/;
        const hasHindi = hindiRegex.test(text);
        const hasEnglish = englishRegex.test(text);
        if (hasHindi && hasEnglish) {
            return 'mixed';
        }
        else if (hasHindi) {
            return 'hi';
        }
        else {
            return 'en';
        }
    }
}
exports.AIService = AIService;
//# sourceMappingURL=aiService.js.map