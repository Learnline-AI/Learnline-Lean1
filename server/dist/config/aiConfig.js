"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.aiConfig = void 0;
exports.getAIProviderConfig = getAIProviderConfig;
exports.getSystemPrompt = getSystemPrompt;
exports.validateAIConfig = validateAIConfig;
exports.aiConfig = {
    providers: {
        openai: {
            apiKey: process.env.OPENAI_API_KEY || '',
            models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            maxTokens: 1000,
            temperature: 0.7
        },
        gemini: {
            apiKey: process.env.GEMINI_API_KEY || '',
            models: ['gemini-pro', 'gemini-pro-latest'],
            maxTokens: 1000,
            temperature: 0.7
        },
        claude: {
            apiKey: process.env.CLAUDE_API_KEY || '',
            models: ['claude-3-sonnet', 'claude-3-haiku'],
            maxTokens: 1000,
            temperature: 0.7
        }
    },
    defaultProvider: process.env.AI_PROVIDER || 'openai',
    language: process.env.AI_LANGUAGE || 'auto',
    systemPrompts: {
        english: `You are a helpful AI assistant that provides clear, concise, and informative responses. 
    Keep your answers natural and conversational. Respond in English unless specifically asked to use another language.`,
        hindi: `आप एक सहायक AI सहायक हैं जो स्पष्ट, संक्षिप्त और जानकारीपूर्ण उत्तर प्रदान करते हैं। 
    अपने उत्तरों को प्राकृतिक और वार्तालाप की तरह रखें। हिंदी में जवाब दें जब तक कि विशेष रूप से किसी अन्य भाषा का उपयोग करने को न कहा जाए।`,
        educational: `You are an AI tutor that helps students learn by providing clear explanations, examples, and guidance. 
    Adapt your teaching style to the student's level and provide encouragement. Use both English and Hindi as needed to ensure understanding.`
    }
};
function getAIProviderConfig(provider) {
    const selectedProvider = provider || exports.aiConfig.defaultProvider;
    const providerConfig = exports.aiConfig.providers[selectedProvider];
    if (!providerConfig || !providerConfig.apiKey) {
        throw new Error(`AI provider '${selectedProvider}' is not configured or missing API key`);
    }
    return {
        provider: selectedProvider,
        model: providerConfig.models[0],
        language: exports.aiConfig.language,
        maxTokens: providerConfig.maxTokens,
        temperature: providerConfig.temperature
    };
}
function getSystemPrompt(language) {
    const lang = language || exports.aiConfig.language;
    switch (lang) {
        case 'hi':
            return exports.aiConfig.systemPrompts.hindi;
        case 'en':
            return exports.aiConfig.systemPrompts.english;
        default:
            return exports.aiConfig.systemPrompts.educational;
    }
}
function validateAIConfig() {
    try {
        const config = getAIProviderConfig();
        return true;
    }
    catch (error) {
        console.error('AI configuration validation failed:', error);
        return false;
    }
}
//# sourceMappingURL=aiConfig.js.map