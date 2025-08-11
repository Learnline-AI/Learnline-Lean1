# Optimized Transcription Processor - Complete Guide

## Overview

The `transcribe.py` file has been completely optimized for live Hindi/English transcription with focus on accuracy, performance, and multilingual support. All TTS-related components have been removed to create a pure transcription solution.

## 🚀 Key Features

### ✅ **Completed Optimizations**

1. **Multi-language Support**
   - English (`en`)
   - Hindi (`hi`) 
   - Hindi-English Code-switching (`hi-en`)
   - Automatic language detection and switching

2. **Real-time Processing**
   - Optimized for continuous transcription
   - Low-latency processing (< 300ms)
   - Enhanced confidence scoring
   - Timestamp tracking with microsecond precision

3. **Export Functionality**
   - JSON export with comprehensive metadata
   - CSV export for data analysis
   - TXT export for human reading
   - Auto-save functionality every N transcriptions

4. **Performance Optimizations**
   - Removed all TTS-related code
   - Enhanced text similarity detection
   - Intelligent deduplication
   - Performance monitoring and statistics

5. **Language Detection**
   - Automatic Hindi/English detection
   - Code-switching recognition
   - Mixed script analysis
   - Smart language switching logic

## 📋 Installation Requirements

```bash
# Core dependencies
pip install RealtimeSTT
pip install torch transformers
pip install scipy numpy

# For language detection (recommended)
pip install langdetect

# For enhanced audio processing
pip install soundfile librosa
```

## 🔧 Usage Examples

### Basic English Transcription

```python
from transcribe import OptimizedTranscriptionProcessor, TranscriptionResult

def on_final_transcription(result: TranscriptionResult):
    print(f"Final: {result.text} (confidence: {result.confidence:.2f})")

processor = OptimizedTranscriptionProcessor(
    source_language="en",
    full_transcription_callback=on_final_transcription,
    continuous_mode=True
)

# Setup transcription loop
processor.transcribe_loop()

# Feed audio data
processor.feed_audio(audio_chunk)

# Shutdown when done
processor.shutdown()
```

### Hindi-English Code-switching with Export

```python
from pathlib import Path
from transcribe import OptimizedTranscriptionProcessor

def on_language_switch(language):
    print(f"Language switched to: {language}")

processor = OptimizedTranscriptionProcessor(
    source_language="hi-en",  # Code-switching mode
    language_detection_callback=on_language_switch,
    auto_language_switching=True,
    export_path=Path("./transcriptions/session.json"),
    continuous_mode=True
)
```

### Advanced Configuration

```python
# Custom recorder configuration
custom_config = {
    "beam_size": 10,  # Higher accuracy
    "temperature": 0.0,  # More deterministic
    "vad_filter": True  # Voice activity detection
}

processor = OptimizedTranscriptionProcessor(
    source_language="hi-en",
    recorder_config=custom_config,
    pipeline_latency=0.2,  # Faster response
    continuous_mode=True
)
```

## 📊 New Data Structures

### TranscriptionResult

```python
class TranscriptionResult:
    def __init__(self, text, confidence, timestamp, language, is_final, duration, word_count, has_mixed_language):
        self.text = text                    # Transcribed text
        self.confidence = confidence        # Confidence score (0-1)
        self.timestamp = timestamp          # Unix timestamp
        self.language = language           # Detected language
        self.is_final = is_final          # Final vs partial result
        self.duration = duration          # Audio duration in seconds
        self.word_count = word_count      # Number of words
        self.has_mixed_language = has_mixed_language  # Code-switching detected
        self.datetime = datetime.fromtimestamp(timestamp)  # Human readable time
```

## 🌐 Language Configuration

### Supported Languages

```python
LANGUAGE_MODELS = {
    "en": {
        "model": "base.en",           # English-only model
        "name": "English",
        "whisper_code": "en"
    },
    "hi": {
        "model": "base",              # Multilingual model
        "name": "Hindi", 
        "whisper_code": "hi"
    },
    "hi-en": {
        "model": "base",              # Best for code-switching
        "name": "Hindi-English (Code-switching)",
        "whisper_code": None         # Auto-detect
    }
}
```

### Language Switching

```python
# Manual language switching
success = processor.switch_language("hi")

# Automatic switching based on content
processor.auto_language_switching = True
```

## 📁 Export Functionality

### Export Formats

#### JSON Export (with metadata)
```python
processor.export_transcriptions(
    path="session.json",
    format="json",
    include_metadata=True
)
```

