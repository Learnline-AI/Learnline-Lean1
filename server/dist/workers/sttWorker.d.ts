import { TranscriptionResult } from '../types/shared';
export declare class STTWorker {
    private worker;
    private isProcessing;
    private queue;
    constructor();
    private initializeWorker;
    transcribeAudio(audioBuffer: Buffer): Promise<TranscriptionResult>;
    private processQueue;
    cleanup(): void;
}
//# sourceMappingURL=sttWorker.d.ts.map