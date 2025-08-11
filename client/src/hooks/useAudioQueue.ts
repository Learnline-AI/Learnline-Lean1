import { useRef, useCallback, useState, useEffect } from 'react';

export interface AudioQueueItem {
  id: string;
  data: ArrayBuffer;
  format: 'mp3' | 'wav' | 'pcm';
  contentType?: string;
  timestamp: number;
}

export interface AudioQueueState {
  isPlaying: boolean;
  currentTrack: string | null;
  queueLength: number;
  error: string | null;
  volume: number;
}

export interface UseAudioQueueReturn {
  state: AudioQueueState;
  addToQueue: (item: AudioQueueItem) => void;
  clearQueue: () => void;
  setVolume: (volume: number) => void;
  skip: () => void;
}

export const useAudioQueue = (): UseAudioQueueReturn => {
  const [state, setState] = useState<AudioQueueState>({
    isPlaying: false,
    currentTrack: null,
    queueLength: 0,
    error: null,
    volume: 0.8
  });

  const queueRef = useRef<AudioQueueItem[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const isProcessingRef = useRef(false);

  useEffect(() => {
    return () => {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current.src = '';
      }
    };
  }, []);

  const playNextInQueue = useCallback(async (): Promise<void> => {
    if (isProcessingRef.current || queueRef.current.length === 0) {
      return;
    }

    isProcessingRef.current = true;

    try {
      const nextItem = queueRef.current.shift();
      if (!nextItem) {
        isProcessingRef.current = false;
        return;
      }

      setState(prev => ({
        ...prev,
        currentTrack: nextItem.id,
        queueLength: queueRef.current.length,
        isPlaying: true,
        error: null
      }));

      const audioElement = await createAudioElement(nextItem);
      currentAudioRef.current = audioElement;

      audioElement.volume = state.volume;

      audioElement.onended = () => {
        setState(prev => ({
          ...prev,
          isPlaying: false,
          currentTrack: null
        }));
        isProcessingRef.current = false;
        playNextInQueue();
      };

      audioElement.onerror = (error) => {
        console.error('Audio playback error:', error);
        setState(prev => ({
          ...prev,
          error: 'Audio playback failed',
          isPlaying: false,
          currentTrack: null
        }));
        isProcessingRef.current = false;
        playNextInQueue();
      };

      audioElement.onloadeddata = () => {
        audioElement.play().catch(error => {
          console.error('Failed to play audio:', error);
          setState(prev => ({
            ...prev,
            error: 'Failed to play audio',
            isPlaying: false,
            currentTrack: null
          }));
          isProcessingRef.current = false;
          playNextInQueue();
        });
      };

    } catch (error) {
      console.error('Error processing audio queue:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Audio processing error',
        isPlaying: false,
        currentTrack: null
      }));
      isProcessingRef.current = false;
      playNextInQueue();
    }
  }, [state.volume]);

  const createAudioElement = async (item: AudioQueueItem): Promise<HTMLAudioElement> => {
    return new Promise((resolve, reject) => {
      try {
        let blob: Blob;
        
        switch (item.format) {
          case 'mp3':
            blob = new Blob([item.data], { type: item.contentType || 'audio/mpeg' });
            break;
          case 'wav':
            blob = new Blob([item.data], { type: 'audio/wav' });
            break;
          case 'pcm':
            const wavBuffer = pcmToWav(new Int16Array(item.data), 16000, 1, 16);
            blob = new Blob([wavBuffer], { type: 'audio/wav' });
            break;
          default:
            throw new Error(`Unsupported audio format: ${item.format}`);
        }

        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);

        audio.onloadedmetadata = () => {
          URL.revokeObjectURL(url);
          resolve(audio);
        };

        audio.onerror = () => {
          URL.revokeObjectURL(url);
          reject(new Error('Failed to load audio'));
        };

      } catch (error) {
        reject(error);
      }
    });
  };

  const pcmToWav = (pcmData: Int16Array, sampleRate: number, channels: number, bitsPerSample: number): ArrayBuffer => {
    const length = pcmData.length;
    const buffer = new ArrayBuffer(44 + length * 2);
    const view = new DataView(buffer);

    const writeString = (offset: number, string: string) => {
      for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
      }
    };

    writeString(0, 'RIFF');
    view.setUint32(4, 36 + length * 2, true);
    writeString(8, 'WAVE');
    writeString(12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, channels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * channels * bitsPerSample / 8, true);
    view.setUint16(32, channels * bitsPerSample / 8, true);
    view.setUint16(34, bitsPerSample, true);
    writeString(36, 'data');
    view.setUint32(40, length * 2, true);

    let offset = 44;
    for (let i = 0; i < length; i++) {
      view.setInt16(offset, pcmData[i], true);
      offset += 2;
    }

    return buffer;
  };

  const addToQueue = useCallback((item: AudioQueueItem): void => {
    queueRef.current.push(item);
    setState(prev => ({
      ...prev,
      queueLength: queueRef.current.length
    }));

    if (!state.isPlaying && !isProcessingRef.current) {
      playNextInQueue();
    }
  }, [state.isPlaying, playNextInQueue]);

  const clearQueue = useCallback((): void => {
    queueRef.current = [];
    
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.src = '';
    }

    setState(prev => ({
      ...prev,
      isPlaying: false,
      currentTrack: null,
      queueLength: 0,
      error: null
    }));

    isProcessingRef.current = false;
  }, []);

  const setVolume = useCallback((volume: number): void => {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    
    setState(prev => ({ ...prev, volume: clampedVolume }));
    
    if (currentAudioRef.current) {
      currentAudioRef.current.volume = clampedVolume;
    }
  }, []);

  const skip = useCallback((): void => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.src = '';
    }

    setState(prev => ({
      ...prev,
      isPlaying: false,
      currentTrack: null
    }));

    isProcessingRef.current = false;
    
    if (queueRef.current.length > 0) {
      playNextInQueue();
    }
  }, [playNextInQueue]);

  return {
    state,
    addToQueue,
    clearQueue,
    setVolume,
    skip
  };
};