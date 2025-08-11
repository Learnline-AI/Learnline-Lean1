import * as fs from 'fs';

export class AudioUtils {
  static createWAVHeader(
    sampleRate: number,
    channels: number,
    bitsPerSample: number,
    dataLength: number
  ): Buffer {
    const header = Buffer.alloc(44);
    
    header.write('RIFF', 0);
    header.writeUInt32LE(36 + dataLength, 4);
    header.write('WAVE', 8);
    header.write('fmt ', 12);
    header.writeUInt32LE(16, 16);
    header.writeUInt16LE(1, 20);
    header.writeUInt16LE(channels, 22);
    header.writeUInt32LE(sampleRate, 24);
    header.writeUInt32LE(sampleRate * channels * bitsPerSample / 8, 28);
    header.writeUInt16LE(channels * bitsPerSample / 8, 32);
    header.writeUInt16LE(bitsPerSample, 34);
    header.write('data', 36);
    header.writeUInt32LE(dataLength, 40);
    
    return header;
  }

  static pcmToWAV(
    pcmData: Buffer,
    sampleRate: number = 16000,
    channels: number = 1,
    bitsPerSample: number = 16
  ): Buffer {
    const header = this.createWAVHeader(sampleRate, channels, bitsPerSample, pcmData.length);
    return Buffer.concat([header, pcmData]);
  }

  static validateAudioFormat(buffer: Buffer): { isValid: boolean; format?: string } {
    if (buffer.length < 12) {
      return { isValid: false };
    }

    const riffHeader = buffer.toString('ascii', 0, 4);
    const waveHeader = buffer.toString('ascii', 8, 12);
    
    if (riffHeader === 'RIFF' && waveHeader === 'WAVE') {
      return { isValid: true, format: 'wav' };
    }

    const mp3Header = buffer.readUInt16BE(0);
    if ((mp3Header & 0xFFE0) === 0xFFE0) {
      return { isValid: true, format: 'mp3' };
    }

    return { isValid: false };
  }

  static arrayBufferToBuffer(arrayBuffer: ArrayBuffer): Buffer {
    return Buffer.from(arrayBuffer);
  }

  static bufferToArrayBuffer(buffer: Buffer): ArrayBuffer {
    const arrayBuffer = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
    return arrayBuffer as ArrayBuffer;
  }

  static normalizeAudio(buffer: Buffer): Buffer {
    const samples = new Int16Array(buffer.buffer, buffer.byteOffset, buffer.length / 2);
    let max = 0;
    
    for (let i = 0; i < samples.length; i++) {
      max = Math.max(max, Math.abs(samples[i]));
    }
    
    if (max === 0) return buffer;
    
    const normalizedSamples = new Int16Array(samples.length);
    const scale = 32767 / max;
    
    for (let i = 0; i < samples.length; i++) {
      normalizedSamples[i] = Math.round(samples[i] * scale);
    }
    
    return Buffer.from(normalizedSamples.buffer);
  }

  static resampleAudio(
    buffer: Buffer,
    fromSampleRate: number,
    toSampleRate: number,
    channels: number = 1
  ): Buffer {
    if (fromSampleRate === toSampleRate) {
      return buffer;
    }

    const inputSamples = new Int16Array(buffer.buffer, buffer.byteOffset, buffer.length / 2);
    const ratio = fromSampleRate / toSampleRate;
    const outputLength = Math.floor(inputSamples.length / ratio);
    const outputSamples = new Int16Array(outputLength);

    for (let i = 0; i < outputLength; i++) {
      const srcIndex = i * ratio;
      const srcIndexFloor = Math.floor(srcIndex);
      const srcIndexCeil = Math.min(srcIndexFloor + 1, inputSamples.length - 1);
      const fraction = srcIndex - srcIndexFloor;

      outputSamples[i] = Math.round(
        inputSamples[srcIndexFloor] * (1 - fraction) +
        inputSamples[srcIndexCeil] * fraction
      );
    }

    return Buffer.from(outputSamples.buffer);
  }

  static splitAudioIntoChunks(buffer: Buffer, chunkDurationMs: number, sampleRate: number): Buffer[] {
    const samplesPerChunk = Math.floor((chunkDurationMs / 1000) * sampleRate * 2);
    const chunks: Buffer[] = [];
    
    for (let i = 0; i < buffer.length; i += samplesPerChunk) {
      const end = Math.min(i + samplesPerChunk, buffer.length);
      chunks.push(buffer.slice(i, end));
    }
    
    return chunks;
  }

  static calculateRMS(buffer: Buffer): number {
    const samples = new Int16Array(buffer.buffer, buffer.byteOffset, buffer.length / 2);
    let sum = 0;
    
    for (let i = 0; i < samples.length; i++) {
      sum += samples[i] * samples[i];
    }
    
    return Math.sqrt(sum / samples.length);
  }

  static async saveAudioFile(buffer: Buffer, filePath: string): Promise<void> {
    return new Promise((resolve, reject) => {
      fs.writeFile(filePath, buffer, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }
}