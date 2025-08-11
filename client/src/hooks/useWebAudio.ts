import { useRef, useCallback, useState, useEffect } from 'react';

export interface WebAudioState {
  isRecording: boolean;
  audioLevel: number;
  error: string | null;
  isSupported: boolean;
}

export interface UseWebAudioReturn {
  state: WebAudioState;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  onAudioData: (callback: (data: Float32Array) => void) => void;
}

export const useWebAudio = (): UseWebAudioReturn => {
  const [state, setState] = useState<WebAudioState>({
    isRecording: false,
    audioLevel: 0,
    error: null,
    isSupported: false
  });

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const audioDataCallbackRef = useRef<((data: Float32Array) => void) | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const isSupported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    setState(prev => ({ ...prev, isSupported }));

    return () => {
      stopRecording();
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  const updateAudioLevel = useCallback(() => {
    if (!analyserRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    analyserRef.current.getByteFrequencyData(dataArray);

    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) {
      sum += dataArray[i];
    }
    const average = sum / dataArray.length;
    const normalizedLevel = Math.min(average / 128, 1);

    setState(prev => ({ ...prev, audioLevel: normalizedLevel }));
    
    if (state.isRecording) {
      animationFrameRef.current = requestAnimationFrame(updateAudioLevel);
    }
  }, [state.isRecording]);

  const startRecording = useCallback(async (): Promise<void> => {
    try {
      setState(prev => ({ ...prev, error: null }));

      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('getUserMedia is not supported in this browser');
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      });

      mediaStreamRef.current = stream;

      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 16000
      });

      if (audioContext.state === 'suspended') {
        await audioContext.resume();
      }

      audioContextRef.current = audioContext;

      const source = audioContext.createMediaStreamSource(stream);
      sourceRef.current = source;

      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;
      analyserRef.current = analyser;

      const processor = audioContext.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (event) => {
        const inputData = event.inputBuffer.getChannelData(0);
        
        if (audioDataCallbackRef.current) {
          const pcmData = new Float32Array(inputData.length);
          pcmData.set(inputData);
          audioDataCallbackRef.current(pcmData);
        }
      };

      source.connect(analyser);
      analyser.connect(processor);
      processor.connect(audioContext.destination);

      setState(prev => ({ ...prev, isRecording: true }));
      updateAudioLevel();

      console.log('🎤 Recording started successfully');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setState(prev => ({ 
        ...prev, 
        error: errorMessage,
        isRecording: false 
      }));
      console.error('Failed to start recording:', error);
    }
  }, [updateAudioLevel]);

  const stopRecording = useCallback((): void => {
    try {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }

      if (processorRef.current) {
        processorRef.current.disconnect();
        processorRef.current = null;
      }

      if (sourceRef.current) {
        sourceRef.current.disconnect();
        sourceRef.current = null;
      }

      if (analyserRef.current) {
        analyserRef.current.disconnect();
        analyserRef.current = null;
      }

      if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }

      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => {
          track.stop();
        });
        mediaStreamRef.current = null;
      }

      setState(prev => ({ 
        ...prev, 
        isRecording: false, 
        audioLevel: 0 
      }));

      console.log('🔇 Recording stopped');
    } catch (error) {
      console.error('Error stopping recording:', error);
      setState(prev => ({ 
        ...prev, 
        error: error instanceof Error ? error.message : 'Error stopping recording',
        isRecording: false 
      }));
    }
  }, []);

  const onAudioData = useCallback((callback: (data: Float32Array) => void): void => {
    audioDataCallbackRef.current = callback;
  }, []);

  return {
    state,
    startRecording,
    stopRecording,
    onAudioData
  };
};