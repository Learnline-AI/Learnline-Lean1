import React, { useState, useEffect, useRef } from 'react';
import { useWebSocketAudio } from '../hooks/useWebSocketAudio';

const Chat: React.FC = () => {
  const {
    connectionState,
    isRecording,
    audioLevel,
    transcription,
    aiResponse,
    startVoiceChat,
    stopVoiceChat,
    clearHistory,
    audioQueue
  } = useWebSocketAudio();

  const [messages, setMessages] = useState<Array<{
    id: string;
    type: 'user' | 'ai';
    content: string;
    timestamp: number;
  }>>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (transcription) {
      setMessages(prev => [...prev, {
        id: `user-${Date.now()}`,
        type: 'user',
        content: transcription.text,
        timestamp: Date.now()
      }]);
    }
  }, [transcription]);

  useEffect(() => {
    if (aiResponse) {
      setMessages(prev => [...prev, {
        id: `ai-${Date.now()}`,
        type: 'ai',
        content: aiResponse.text,
        timestamp: Date.now()
      }]);
    }
  }, [aiResponse]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleVoiceToggle = async () => {
    try {
      if (isRecording) {
        stopVoiceChat();
      } else {
        await startVoiceChat();
      }
    } catch (error) {
      console.error('Voice chat error:', error);
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    clearHistory();
  };

  const getConnectionStatusColor = () => {
    switch (connectionState.status) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'error': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getQualityIndicator = () => {
    switch (connectionState.quality) {
      case 'excellent': return '🟢';
      case 'good': return '🟡';
      case 'poor': return '🔴';
      default: return '⚪';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold text-gray-800">
              Voice Chat AI
            </h1>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">Connection:</span>
                <span className={`text-sm font-medium ${getConnectionStatusColor()}`}>
                  {connectionState.status}
                </span>
                <span className="text-sm">{getQualityIndicator()}</span>
              </div>
              {connectionState.reconnectAttempts > 0 && (
                <span className="text-xs text-orange-500">
                  Reconnect attempts: {connectionState.reconnectAttempts}
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-4xl mx-auto w-full px-4 py-6">
        <div className="bg-white rounded-lg shadow-sm h-[600px] flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 mt-20">
                <div className="text-4xl mb-4">🎤</div>
                <h2 className="text-lg font-medium mb-2">Start a Voice Conversation</h2>
                <p className="text-sm">
                  Click the microphone button below to start talking with the AI assistant.
                </p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      message.type === 'user'
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-800'
                    }`}
                  >
                    <div className="flex items-start space-x-2">
                      <span className="text-xs opacity-75">
                        {message.type === 'user' ? '👤' : '🤖'}
                      </span>
                      <div>
                        <p className="text-sm">{message.content}</p>
                        <span className="text-xs opacity-50">
                          {new Date(message.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t bg-gray-50 p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">Audio Queue:</span>
                  <span className="text-sm font-medium">
                    {audioQueue.state.queueLength} items
                  </span>
                  {audioQueue.state.isPlaying && (
                    <span className="text-xs text-green-600 flex items-center">
                      ▶️ Playing
                    </span>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">Volume:</span>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={audioQueue.state.volume}
                    onChange={(e) => audioQueue.setVolume(parseFloat(e.target.value))}
                    className="w-20"
                  />
                  <span className="text-xs text-gray-500">
                    {Math.round(audioQueue.state.volume * 100)}%
                  </span>
                </div>
              </div>
              <button
                onClick={handleClearChat}
                className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
              >
                Clear Chat
              </button>
            </div>

            <div className="flex items-center justify-center space-x-4">
              {isRecording && (
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-1">
                    <div className="w-4 h-4 bg-red-500 rounded-full animate-pulse"></div>
                    <span className="text-sm text-red-600 font-medium">Recording</span>
                  </div>
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full transition-all duration-100"
                      style={{ width: `${audioLevel * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <button
                onClick={handleVoiceToggle}
                disabled={connectionState.status !== 'connected'}
                className={`w-16 h-16 rounded-full flex items-center justify-center text-white font-semibold transition-all duration-200 ${
                  connectionState.status !== 'connected'
                    ? 'bg-gray-400 cursor-not-allowed'
                    : isRecording
                    ? 'bg-red-500 hover:bg-red-600 shadow-lg'
                    : 'bg-blue-500 hover:bg-blue-600 shadow-md hover:shadow-lg'
                }`}
              >
                {connectionState.status !== 'connected' ? (
                  '⏳'
                ) : isRecording ? (
                  '🔴'
                ) : (
                  '🎤'
                )}
              </button>

              {audioQueue.state.isPlaying && (
                <button
                  onClick={audioQueue.skip}
                  className="px-3 py-1 text-sm bg-gray-200 hover:bg-gray-300 rounded-md transition-colors"
                >
                  Skip ⏭️
                </button>
              )}
            </div>

            {connectionState.status !== 'connected' && (
              <div className="mt-4 text-center">
                <p className="text-sm text-gray-500">
                  {connectionState.status === 'connecting' && 'Connecting to server...'}
                  {connectionState.status === 'error' && 'Connection failed. Retrying...'}
                  {connectionState.status === 'disconnected' && 'Disconnected from server'}
                </p>
              </div>
            )}

            {audioQueue.state.error && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-600">{audioQueue.state.error}</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Chat;