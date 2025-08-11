import { TranscriptionResult } from '../types/shared';
export declare class PythonAudioService {
    private pythonServiceUrl;
    private timeout;
    private retryAttempts;
    constructor();
    transcribeAudio(audioBuffer: Buffer): Promise<TranscriptionResult>;
    private makeTranscriptionRequest;
    private ensureWAVFormat;
    processAudioWithSpectralGating(audioBuffer: Buffer): Promise<Buffer>;
    checkHealth(): Promise<boolean>;
    getServiceInfo(): Promise<any>;
    private delay;
    getPythonServiceUrl(): string;
}
//# sourceMappingURL=pythonAudioService.d.ts.map