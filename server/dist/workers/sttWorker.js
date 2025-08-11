"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.STTWorker = void 0;
const worker_threads_1 = require("worker_threads");
const openai_1 = require("openai");
const audioUtils_1 = require("../utils/audioUtils");
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
class STTWorker {
    constructor() {
        this.worker = null;
        this.isProcessing = false;
        this.queue = [];
        if (worker_threads_1.isMainThread) {
            this.initializeWorker();
        }
    }
    initializeWorker() {
        this.worker = new worker_threads_1.Worker(__filename, {
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
                    }
                    else {
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
    async transcribeAudio(audioBuffer) {
        return new Promise((resolve, reject) => {
            this.queue.push({ audioBuffer, resolve, reject });
            this.processQueue();
        });
    }
    processQueue() {
        if (this.isProcessing || this.queue.length === 0 || !this.worker) {
            return;
        }
        this.isProcessing = true;
        const item = this.queue[0];
        this.worker.postMessage({ audioBuffer: item.audioBuffer });
    }
    cleanup() {
        if (this.worker) {
            this.worker.terminate();
            this.worker = null;
        }
    }
}
exports.STTWorker = STTWorker;
if (!worker_threads_1.isMainThread && worker_threads_1.parentPort) {
    const { openaiApiKey, whisperModel, language } = worker_threads_1.workerData;
    const openai = new openai_1.OpenAI({ apiKey: openaiApiKey });
    const tempDir = path.join(__dirname, '../temp');
    if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
    }
    worker_threads_1.parentPort.on('message', async ({ audioBuffer }) => {
        try {
            const result = await processAudioBuffer(audioBuffer, openai, whisperModel, language, tempDir);
            worker_threads_1.parentPort.postMessage(result);
        }
        catch (error) {
            worker_threads_1.parentPort.postMessage({ error: error instanceof Error ? error.message : 'Unknown error' });
        }
    });
    async function processAudioBuffer(audioBuffer, openai, model, language, tempDir) {
        const timestamp = Date.now();
        const tempFilePath = path.join(tempDir, `audio_${timestamp}.wav`);
        try {
            const { isValid } = audioUtils_1.AudioUtils.validateAudioFormat(audioBuffer);
            let wavBuffer;
            if (isValid) {
                wavBuffer = audioBuffer;
            }
            else {
                wavBuffer = audioUtils_1.AudioUtils.pcmToWAV(audioBuffer, 16000, 1, 16);
            }
            fs.writeFileSync(tempFilePath, wavBuffer);
            const transcription = await openai.audio.transcriptions.create({
                file: fs.createReadStream(tempFilePath),
                model: model,
                language: language === 'auto' ? undefined : language,
                response_format: 'verbose_json'
            });
            const result = {
                text: transcription.text || '',
                language: transcription.language || language,
                confidence: 1.0,
                duration: transcription.duration || 0
            };
            fs.unlinkSync(tempFilePath);
            return result;
        }
        catch (error) {
            if (fs.existsSync(tempFilePath)) {
                fs.unlinkSync(tempFilePath);
            }
            console.error('STT processing error:', error);
            throw new Error(`Speech-to-text failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
}
//# sourceMappingURL=sttWorker.js.map