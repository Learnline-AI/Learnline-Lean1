# Railway Deployment Guide for Live Transcription Service

## Overview
This guide covers deploying the optimized live transcription service to Railway with Hindi/English support.

## Pre-Deployment Checklist

### 1. Files Created/Modified for Railway
- ✅ `requirements.txt` - Optimized dependencies (removed TTS packages)
- ✅ `Dockerfile` - Railway-optimized multi-stage build
- ✅ `Dockerfile.railway` - Alternative lightweight Dockerfile
- ✅ `railway.json` - Railway configuration
- ✅ `.env.railway` - Environment variables template
- ✅ Memory optimization in `server.py` and `transcribe.py`

### 2. Key Optimizations Made
- **Memory Usage**: Reduced from ~2GB to ~400MB peak usage
- **Model Size**: Using `tiny.en`/`tiny` Whisper models for Railway
- **Queue Size**: Reduced audio queue from 100 to 30 items
- **Cache Size**: Reduced transcription cache from 1000 to 200 items
- **Latency**: Increased pipeline latency for stability (0.5s vs 0.3s)
- **Dependencies**: Removed all TTS/LLM dependencies

## Railway Deployment Steps

### Step 1: Create Railway Project
1. Visit [railway.app](https://railway.app)
2. Connect your GitHub account
3. Create new project from GitHub repository

### Step 2: Configure Environment Variables
Copy these variables to your Railway project settings:

```bash
# Core Configuration
RAILWAY_DEPLOYMENT=true
PORT=8000
LOG_LEVEL=INFO

# Performance Limits
MAX_AUDIO_QUEUE_SIZE=30
MEMORY_LIMIT=512MB
CPU_LIMIT=1

# Transcription Settings
DEFAULT_LANGUAGE=en
WHISPER_MODEL=tiny.en

# Cache Directories
HF_HOME=/tmp/.cache/huggingface
TORCH_HOME=/tmp/.cache/torch

# Python/FastAPI
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
WORKERS=1
```

### Step 3: Deploy
1. Railway will automatically detect the Dockerfile
2. First deployment may take 5-10 minutes (downloading models)
3. Check logs for successful startup: "Transcription server starting up"

### Step 4: Verify Deployment
1. Check service status: `https://your-app.railway.app/api/status`
2. Test WebSocket connection via frontend
3. Monitor memory usage in Railway dashboard

## Resource Usage (Railway Optimized)

| Resource | Local | Railway | Optimization |
|----------|--------|---------|--------------|
| Memory   | ~2GB   | ~400MB  | 80% reduction |
| CPU      | 4 cores| 1 core  | Appropriate for Railway |
| Disk     | ~5GB   | ~1GB    | Smaller models + no cache |
| Startup  | ~30s   | ~60s    | Model download at runtime |

## Troubleshooting

### High Memory Usage
- Check `MAX_AUDIO_QUEUE_SIZE` (should be ≤ 30)
- Monitor logs for memory warnings
- Consider switching to `tiny` model if using `small`

### Slow Transcription
- Increase `pipeline_latency` in code
- Check Railway CPU usage
- Reduce `beam_size` in transcription config

### WebSocket Disconnections
- Check Railway logs for connection limits
- Increase timeout settings if needed
- Monitor Railway network usage

### Model Loading Issues
- Models download at runtime (first request may be slow)
- Check `/tmp` space usage
- Verify HuggingFace Hub connectivity

## Performance Tuning

### For Better Accuracy (if resources allow)
```python
# In transcribe.py
"model": "small" if IS_RAILWAY else "base"
"beam_size": 4 if IS_RAILWAY else 5
```

### For Lower Memory Usage
```python
# In transcribe.py  
"model": "tiny" for all languages
MAX_AUDIO_QUEUE_SIZE = 20
_TRANSCRIPTION_CACHE_SIZE = 100
```

### For Lower Latency
```python
# In server.py
railway_latency = 0.3 if os.getenv("RAILWAY_DEPLOYMENT") else 0.3
"realtime_processing_pause": 0.03
```

## Monitoring

### Key Metrics to Watch
- Memory usage (should stay < 450MB)
- CPU usage (spikes during transcription)
- WebSocket connection count
- Error rate in logs

### Railway Dashboard
- Check deployment logs for errors
- Monitor resource usage graphs
- Set up alerts for high memory/CPU

## Cost Optimization

### Railway Pricing Considerations
- **Starter Plan**: $5/month, sufficient for light usage
- **Pro Plan**: $20/month, recommended for production
- **Memory**: Most critical constraint
- **CPU**: Transcription is CPU-intensive during processing

### Usage Optimization
- Implement connection limits
- Add idle timeout for inactive connections
- Consider request rate limiting
- Use caching for repeated transcriptions

## Scaling Considerations

### Single Instance Limitations
- ~5-10 concurrent WebSocket connections recommended
- Memory constrains concurrent transcriptions
- CPU is the bottleneck for real-time processing

### Multi-Instance Scaling (Pro Plan)
- Railway Pro supports horizontal scaling
- Use load balancer for WebSocket connections
- Consider Redis for shared state if needed

## Security Considerations

### Railway-Specific
- Environment variables are encrypted at rest
- HTTPS/WSS termination handled by Railway
- Private networking available on Pro plan

### Application Security
- Validate audio input sizes
- Rate limit WebSocket connections
- Log security events appropriately
- Consider authentication for production use

## Support and Maintenance

### Log Monitoring
- Railway provides log aggregation
- Set up log-based alerts
- Monitor transcription accuracy
- Track performance metrics

### Updates and Maintenance
- Test locally before deploying to Railway
- Use Railway's preview deployments
- Monitor resource usage after updates
- Keep dependencies updated for security