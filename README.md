# Live Transcription Website 🎙️✍️

**Real-time Hindi/English transcription service optimized for Railway deployment**

A production-ready web application that provides real-time speech-to-text transcription with support for Hindi, English, and Hindi-English code-switching. Built with FastAPI, WebSockets, and optimized for cloud deployment on Railway.

## ✨ Features

- **Real-time transcription**: Live speech-to-text processing via WebSocket connection
- **Multi-language support**: Hindi, English, and Hindi-English code-switching
- **Language switching**: Dynamic language change during active sessions
- **Export functionality**: Download transcriptions as JSON or text files
- **Session management**: Clear history, view recent transcriptions
- **Railway optimized**: Memory-efficient deployment with health monitoring
- **Production ready**: Comprehensive logging, error handling, and monitoring

## 🚀 Quick Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/live-transcription)

### One-Click Railway Deployment

1. Click the "Deploy on Railway" button above
2. Connect your GitHub account and fork this repository
3. Railway will automatically:
   - Build the application using the optimized configuration
   - Install CPU-optimized PyTorch and dependencies
   - Set up health checks and monitoring
   - Deploy to a public URL

4. **Configure Environment Variables** (optional):
   - `DEFAULT_LANGUAGE`: Set to `hi` for Hindi default, `en` for English
   - `MAX_AUDIO_QUEUE_SIZE`: Adjust for memory usage (default: 30)
   - `PIPELINE_LATENCY`: Adjust for performance vs stability (default: 0.5)

### Manual Railway Deployment

1. **Fork this repository**
2. **Connect to Railway**:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Initialize project
   railway init
   ```

3. **Deploy**:
   ```bash
   railway up
   ```

## 🛠️ Local Development Setup

### Prerequisites

- Python 3.11+
- Git
- Audio input device (microphone)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd live-transcription-website
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   cd code
   
   # For CPU-only (Railway compatible)
   pip install torch==2.1.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu
   
   # Install requirements
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   # Copy environment template
   cp ../.env.example .env
   
   # Edit .env with your settings
   ```

5. **Run the application**:
   ```bash
   python server.py
   ```

6. **Access the application**:
   - Open `http://localhost:8000` in your browser
   - Grant microphone permissions
   - Start transcribing!

## 🌐 Usage Instructions

### Web Interface

1. **Access the application** at your Railway URL or `http://localhost:8000`
2. **Grant microphone permissions** when prompted by your browser
3. **Select language** from the dropdown (English, Hindi, or Hindi-English)
4. **Click "Start"** to begin transcription
5. **Speak clearly** into your microphone
6. **View results** in real-time:
   - Partial transcriptions appear as you speak
   - Final transcriptions are confirmed when you pause
   - Language is automatically detected and displayed

### Features

- **Language Switching**: Change transcription language without restarting
- **Export Transcriptions**: Download your session as JSON or text file
- **Clear History**: Reset the session and start fresh
- **View Recent**: See your last 50 transcriptions
- **Real-time Status**: Monitor recording state and transcription progress

### API Endpoints

The service provides a REST API for programmatic access:

- `GET /api/status` - Service status and configuration
- `GET /api/languages` - Supported languages information
- `GET /api/history?limit=50` - Recent transcriptions
- `DELETE /api/history` - Clear transcription history
- `POST /api/export/json` - Export as JSON
- `POST /api/export/text` - Export as text file

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Core Settings
RAILWAY_DEPLOYMENT=true
DEFAULT_LANGUAGE=en
SUPPORTED_LANGUAGES=en,hi,hi-en

# Performance
MAX_AUDIO_QUEUE_SIZE=30
PIPELINE_LATENCY=0.5
WEB_CONCURRENCY=1

