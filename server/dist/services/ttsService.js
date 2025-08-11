"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.TTSService = void 0;
const axios_1 = __importDefault(require("axios"));
class TTSService {
    constructor() {
        this.elevenlabsApiKey = process.env.ELEVENLABS_API_KEY || '';
        this.voiceId = process.env.ELEVENLABS_VOICE_ID || 'pNInz6obpgDQGcFmaJgB'; // Adam voice
        this.model = process.env.ELEVENLABS_MODEL || 'eleven_multilingual_v2';
        this.provider = 'elevenlabs';
        if (!this.elevenlabsApiKey) {
            throw new Error('ElevenLabs API key is required for TTS service');
        }
    }
    async generateTTS(aiResponse) {
        try {
            console.log(`Generating TTS using ${this.provider} for text: "${aiResponse.text.substring(0, 50)}..."`);
            return await this.generateElevenLabsTTS(aiResponse.text, aiResponse.language);
        }
        catch (error) {
            console.error('TTS generation failed:', error);
            throw new Error(`TTS generation failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    async generateElevenLabsTTS(text, language) {
        const url = `https://api.elevenlabs.io/v1/text-to-speech/${this.voiceId}`;
        const requestBody = {
            text: text,
            model_id: this.model,
            voice_settings: {
                stability: parseFloat(process.env.ELEVENLABS_STABILITY || '0.5'),
                similarity_boost: parseFloat(process.env.ELEVENLABS_SIMILARITY_BOOST || '0.75'),
                style: 0.0,
                use_speaker_boost: true
            }
        };
        const response = await axios_1.default.post(url, requestBody, {
            headers: {
                'Accept': 'audio/mpeg',
                'xi-api-key': this.elevenlabsApiKey,
                'Content-Type': 'application/json'
            },
            responseType: 'arraybuffer'
        });
        if (response.status !== 200) {
            throw new Error(`ElevenLabs API returned status ${response.status}`);
        }
        return {
            audioData: response.data,
            format: 'mp3',
            contentType: 'audio/mpeg',
            duration: this.estimateAudioDuration(text)
        };
    }
    estimateAudioDuration(text) {
        const wordsPerMinute = 150;
        const words = text.split(' ').length;
        const minutes = words / wordsPerMinute;
        return Math.max(minutes * 60, 1);
    }
    async testConnection() {
        try {
            const testResponse = await this.generateElevenLabsTTS('Test', 'en');
            return testResponse.audioData.byteLength > 0;
        }
        catch (error) {
            console.error('TTS connection test failed:', error);
            return false;
        }
    }
    getAvailableVoices() {
        return [
            'pNInz6obpgDQGcFmaJgB', // Adam
            'EXAVITQu4vr4xnSDxMaL', // Bella
            'VR6AewLTigWG4xSOukaG', // Domi
            'AZnzlk1XvdvUeBnXmlld', // Elli
            'MF3mGyEYCl7XYWbV9V6O', // Josh
            '21m00Tcm4TlvDq8ikWAM', // Rachel
            'yoZ06aMxZJJ28mfd3POQ', // Sam
            'pqHfZKP75CvOlQylNhV4' // Bill
        ];
    }
    setVoice(voiceId) {
        if (this.getAvailableVoices().includes(voiceId)) {
            this.voiceId = voiceId;
        }
        else {
            throw new Error(`Invalid voice ID: ${voiceId}`);
        }
    }
    detectLanguageForTTS(text) {
        const hindiRegex = /[\u0900-\u097F]/;
        const englishRegex = /[a-zA-Z]/;
        const hasHindi = hindiRegex.test(text);
        const hasEnglish = englishRegex.test(text);
        if (hasHindi && hasEnglish) {
            return 'auto';
        }
        else if (hasHindi) {
            return 'hi';
        }
        else {
            return 'en';
        }
    }
    cleanup() {
        // No cleanup needed for HTTP-based TTS
    }
}
exports.TTSService = TTSService;
//# sourceMappingURL=ttsService.js.map