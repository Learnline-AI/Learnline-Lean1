export * from '../../../shared/types';

export interface ClientConfig {
  serverUrl: string;
  reconnectionAttempts: number;
  reconnectionDelay: number;
  connectionTimeout: number;
}

declare global {
  interface Window {
    webkitAudioContext: typeof AudioContext;
  }
}