# Logging
LOG_LEVEL=INFO
```

### Railway-Specific Configuration

The application is optimized for Railway's platform:

- **Memory Usage**: Optimized for 512MB-1GB RAM limits
- **CPU Processing**: Uses CPU-only PyTorch for compatibility
- **Health Checks**: Automatic monitoring at `/api/status`
- **Logging**: Structured logging for Railway's log aggregation
- **Build Optimization**: Multi-stage Docker build for efficiency

## 📋 Deployment Files

This repository includes production-ready deployment configurations:

- **`railway.json`**: Railway service configuration with health checks and environment setup
- **`nixpacks.toml`**: Build configuration optimized for Python and audio processing
- **`Procfile`**: Process configuration for web service startup
- **`Dockerfile`**: Multi-stage Docker build for Railway deployment
- **`.env.example`**: Complete environment variable template

## 🎯 Language Support

### Supported Languages

1. **English (`en`)**: Full English transcription with optimized models
2. **Hindi (`hi`)**: Native Hindi transcription with Devanagari script support  
3. **Hindi-English (`hi-en`)**: Code-switching between Hindi and English within the same conversation

### Language Switching

- Change languages dynamically during active sessions
- Automatic language detection for mixed conversations
- Optimized models for each language pair
- Seamless switching without connection interruption

## 📊 Monitoring and Troubleshooting

### Health Monitoring

Railway automatically monitors your deployment:

- **Health Check**: `/api/status` endpoint verification
- **Memory Usage**: Tracked and logged for optimization
- **Connection Count**: WebSocket connection monitoring
- **Response Times**: Automatic performance tracking

### Troubleshooting

#### Common Issues

1. **High Memory Usage**:
   - Reduce `MAX_AUDIO_QUEUE_SIZE` in environment variables
   - Monitor `/api/status` for memory statistics
   - Check Railway logs for memory warnings

2. **Transcription Delays**:
   - Increase `PIPELINE_LATENCY` for stability
   - Check network connectivity
   - Verify microphone permissions

3. **Language Detection Issues**:
   - Speak clearly with pauses between sentences
   - Use appropriate language settings
   - Check audio quality and background noise

#### Log Analysis

Access Railway logs to troubleshoot:

```bash
# Railway CLI
railway logs

# Or access via Railway dashboard
```

Look for:
- Memory usage warnings
- WebSocket connection status
- Transcription processing times
- Error messages and stack traces

### Performance Optimization

1. **Memory Management**:
   - Monitor memory usage in Railway dashboard
   - Adjust queue sizes based on usage patterns
   - Clear transcription history regularly

2. **Latency Optimization**:
   - Use appropriate `PIPELINE_LATENCY` settings
   - Optimize network connectivity
   - Consider regional deployment for global users

3. **Audio Quality**:
   - Use good quality microphone
   - Minimize background noise
   - Speak clearly with appropriate volume

## 🔧 Development

### Project Structure

```
live-transcription-website/
├── code/                    # Application source code
│   ├── server.py           # FastAPI server with WebSocket handling
│   ├── transcribe.py       # Speech-to-text processing
│   ├── audio_in.py         # Audio input processing
│   ├── requirements.txt    # Python dependencies
│   └── static/            # Frontend assets
├── railway.json           # Railway deployment configuration
├── nixpacks.toml         # Build system configuration
├── Procfile              # Process configuration
├── Dockerfile            # Container configuration
├── .env.example          # Environment template
└── README.md             # This file
```

### Local Testing

Test Railway-specific features locally:

```bash
# Set Railway environment variables
export RAILWAY_DEPLOYMENT=true
export MAX_AUDIO_QUEUE_SIZE=30

# Run with Railway-like constraints
python server.py
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Test locally with Railway environment variables
4. Submit a pull request with:
   - Clear description of changes
   - Testing results
   - Performance impact assessment

## 📄 License

This project is released under the MIT License. See [LICENSE](./LICENSE) for details.

## 🤝 Support

- **Issues**: Open GitHub issues for bug reports
- **Discussions**: Use GitHub discussions for feature requests
- **Railway Support**: Check Railway documentation for platform-specific issues

## 🚀 Roadmap

- [ ] WebRTC integration for improved audio quality
- [ ] Additional language support (Tamil, Telugu, Gujarati)
- [ ] Real-time collaboration features
- [ ] Mobile app integration
- [ ] Advanced speaker recognition
- [ ] Sentiment analysis integration

---

**Built with ❤️ for seamless multilingual transcription on Railway**