Output structure:
```json
{
    "metadata": {
        "export_timestamp": "2024-01-15T10:30:00",
        "total_transcriptions": 150,
        "languages": ["en", "hi", "hi-en"],
        "total_duration": 450.5,
        "average_confidence": 0.87
    },
    "transcriptions": [
        {
            "text": "Hello, how are you?",
            "confidence": 0.95,
            "timestamp": 1642248600.123,
            "datetime": "2024-01-15T10:30:00.123",
            "language": "en",
            "is_final": true,
            "duration": 2.5,
            "word_count": 4,
            "has_mixed_language": false
        }
    ]
}
```

#### CSV Export
```python
processor.export_transcriptions(
    path="session.csv",
    format="csv"
)
```

#### Text Export
```python
processor.export_transcriptions(
    path="session.txt", 
    format="txt",
    include_metadata=True
)
```

### Auto-save Configuration

```python
processor = OptimizedTranscriptionProcessor(
    export_path=Path("./transcriptions/auto_save.json"),
    # Auto-saves every 100 final transcriptions
)
```

## 🎯 Performance Features

### Confidence Scoring

The system now provides intelligent confidence scoring based on:

- Text length and complexity
- Character diversity
- Language consistency
- Audio quality (SNR estimation)
- Repetition detection
- Mixed script analysis

```python
def on_confidence_update(confidence):
    if confidence < 0.5:
        print("⚠️ Low confidence transcription")
    elif confidence > 0.9:
        print("✅ High confidence transcription")

processor = OptimizedTranscriptionProcessor(
    confidence_callback=on_confidence_update
)
```

### Performance Monitoring

```python
# Get comprehensive statistics
stats = processor.get_statistics()
print(f"Total transcriptions: {stats['total_transcriptions']}")
print(f"Average confidence: {stats['average_confidence']:.2f}")
print(f"Language distribution: {stats['language_distribution']}")
print(f"Processing time: {stats['average_processing_time']*1000:.1f}ms")
```

### Memory Management

```python
# Clear old transcriptions, keep recent 100
processor.clear_history(keep_recent=100)

# Automatic memory management (keeps last 1000 by default)
processor._TRANSCRIPTION_CACHE_SIZE = 500  # Reduce if needed
```

## ⚡ Performance Optimizations

### Configuration Optimizations

```python
# Optimized default configuration
DEFAULT_RECORDER_CONFIG = {
    "model": "base",                          # Multilingual support
    "beam_size": 5,                          # Increased accuracy
    "realtime_processing_pause": 0.02,       # Faster updates  
    "allowed_latency_limit": 300,            # Reduced latency
    "faster_whisper_vad_filter": True,       # Better performance
    "vad_filter": True,                      # Voice activity detection
    "condition_on_previous_text": True,      # Better context
}
```

### Continuous Mode Optimizations

```python
processor = OptimizedTranscriptionProcessor(
    continuous_mode=True,  # Optimized for continuous transcription
    pipeline_latency=0.2,  # Faster response time
)

# Continuous mode automatically adjusts:
# - post_speech_silence_duration: 0.5s (shorter pauses)
# - min_length_of_recording: 0.3s
# - realtime_processing_pause: 0.015s (faster updates)
```

## 🔍 Language Detection Features

### Automatic Detection

```python
def on_language_detected(language):
    print(f"Language detected: {language}")

processor = OptimizedTranscriptionProcessor(
    language_detection_callback=on_language_detected,
    auto_language_switching=True
)
```

### Code-switching Detection

The system automatically detects:
- Mixed Hindi-English content
- Script transitions (Latin ↔ Devanagari)
- Sustained single-language segments
- Language boundaries within text

### Manual Language Control

```python
# Check current language
current = processor.current_language

# Switch language
if processor.switch_language("hi"):
    print("Switched to Hindi")

# Detect language of specific text
detected = processor.detect_language("Hello नमस्ते")
# Returns: "hi-en" (code-switching detected)
```

## 🛠️ Advanced Features

### Custom Callbacks

```python
def on_realtime(result: TranscriptionResult):
    # Real-time transcription updates
    print(f"Partial: {result.text}")

def on_final(result: TranscriptionResult):
    # Final transcription results
    print(f"Final: {result.text}")
    
def on_silence_change(is_silent: bool):
    # Silence detection
    print(f"Silence: {is_silent}")

def on_recording_start():
    # Recording started
    print("Recording...")

processor = OptimizedTranscriptionProcessor(
    realtime_transcription_callback=on_realtime,
    full_transcription_callback=on_final,
    silence_active_callback=on_silence_change,
    on_recording_start_callback=on_recording_start
)
```

### Force Finalization

```python
# Manually finalize current transcription
processor.force_finalize()
```

### Audio Processing

