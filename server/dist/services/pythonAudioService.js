"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.PythonAudioService = void 0;
const axios_1 = __importDefault(require("axios"));
const form_data_1 = __importDefault(require("form-data"));
const audioUtils_1 = require("../utils/audioUtils");
class PythonAudioService {
    constructor() {
        this.pythonServiceUrl = process.env.PYTHON_AUDIO_SERVICE_URL || 'https://learnline-v2-production-570c.up.railway.app';
        this.timeout = parseInt(process.env.PYTHON_SERVICE_TIMEOUT || '30000');
        this.retryAttempts = parseInt(process.env.PYTHON_SERVICE_RETRIES || '2');
    }
    async transcribeAudio(audioBuffer) {
        console.log(`🐍 Sending audio to Python service: ${this.pythonServiceUrl}`);
        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                return await this.makeTranscriptionRequest(audioBuffer);
            }
            catch (error) {
                console.warn(`Python service attempt ${attempt}/${this.retryAttempts} failed:`, error);
                if (attempt === this.retryAttempts) {
                    throw new Error(`Python audio service failed after ${this.retryAttempts} attempts: ${error instanceof Error ? error.message : 'Unknown error'}`);
                }
                // Wait before retry
                await this.delay(1000 * attempt);
            }
        }
        throw new Error('All retry attempts exhausted');
    }
    async makeTranscriptionRequest(audioBuffer) {
        // Ensure audio is in WAV format for the Python service
        const wavBuffer = this.ensureWAVFormat(audioBuffer);
        // Create form data for multipart upload
        const formData = new form_data_1.default();
        formData.append('audio', wavBuffer, {
            filename: 'audio.wav',
            contentType: 'audio/wav'
        });
        const response = await axios_1.default.post(`${this.pythonServiceUrl}/transcribe`, formData, {
            headers: {
                ...formData.getHeaders(),
                'Accept': 'application/json'
            },
            timeout: this.timeout,
            maxContentLength: Infinity,
            maxBodyLength: Infinity
        });
        if (response.status !== 200) {
            throw new Error(`Python service returned status ${response.status}: ${response.statusText}`);
        }
        const result = response.data;
        // Normalize the response format
        return {
            text: result.text || result.transcription || '',
            language: result.language || 'auto',
            confidence: result.confidence || 1.0,
            duration: result.duration || 0
        };
    }
    ensureWAVFormat(audioBuffer) {
        const { isValid, format } = audioUtils_1.AudioUtils.validateAudioFormat(audioBuffer);
        if (isValid && format === 'wav') {
            return audioBuffer;
        }
        // Convert PCM to WAV if needed
        return audioUtils_1.AudioUtils.pcmToWAV(audioBuffer, 16000, 1, 16);
    }
    async processAudioWithSpectralGating(audioBuffer) {
        console.log(`🔊 Sending audio for spectral gating to Python service`);
        try {
            const wavBuffer = this.ensureWAVFormat(audioBuffer);
            const formData = new form_data_1.default();
            formData.append('audio', wavBuffer, {
                filename: 'audio.wav',
                contentType: 'audio/wav'
            });
            const response = await axios_1.default.post(`${this.pythonServiceUrl}/spectral-gate`, formData, {
                headers: {
                    ...formData.getHeaders()
                },
                timeout: this.timeout,
                responseType: 'arraybuffer'
            });
            if (response.status !== 200) {
                console.warn('Spectral gating failed, returning original audio');
                return audioBuffer;
            }
            return Buffer.from(response.data);
        }
        catch (error) {
            console.warn('Spectral gating service failed, returning original audio:', error);
            return audioBuffer;
        }
    }
    async checkHealth() {
        try {
            const response = await axios_1.default.get(`${this.pythonServiceUrl}/health`, {
                timeout: 5000
            });
            const isHealthy = response.status === 200 && response.data?.status === 'healthy';
            console.log(`🐍 Python service health: ${isHealthy ? '✅ Healthy' : '❌ Unhealthy'}`);
            return isHealthy;
        }
        catch (error) {
            console.warn('Python service health check failed:', error);
            return false;
        }
    }
    async getServiceInfo() {
        try {
            const response = await axios_1.default.get(`${this.pythonServiceUrl}/info`, {
                timeout: 5000
            });
            return response.data;
        }
        catch (error) {
            console.warn('Could not get Python service info:', error);
            return null;
        }
    }
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    getPythonServiceUrl() {
        return this.pythonServiceUrl;
    }
}
exports.PythonAudioService = PythonAudioService;
//# sourceMappingURL=pythonAudioService.js.map