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

export const aiConfig: AIConfig = {
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
  defaultProvider: (process.env.AI_PROVIDER as 'openai' | 'gemini' | 'claude') || 'openai',
  language: (process.env.AI_LANGUAGE as 'en' | 'hi' | 'auto') || 'auto',
  systemPrompts: {
    english: `You are a helpful AI assistant that provides clear, concise, and informative responses. 
    Keep your answers natural and conversational. Respond in English unless specifically asked to use another language.`,
    
    hindi: `आप एक सहायक AI सहायक हैं जो स्पष्ट, संक्षिप्त और जानकारीपूर्ण उत्तर प्रदान करते हैं। 
    अपने उत्तरों को प्राकृतिक और वार्तालाप की तरह रखें। हिंदी में जवाब दें जब तक कि विशेष रूप से किसी अन्य भाषा का उपयोग करने को न कहा जाए।`,
    
    educational: `You are an AI tutor that helps students learn by providing clear explanations, examples, and guidance. 
    Adapt your teaching style to the student's level and provide encouragement. Use both English and Hindi as needed to ensure understanding.`
  }
};

export function getAIProviderConfig(provider?: string): AIProviderConfig {
  const selectedProvider = provider || aiConfig.defaultProvider;
  const providerConfig = aiConfig.providers[selectedProvider as keyof typeof aiConfig.providers];
  
  if (!providerConfig || !providerConfig.apiKey) {
    throw new Error(`AI provider '${selectedProvider}' is not configured or missing API key`);
  }

  return {
    provider: selectedProvider as 'openai' | 'gemini' | 'claude',
    model: providerConfig.models[0],
    language: aiConfig.language,
    maxTokens: providerConfig.maxTokens,
    temperature: providerConfig.temperature
  };
}

export function getSystemPrompt(language?: string): string {
  const lang = language || aiConfig.language;
  
  switch (lang) {
    case 'hi':
      return aiConfig.systemPrompts.hindi;
    case 'en':
      return aiConfig.systemPrompts.english;
    default:
      return aiConfig.systemPrompts.educational;
  }
}

export function validateAIConfig(): boolean {
  try {
    const config = getAIProviderConfig();
    return true;
  } catch (error) {
    console.error('AI configuration validation failed:', error);
    return false;
  }
}