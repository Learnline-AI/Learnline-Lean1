let ort: any = null;
try {
  ort = require('onnxruntime-node');
} catch (error) {
  console.warn('ONNX Runtime not available:', error instanceof Error ? error.message : 'Unknown error');
}
import { VADResult } from '../types/shared';
import { AudioUtils } from '../utils/audioUtils';

export class VADService {
  private session: any | null = null;
  private isInitialized = false;
  private modelPath: string;
  private sampleRate = 16000;
  private windowSizeMs = 96;
  private threshold = 0.5;
  
  private conversationState: {
    isSpeaking: boolean;
    speechStartTime: number | null;
    silenceStartTime: number | null;
    speechDuration: number;
    silenceDuration: number;
  } = {
    isSpeaking: false,
    speechStartTime: null,
    silenceStartTime: null,
    speechDuration: 0,
    silenceDuration: 0
  };

  constructor(modelPath?: string) {
    this.modelPath = modelPath || './models/silero_vad.onnx';
  }

  async initialize(): Promise<void> {
    try {
      console.log('Initializing VAD service...');
      
      if (!ort) {
        throw new Error('ONNX Runtime not available');
      }
      
      // Check if ONNX model file exists
      const fs = require('fs');
      if (!fs.existsSync(this.modelPath)) {
        throw new Error(`VAD model file not found at ${this.modelPath}`);
      }
      
      this.session = await ort.InferenceSession.create(this.modelPath);
      this.isInitialized = true;
      console.log('VAD service initialized successfully');
    } catch (error) {
      console.warn('Failed to initialize VAD service:', error);
      console.log('VAD will be disabled, using simple energy detection fallback');
      this.isInitialized = false;
      this.session = null;
    }
  }

  async processAudio(audioBuffer: Buffer): Promise<VADResult> {
    const timestamp = Date.now();

    if (!this.isInitialized || !this.session) {
      return this.fallbackVAD(audioBuffer, timestamp);
    }

    try {
      const pcmData = this.preprocessAudio(audioBuffer);
      const tensor = new ort.Tensor('float32', pcmData, [1, pcmData.length]);
      
      const feeds = { input: tensor };
      const results = await this.session.run(feeds);
      
      const speechProb = results.output.data[0] as number;
      const isSpeech = speechProb > this.threshold;
      
      this.updateConversationState(isSpeech, timestamp);
      
      return {
        isSpeech,
        confidence: speechProb,
        timestamp
      };
    } catch (error) {
      console.error('Error in VAD processing:', error);
      return this.fallbackVAD(audioBuffer, timestamp);
    }
  }

  private preprocessAudio(audioBuffer: Buffer): Float32Array {
    const windowSize = Math.floor((this.windowSizeMs / 1000) * this.sampleRate);
    const samples = new Int16Array(audioBuffer.buffer, audioBuffer.byteOffset, audioBuffer.length / 2);
    
    let processedSamples: Int16Array;
    if (samples.length > windowSize) {
      processedSamples = samples.slice(0, windowSize);
    } else if (samples.length < windowSize) {
      processedSamples = new Int16Array(windowSize);
      processedSamples.set(samples);
    } else {
      processedSamples = samples;
    }

    const floatSamples = new Float32Array(processedSamples.length);
    for (let i = 0; i < processedSamples.length; i++) {
      floatSamples[i] = processedSamples[i] / 32768.0;
    }

    return floatSamples;
  }

  private fallbackVAD(audioBuffer: Buffer, timestamp: number): VADResult {
    const rms = AudioUtils.calculateRMS(audioBuffer);
    const threshold = 1000;
    const isSpeech = rms > threshold;
    const confidence = Math.min(rms / (threshold * 2), 1.0);
    
    this.updateConversationState(isSpeech, timestamp);
    
    return {
      isSpeech,
      confidence,
      timestamp
    };
  }

  private updateConversationState(isSpeech: boolean, timestamp: number) {
    if (isSpeech && !this.conversationState.isSpeaking) {
      this.conversationState.isSpeaking = true;
      this.conversationState.speechStartTime = timestamp;
      
      if (this.conversationState.silenceStartTime) {
        this.conversationState.silenceDuration += 
          timestamp - this.conversationState.silenceStartTime;
        this.conversationState.silenceStartTime = null;
      }
    } else if (!isSpeech && this.conversationState.isSpeaking) {
      this.conversationState.isSpeaking = false;
      this.conversationState.silenceStartTime = timestamp;
      
      if (this.conversationState.speechStartTime) {
        this.conversationState.speechDuration += 
          timestamp - this.conversationState.speechStartTime;
        this.conversationState.speechStartTime = null;
      }
    }
  }

  public getConversationState() {
    return { ...this.conversationState };
  }

  public resetConversationState() {
    this.conversationState = {
      isSpeaking: false,
      speechStartTime: null,
      silenceStartTime: null,
      speechDuration: 0,
      silenceDuration: 0
    };
  }

  public isCurrentlySpeaking(): boolean {
    return this.conversationState.isSpeaking;
  }

  public shouldEndSegment(): boolean {
    const minSilenceDuration = 1500;
    
    if (!this.conversationState.isSpeaking && 
        this.conversationState.silenceStartTime &&
        Date.now() - this.conversationState.silenceStartTime > minSilenceDuration) {
      return this.conversationState.speechDuration > 500;
    }
    
    return false;
  }

  public cleanup() {
    if (this.session) {
      this.session = null;
    }
    this.isInitialized = false;
  }
}