```python
# Get current audio buffer
audio_data = processor.get_last_audio_copy()

# Feed audio with metadata
processor.feed_audio(audio_chunk, metadata={"sample_rate": 16000})
```

## 🧪 Testing and Validation

### Test Different Scenarios

```python
# Test English
processor_en = OptimizedTranscriptionProcessor(source_language="en")

# Test Hindi  
processor_hi = OptimizedTranscriptionProcessor(source_language="hi")

# Test code-switching
processor_mixed = OptimizedTranscriptionProcessor(
    source_language="hi-en",
    auto_language_switching=True
)
```

### Performance Testing

```python
import time

start_time = time.time()
# ... transcription process ...
end_time = time.time()

stats = processor.get_statistics()
print(f"Processing time: {stats['average_processing_time']*1000:.1f}ms")
print(f"Real-time factor: {stats['total_processed_audio']/(end_time-start_time):.2f}")
```

## ⚠️ Important Notes

1. **TTS Components Removed**: All TTS-related callbacks and processing have been completely removed for pure transcription focus.

2. **Memory Usage**: The system maintains a cache of the last 1000 transcriptions by default. Adjust `_TRANSCRIPTION_CACHE_SIZE` if needed.

3. **Language Detection**: Install `langdetect` package for automatic language detection. The system works without it but with reduced functionality.

4. **Performance**: Continuous mode is optimized for real-time applications. Use conversation mode for traditional turn-based interactions.

5. **Export**: Auto-save triggers every 100 final transcriptions. Adjust `_AUTO_SAVE_INTERVAL` as needed.

## 🔧 Configuration Reference

### Core Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source_language` | str | "en" | Initial language ("en", "hi", "hi-en") |
| `continuous_mode` | bool | True | Continuous vs conversation mode |
| `auto_language_switching` | bool | True | Enable automatic language switching |
| `export_path` | Path | None | Auto-export file path |
| `pipeline_latency` | float | 0.3 | Pipeline latency in seconds |

### Callback Functions

| Callback | Parameters | Description |
|----------|------------|-------------|
| `realtime_transcription_callback` | `TranscriptionResult` | Real-time updates |
| `full_transcription_callback` | `TranscriptionResult` | Final results |
| `language_detection_callback` | `str` | Language switches |
| `confidence_callback` | `float` | Confidence updates |
| `silence_active_callback` | `bool` | Silence state changes |
| `on_recording_start_callback` | None | Recording start |

### Performance Constants

| Constant | Default | Description |
|----------|---------|-------------|
| `_CONFIDENCE_THRESHOLD` | 0.7 | Minimum reliable confidence |
| `_TRANSCRIPTION_CACHE_SIZE` | 1000 | Maximum history size |
| `_AUTO_SAVE_INTERVAL` | 100 | Auto-save frequency |
| `_SIMILARITY_THRESHOLD` | 0.85 | Text similarity threshold |

## 📈 Migration Guide

If you're upgrading from the previous version:

### Changed APIs

```python
# OLD (removed TTS callbacks)
processor = TranscriptionProcessor(
    potential_full_transcription_callback=callback,  # ❌ Removed
    potential_full_transcription_abort_callback=callback,  # ❌ Removed  
    potential_sentence_end=callback,  # ❌ Removed
    before_final_sentence=callback,  # ❌ Removed
    tts_allowed_event=event,  # ❌ Removed
)

# NEW (transcription-focused)
processor = OptimizedTranscriptionProcessor(
    realtime_transcription_callback=callback,  # ✅ Enhanced
    full_transcription_callback=callback,      # ✅ Enhanced
    language_detection_callback=callback,      # ✅ New
    confidence_callback=callback,              # ✅ New
)
```

### New Return Types

```python
# OLD: Callbacks received strings
def old_callback(text: str):
    print(text)

# NEW: Callbacks receive rich TranscriptionResult objects
def new_callback(result: TranscriptionResult):
    print(f"{result.text} (conf: {result.confidence:.2f})")
```

## 🚀 Quick Start

```python
from transcribe import OptimizedTranscriptionProcessor
from pathlib import Path

# Create processor with Hindi-English support
processor = OptimizedTranscriptionProcessor(
    source_language="hi-en",
    export_path=Path("./transcriptions/session.json"),
    continuous_mode=True,
    auto_language_switching=True
)

# Setup transcription
processor.transcribe_loop()

# Your audio processing loop
while recording:
    audio_chunk = get_audio_chunk()  # Your audio source
    processor.feed_audio(audio_chunk)

# Cleanup
processor.shutdown()
```

This optimized transcription processor provides a comprehensive solution for live Hindi/English transcription with professional-grade features and performance optimizations.