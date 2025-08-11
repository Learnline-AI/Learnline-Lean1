import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import { OpenAI } from 'openai';
import { AudioUtils } from '../utils/audioUtils';
import { TranscriptionResult } from '../types/shared';
import * as fs from 'fs';
import * as path from 'path';

export class STTWorker {
  private worker: Worker | null = null;
  private isProcessing = false;
  private queue: Array<{ audioBuffer: Buffer; resolve: Function; reject: Function }> = [];

  constructor() {
    if (isMainThread) {
      this.initializeWorker();
    }
  }

  private initializeWorker() {
    this.worker = new Worker(__filename, {
      workerData: {
        openaiApiKey: process.env.OPENAI_API_KEY,
        whisperModel: process.env.WHISPER_MODEL || 'whisper-1',
        language: process.env.WHISPER_LANGUAGE || 'hi'
      }
    });

    this.worker.on('message', (result) => {
      if (this.queue.length > 0) {
        const item = this.queue.shift();
        if (item) {
          if (result.error) {
            item.reject(new Error(result.error));
          } else {
            item.resolve(result);
          }
        }
      }
      this.isProcessing = false;
      this.processQueue();
    });

    this.worker.on('error', (error) => {
      console.error('STT Worker error:', error);
      if (this.queue.length > 0) {
        const item = this.queue.shift();
        if (item) {
          item.reject(error);
        }
      }
      this.isProcessing = false;
      this.processQueue();
    });
  }

  async transcribeAudio(audioBuffer: Buffer): Promise<TranscriptionResult> {
    return new Promise((resolve, reject) => {
      this.queue.push({ audioBuffer, resolve, reject });
      this.processQueue();
    });
  }

  private processQueue() {
    if (this.isProcessing || this.queue.length === 0 || !this.worker) {
      return;
    }

    this.isProcessing = true;
    const item = this.queue[0];
    this.worker.postMessage({ audioBuffer: item.audioBuffer });
  }

  public cleanup() {
    if (this.worker) {
      this.worker.terminate();
      this.worker = null;
    }
  }
}

if (!isMainThread && parentPort) {
  const { openaiApiKey, whisperModel, language } = workerData;
  const openai = new OpenAI({ apiKey: openaiApiKey });
  const tempDir = path.join(__dirname, '../temp');

  if (!fs.existsSync(tempDir)) {
    fs.mkdirSync(tempDir, { recursive: true });
  }

  parentPort.on('message', async ({ audioBuffer }) => {
    try {
      const result = await processAudioBuffer(audioBuffer, openai, whisperModel, language, tempDir);
      parentPort!.postMessage(result);
    } catch (error) {
      parentPort!.postMessage({ error: error instanceof Error ? error.message : 'Unknown error' });
    }
  });

  async function processAudioBuffer(
    audioBuffer: Buffer, 
    openai: OpenAI, 
    model: string, 
    language: string,
    tempDir: string
  ): Promise<TranscriptionResult> {
    const timestamp = Date.now();
    const tempFilePath = path.join(tempDir, `audio_${timestamp}.wav`);

    try {
      const { isValid } = AudioUtils.validateAudioFormat(audioBuffer);
      
      let wavBuffer: Buffer;
      if (isValid) {
        wavBuffer = audioBuffer;
      } else {
        wavBuffer = AudioUtils.pcmToWAV(audioBuffer, 16000, 1, 16);
      }

      fs.writeFileSync(tempFilePath, wavBuffer);

      const transcription = await openai.audio.transcriptions.create({
        file: fs.createReadStream(tempFilePath),
        model: model,
        language: language === 'auto' ? undefined : language,
        response_format: 'verbose_json'
      });

      const result: TranscriptionResult = {
        text: transcription.text || '',
        language: transcription.language || language,
        confidence: 1.0,
        duration: transcription.duration || 0
      };

      fs.unlinkSync(tempFilePath);
      return result;
    } catch (error) {
      if (fs.existsSync(tempFilePath)) {
        fs.unlinkSync(tempFilePath);
      }
      
      console.error('STT processing error:', error);
      throw new Error(`Speech-to-text failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}