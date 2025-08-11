import { spawn, ChildProcess } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import { AudioUtils } from '../utils/audioUtils';

export class SpectralGatingService {
  private isEnabled: boolean;
  private pythonScript: string;
  private tempDir: string;

  constructor() {
    this.isEnabled = process.env.SPECTRAL_GATING_ENABLED === 'true';
    this.tempDir = path.join(__dirname, '../temp');
    this.pythonScript = `
import numpy as np
import scipy.signal
import scipy.io.wavfile
import sys
import os

def spectral_gate(audio_data, sample_rate, alpha=1.2, beta=0.15, gamma=1.5):
    """
    Apply spectral gating noise reduction
    """
    # Convert to float
    if audio_data.dtype != np.float32:
        audio_data = audio_data.astype(np.float32) / 32768.0
    
    # Parameters
    frame_len = int(0.025 * sample_rate)  # 25ms frames
    frame_shift = int(0.010 * sample_rate)  # 10ms shift
    
    # Add padding
    padded_len = len(audio_data) + frame_len
    padded_audio = np.pad(audio_data, (frame_len//2, frame_len//2), mode='reflect')
    
    # Create frames
    frames = []
    for i in range(0, len(padded_audio) - frame_len + 1, frame_shift):
        frame = padded_audio[i:i+frame_len] * np.hanning(frame_len)
        frames.append(frame)
    
    frames = np.array(frames)
    
    # FFT
    fft_frames = np.fft.rfft(frames, axis=1)
    magnitude = np.abs(fft_frames)
    phase = np.angle(fft_frames)
    
    # Estimate noise (first few frames)
    noise_frames = magnitude[:5]  # First 5 frames as noise estimate
    noise_profile = np.mean(noise_frames, axis=0) + 1e-10
    
    # Apply spectral gating
    for i in range(len(magnitude)):
        snr = magnitude[i] / noise_profile
        
        # Gating function
        gain = np.where(snr > alpha, 1.0, 
                       np.where(snr > beta, 
                               ((snr - beta) / (alpha - beta)) ** gamma, 
                               0.0))
        
        magnitude[i] *= gain
    
    # Reconstruct signal
    gated_fft = magnitude * np.exp(1j * phase)
    gated_frames = np.fft.irfft(gated_fft, axis=1)
    
    # Overlap-add reconstruction
    output_len = len(audio_data)
    output = np.zeros(output_len + frame_len)
    
    for i, frame in enumerate(gated_frames):
        start_idx = i * frame_shift
        end_idx = start_idx + frame_len
        if end_idx <= len(output):
            output[start_idx:end_idx] += frame * np.hanning(frame_len)
    
    # Remove padding and normalize
    result = output[frame_len//2:frame_len//2 + output_len]
    
    # Convert back to int16
    result = np.clip(result * 32768.0, -32768, 32767).astype(np.int16)
    
    return result

if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        sample_rate, audio_data = scipy.io.wavfile.read(input_file)
        
        # Ensure mono
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Apply spectral gating
        cleaned_audio = spectral_gate(audio_data, sample_rate)
        
        # Write output
        scipy.io.wavfile.write(output_file, sample_rate, cleaned_audio)
        
        print("SUCCESS")
    except Exception as e:
        print(f"ERROR: {str(e)}")
        sys.exit(1)
`;

    this.ensureTempDirectory();
    this.createPythonScript();
  }

  private ensureTempDirectory() {
    if (!fs.existsSync(this.tempDir)) {
      fs.mkdirSync(this.tempDir, { recursive: true });
    }
  }

  private createPythonScript() {
    const scriptPath = path.join(this.tempDir, 'spectral_gating.py');
    fs.writeFileSync(scriptPath, this.pythonScript);
  }

  async processAudio(audioBuffer: Buffer): Promise<Buffer> {
    if (!this.isEnabled) {
      return audioBuffer;
    }

    try {
      return await this.applySpectralGating(audioBuffer);
    } catch (error) {
      console.warn('Spectral gating failed, returning original audio:', error);
      return audioBuffer;
    }
  }

  private async applySpectralGating(audioBuffer: Buffer): Promise<Buffer> {
    const timestamp = Date.now();
    const inputPath = path.join(this.tempDir, `input_${timestamp}.wav`);
    const outputPath = path.join(this.tempDir, `output_${timestamp}.wav`);
    const scriptPath = path.join(this.tempDir, 'spectral_gating.py');

    try {
      const wavBuffer = AudioUtils.pcmToWAV(audioBuffer, 16000, 1, 16);
      fs.writeFileSync(inputPath, wavBuffer);

      await this.runPythonScript(scriptPath, inputPath, outputPath);

      if (fs.existsSync(outputPath)) {
        const processedWav = fs.readFileSync(outputPath);
        
        const processedPcm = processedWav.slice(44);
        
        this.cleanupTempFiles(inputPath, outputPath);
        
        return processedPcm;
      } else {
        throw new Error('Output file not generated');
      }
    } catch (error) {
      this.cleanupTempFiles(inputPath, outputPath);
      throw error;
    }
  }

  private runPythonScript(scriptPath: string, inputPath: string, outputPath: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const python = spawn('python3', [scriptPath, inputPath, outputPath], {
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      python.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      python.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      python.on('close', (code) => {
        if (code === 0 && stdout.includes('SUCCESS')) {
          resolve();
        } else {
          reject(new Error(`Python script failed: ${stderr || stdout}`));
        }
      });

      python.on('error', (error) => {
        reject(new Error(`Failed to spawn python process: ${error.message}`));
      });

      setTimeout(() => {
        python.kill();
        reject(new Error('Python script timeout'));
      }, 10000);
    });
  }

  private cleanupTempFiles(...filePaths: string[]) {
    filePaths.forEach(filePath => {
      if (fs.existsSync(filePath)) {
        try {
          fs.unlinkSync(filePath);
        } catch (error) {
          console.warn(`Failed to cleanup temp file ${filePath}:`, error);
        }
      }
    });
  }

  public isSpectralGatingEnabled(): boolean {
    return this.isEnabled;
  }

  public cleanup() {
    try {
      if (fs.existsSync(this.tempDir)) {
        const files = fs.readdirSync(this.tempDir);
        files.forEach(file => {
          const filePath = path.join(this.tempDir, file);
          if (file.includes('input_') || file.includes('output_')) {
            fs.unlinkSync(filePath);
          }
        });
      }
    } catch (error) {
      console.warn('Error during spectral gating cleanup:', error);
    }
  }
}