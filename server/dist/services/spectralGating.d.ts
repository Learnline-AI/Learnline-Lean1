export declare class SpectralGatingService {
    private isEnabled;
    private pythonScript;
    private tempDir;
    constructor();
    private ensureTempDirectory;
    private createPythonScript;
    processAudio(audioBuffer: Buffer): Promise<Buffer>;
    private applySpectralGating;
    private runPythonScript;
    private cleanupTempFiles;
    isSpectralGatingEnabled(): boolean;
    cleanup(): void;
}
//# sourceMappingURL=spectralGating.d.ts.map