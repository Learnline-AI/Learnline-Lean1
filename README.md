# Learnline V2 - Voice Chat AI

A modern, high-performance voice chat application with AI responses, built using TypeScript, React, and Node.js. This is the second iteration of the Learnline AI Tutor project, featuring a clean architecture and optimized performance.

## 🚀 Features

- **Real-time Voice Detection**: Silero VAD with spectral gating noise reduction
- **Speech-to-Text**: OpenAI Whisper with Hindi/English support
- **AI Responses**: Multi-provider support (OpenAI, Gemini, Claude) with fallbacks
- **Text-to-Speech**: ElevenLabs HTTP API (no streaming complexity)
- **WebSocket Communication**: Robust connection management with reconnection logic
- **Clean Audio Pipeline**: Worker-based processing, proper format handling
- **Modern UI**: React-based frontend with TypeScript

## 🏗️ Architecture

### Simple Flow
1. **Client**: Record audio → Send via WebSocket
2. **Server**: VAD detection → Spectral gating → STT (Whisper) → AI response → TTS (ElevenLabs) → Send audio back
3. **Client**: Receive audio → Play via audio queue

### Technology Stack
- **Backend**: Node.js, Express, Socket.IO, TypeScript
- **Frontend**: React, TypeScript, Vite
- **Audio**: Silero VAD (ONNX), OpenAI Whisper, ElevenLabs HTTP TTS
- **Real-time**: WebSocket connections only

## 📦 Installation

### Prerequisites
- Node.js 18+ 
- Python 3.8+ (for spectral gating)
- Required Python packages: `numpy`, `scipy`

```bash
# Install Python dependencies for spectral gating
pip3 install numpy scipy
```

### Setup

1. **Clone and install dependencies:**
```bash
# Install root dependencies
npm install

# Install server dependencies
cd server && npm install

# Install client dependencies  
cd ../client && npm install
```

2. **Configure environment variables:**
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

3. **Required API Keys:**
```env
# At minimum, you need:
OPENAI_API_KEY=sk-your-openai-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
```

## 🚀 Running the Application

### Development Mode
```bash
# Start both server and client (from root directory)
npm run dev

# Or run separately:
npm run server:dev  # Server on port 3001
npm run client:dev  # Client on port 5173
```

### Production Mode
```bash
# Build everything
npm run build

# Start production server
npm start
```

## 🌐 Access Points

- **Client**: http://localhost:5173
- **Server**: http://localhost:3001  
- **Health Check**: http://localhost:3001/health
- **WebSocket**: ws://localhost:3001

## ⚙️ Configuration Options

### Audio Configuration
```env
WHISPER_MODEL=whisper-1          # OpenAI Whisper model
WHISPER_LANGUAGE=hi              # Hindi/English (hi/en/auto)
SPECTRAL_GATING_ENABLED=true     # Enable noise reduction
```

### AI Provider Configuration
```env
AI_PROVIDER=openai               # openai/gemini/claude
AI_LANGUAGE=auto                 # en/hi/auto
```

### TTS Configuration  
```env
TTS_PROVIDER=elevenlabs
ELEVENLABS_VOICE_ID=pNInz6obpgDQGcFmaJgB  # Adam voice
ELEVENLABS_STABILITY=0.5
ELEVENLABS_SIMILARITY_BOOST=0.75
```

## 🎯 Core Components

### Server Components
- **WebSocket Service**: Connection management, health monitoring
- **VAD Service**: Silero ONNX voice activity detection
- **Spectral Gating**: Python-based noise reduction
- **STT Worker**: Worker-based Whisper processing
- **AI Service**: Multi-provider abstraction with fallbacks
- **TTS Service**: ElevenLabs HTTP API integration

### Client Components
- **useWebAudio**: Web Audio API integration
- **useAudioQueue**: Audio playback queue management
- **useWebSocketAudio**: WebSocket to audio pipeline
- **Chat Component**: Clean voice chat interface

## 🔧 Development

### Project Structure
```
├── server/                 # Node.js backend
│   ├── services/          # Core business logic
│   ├── workers/           # Background processing
│   ├── utils/             # Utility functions
│   └── config/            # Configuration
├── client/                # React frontend  
│   └── src/
│       ├── hooks/         # Audio/WebSocket hooks
│       ├── pages/         # Chat interface
│       └── types/         # TypeScript definitions
└── shared/                # Shared types
```

### Key Features Implemented
✅ Robust WebSocket connection management  
✅ Silero VAD with spectral gating  
✅ Worker-based STT processing  
✅ Multi-provider AI responses  
✅ HTTP-only TTS (no streaming issues)  
✅ Client-side audio queue management  

### Features Excluded (Bloat Removed)
❌ ElevenLabs WebSocket streaming  
❌ Google TTS streaming  
❌ MediaSource streaming player  
❌ Multiple chat variants  
❌ RAG system  
❌ Database persistence  

## 🧪 Testing

1. **Check server health:**
```bash
curl http://localhost:3001/health
```

2. **Test WebSocket connection:**
   - Open browser dev tools
   - Check WebSocket connections tab
   - Should show successful connection to `ws://localhost:3001`

3. **Test audio pipeline:**
   - Click microphone button
   - Speak clearly in Hindi or English
   - Check console for processing logs
   - Verify AI response and audio playback

## 🐛 Troubleshooting

### Common Issues

**VAD Service fails to initialize:**
- VAD will use fallback energy detection
- Download Silero model if needed

**Python spectral gating fails:**
- Install required packages: `pip3 install numpy scipy`  
- Set `SPECTRAL_GATING_ENABLED=false` to disable

**WebSocket connection issues:**
- Check CORS configuration
- Verify CLIENT_URL environment variable

**Audio playback issues:**
- Check browser permissions for microphone
- Ensure HTTPS in production for getUserMedia

## 📝 Logs

The application provides detailed console logging:
- 🔗 WebSocket connections
- 🎤 Audio session events  
- 📝 Speech-to-text results
- 🤖 AI response generation
- 🔊 TTS audio generation

## 🔒 Security Notes

- All API keys in environment variables
- No secrets in client-side code
- CORS properly configured
- Input validation on audio data

## 📈 Performance

- Worker-based STT processing (non-blocking)
- Connection pooling and health monitoring  
- Audio format optimization
- Memory-efficient audio processing
- Queue-based audio playback

---

**Built with clean, proven components for optimal performance and reliability.**
