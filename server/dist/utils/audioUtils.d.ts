export declare class AudioUtils {
    static createWAVHeader(sampleRate: number, channels: number, bitsPerSample: number, dataLength: number): Buffer;
    static pcmToWAV(pcmData: Buffer, sampleRate?: number, channels?: number, bitsPerSample?: number): Buffer;
    static validateAudioFormat(buffer: Buffer): {
        isValid: boolean;
        format?: string;
    };
    static arrayBufferToBuffer(arrayBuffer: ArrayBuffer): Buffer;
    static bufferToArrayBuffer(buffer: Buffer): ArrayBuffer;
    static normalizeAudio(buffer: Buffer): Buffer;
    static resampleAudio(buffer: Buffer, fromSampleRate: number, toSampleRate: number, channels?: number): Buffer;
    static splitAudioIntoChunks(buffer: Buffer, chunkDurationMs: number, sampleRate: number): Buffer[];
    static calculateRMS(buffer: Buffer): number;
    static saveAudioFile(buffer: Buffer, filePath: string): Promise<void>;
}
//# sourceMappingURL=audioUtils.d.ts.map