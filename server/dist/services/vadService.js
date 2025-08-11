"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.VADService = void 0;
let ort = null;
try {
    ort = require('onnxruntime-node');
}
catch (error) {
    console.warn('ONNX Runtime not available:', error instanceof Error ? error.message : 'Unknown error');
}
const audioUtils_1 = require("../utils/audioUtils");
class VADService {
    constructor(modelPath) {
        this.session = null;
        this.isInitialized = false;
        this.sampleRate = 16000;
        this.windowSizeMs = 96;
        this.threshold = 0.5;
        this.conversationState = {
            isSpeaking: false,
            speechStartTime: null,
            silenceStartTime: null,
            speechDuration: 0,
            silenceDuration: 0
        };
        this.modelPath = modelPath || './models/silero_vad.onnx';
    }
    async initialize() {
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
        }
        catch (error) {
            console.warn('Failed to initialize VAD service:', error);
            console.log('VAD will be disabled, using simple energy detection fallback');
            this.isInitialized = false;
            this.session = null;
        }
    }
    async processAudio(audioBuffer) {
        const timestamp = Date.now();
        if (!this.isInitialized || !this.session) {
            return this.fallbackVAD(audioBuffer, timestamp);
        }
        try {
            const pcmData = this.preprocessAudio(audioBuffer);
            const tensor = new ort.Tensor('float32', pcmData, [1, pcmData.length]);
            const feeds = { input: tensor };
            const results = await this.session.run(feeds);
            const speechProb = results.output.data[0];
            const isSpeech = speechProb > this.threshold;
            this.updateConversationState(isSpeech, timestamp);
            return {
                isSpeech,
                confidence: speechProb,
                timestamp
            };
        }
        catch (error) {
            console.error('Error in VAD processing:', error);
            return this.fallbackVAD(audioBuffer, timestamp);
        }
    }
    preprocessAudio(audioBuffer) {
        const windowSize = Math.floor((this.windowSizeMs / 1000) * this.sampleRate);
        const samples = new Int16Array(audioBuffer.buffer, audioBuffer.byteOffset, audioBuffer.length / 2);
        let processedSamples;
        if (samples.length > windowSize) {
            processedSamples = samples.slice(0, windowSize);
        }
        else if (samples.length < windowSize) {
            processedSamples = new Int16Array(windowSize);
            processedSamples.set(samples);
        }
        else {
            processedSamples = samples;
        }
        const floatSamples = new Float32Array(processedSamples.length);
        for (let i = 0; i < processedSamples.length; i++) {
            floatSamples[i] = processedSamples[i] / 32768.0;
        }
        return floatSamples;
    }
    fallbackVAD(audioBuffer, timestamp) {
        const rms = audioUtils_1.AudioUtils.calculateRMS(audioBuffer);
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
    updateConversationState(isSpeech, timestamp) {
        if (isSpeech && !this.conversationState.isSpeaking) {
            this.conversationState.isSpeaking = true;
            this.conversationState.speechStartTime = timestamp;
            if (this.conversationState.silenceStartTime) {
                this.conversationState.silenceDuration +=
                    timestamp - this.conversationState.silenceStartTime;
                this.conversationState.silenceStartTime = null;
            }
        }
        else if (!isSpeech && this.conversationState.isSpeaking) {
            this.conversationState.isSpeaking = false;
            this.conversationState.silenceStartTime = timestamp;
            if (this.conversationState.speechStartTime) {
                this.conversationState.speechDuration +=
                    timestamp - this.conversationState.speechStartTime;
                this.conversationState.speechStartTime = null;
            }
        }
    }
    getConversationState() {
        return { ...this.conversationState };
    }
    resetConversationState() {
        this.conversationState = {
            isSpeaking: false,
            speechStartTime: null,
            silenceStartTime: null,
            speechDuration: 0,
            silenceDuration: 0
        };
    }
    isCurrentlySpeaking() {
        return this.conversationState.isSpeaking;
    }
    shouldEndSegment() {
        const minSilenceDuration = 1500;
        if (!this.conversationState.isSpeaking &&
            this.conversationState.silenceStartTime &&
            Date.now() - this.conversationState.silenceStartTime > minSilenceDuration) {
            return this.conversationState.speechDuration > 500;
        }
        return false;
    }
    cleanup() {
        if (this.session) {
            this.session = null;
        }
        this.isInitialized = false;
    }
}
exports.VADService = VADService;
//# sourceMappingURL=vadService.js.map