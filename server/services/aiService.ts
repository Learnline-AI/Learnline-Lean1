import { OpenAI } from 'openai';
import axios from 'axios';
import { AIResponse, TranscriptionResult } from '../types/shared';
import { getAIProviderConfig, getSystemPrompt } from '../config/aiConfig';

export class AIService {
  private openai: OpenAI;
  private providers: string[] = [];

  constructor() {
    this.openai = new OpenAI({ 
      apiKey: process.env.OPENAI_API_KEY || '' 
    });
    
    this.initializeProviders();
  }

  private initializeProviders() {
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

  async generateResponse(transcription: TranscriptionResult, conversationHistory: string[] = []): Promise<AIResponse> {
    const config = getAIProviderConfig();
    const systemPrompt = getSystemPrompt(transcription.language);
    
    for (const provider of this.providers) {
      try {
        console.log(`Attempting to generate response using ${provider}`);
        
        const response = await this.callProvider(
          provider,
          transcription.text,
          systemPrompt,
          conversationHistory,
          config
        );
        
        return {
          text: response,
          language: transcription.language,
          provider,
          model: config.model,
          timestamp: Date.now()
        };
      } catch (error) {
        console.error(`Provider ${provider} failed:`, error);
        
        if (provider === this.providers[this.providers.length - 1]) {
          throw new Error(`All AI providers failed. Last error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
      }
    }

    throw new Error('No AI providers available');
  }

  private async callProvider(
    provider: string,
    userMessage: string,
    systemPrompt: string,
    conversationHistory: string[],
    config: any
  ): Promise<string> {
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

  private async callOpenAI(
    userMessage: string,
    systemPrompt: string,
    conversationHistory: string[],
    config: any
  ): Promise<string> {
    const messages: any[] = [
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

  private async callGemini(
    userMessage: string,
    systemPrompt: string,
    conversationHistory: string[],
    config: any
  ): Promise<string> {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${config.model}:generateContent?key=${process.env.GEMINI_API_KEY}`;
    
    const prompt = `${systemPrompt}\n\nConversation History:\n${conversationHistory.slice(-10).join('\n')}\n\nUser: ${userMessage}\n\nAssistant:`;
    
    const response = await axios.post(url, {
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

  private async callClaude(
    userMessage: string,
    systemPrompt: string,
    conversationHistory: string[],
    config: any
  ): Promise<string> {
    const url = 'https://api.anthropic.com/v1/messages';
    
    const messages: any[] = [];
    
    conversationHistory.slice(-10).forEach((msg, index) => {
      const role = index % 2 === 0 ? 'user' : 'assistant';
      messages.push({ role, content: msg });
    });

    messages.push({ role: 'user', content: userMessage });

    const response = await axios.post(url, {
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

  public getAvailableProviders(): string[] {
    return [...this.providers];
  }

  public detectLanguage(text: string): 'en' | 'hi' | 'mixed' {
    const hindiRegex = /[\u0900-\u097F]/;
    const englishRegex = /[a-zA-Z]/;
    
    const hasHindi = hindiRegex.test(text);
    const hasEnglish = englishRegex.test(text);
    
    if (hasHindi && hasEnglish) {
      return 'mixed';
    } else if (hasHindi) {
      return 'hi';
    } else {
      return 'en';
    }
  }
}