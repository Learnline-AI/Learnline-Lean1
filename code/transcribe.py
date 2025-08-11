"""
Optimized Transcription Processor for Live Hindi/English Transcription

This module provides an enhanced TranscriptionProcessor optimized for:
- Hindi/English multilingual support with code-switching
- Real-time transcription with timestamps and confidence scoring  
- Export functionality for transcription results
- Continuous transcription mode optimization
- Automatic language detection
- Removal of TTS-related components for pure transcription focus

Author: Claude (Anthropic)
Version: 2.0 - Optimized for Live Transcription
"""

import logging
logger = logging.getLogger(__name__)

from turndetect import strip_ending_punctuation
from difflib import SequenceMatcher
from colors import Colors
from text_similarity import TextSimilarity
from scipy import signal
import numpy as np
import threading
import textwrap
import torch
import json
import copy
import time
import re
import csv
import datetime
from pathlib import Path
from typing import Optional, Callable, Any, Dict, List, Literal, Union

try:
    import langdetect
except ImportError:
    langdetect = None
    logger.warning("langdetect not installed - automatic language detection will be disabled")

# --- Configuration Flags ---
USE_TURN_DETECTION = True
START_STT_SERVER = False  # Set to True to use the client/server version of RealtimeSTT

# Language support mappings for Hindi/English
LANGUAGE_MODELS = {
    "en": {
        "model": "tiny.en" if IS_RAILWAY else "base.en",
        "realtime_model": "tiny.en" if IS_RAILWAY else "base.en", 
        "name": "English",
        "whisper_code": "en"
    },
    "hi": {
        "model": "tiny" if IS_RAILWAY else "base",  # Smaller models for Railway
        "realtime_model": "tiny" if IS_RAILWAY else "base",
        "name": "Hindi", 
        "whisper_code": "hi"
    },
    "hi-en": {
        "model": "tiny" if IS_RAILWAY else "base",  # Smaller model for code-switching
        "realtime_model": "tiny" if IS_RAILWAY else "base",
        "name": "Hindi-English (Code-switching)",
        "whisper_code": None  # Let Whisper auto-detect
    }
}

# Railway-optimized configuration for live transcription
import os
IS_RAILWAY = os.getenv("RAILWAY_DEPLOYMENT", "false").lower() == "true"

DEFAULT_RECORDER_CONFIG: Dict[str, Any] = {
    "use_microphone": False,
    "spinner": False,
    "model": "tiny.en" if IS_RAILWAY else "base",  # Smaller model for Railway
    "realtime_model_type": "tiny.en" if IS_RAILWAY else "base",
    "use_main_model_for_realtime": False,
    "language": "en",  # Default, will be overridden by source_language
    "silero_sensitivity": 0.1 if IS_RAILWAY else 0.05,  # Less sensitive for Railway
    "webrtc_sensitivity": 3,
    "post_speech_silence_duration": 0.9 if IS_RAILWAY else 0.7,  # Longer for Railway stability
    "min_length_of_recording": 0.7 if IS_RAILWAY else 0.5,
    "min_gap_between_recordings": 0,
    "enable_realtime_transcription": True,
    "realtime_processing_pause": 0.05 if IS_RAILWAY else 0.02,  # Slower for Railway
    "silero_use_onnx": True,
    "silero_deactivity_detection": True,
    "early_transcription_on_silence": 0,
    "beam_size": 3 if IS_RAILWAY else 5,  # Reduced for Railway memory
    "beam_size_realtime": 2 if IS_RAILWAY else 3,
    "no_log_file": True,
    "wake_words": "",  # Disabled for continuous transcription
    "wakeword_backend": "pvporcupine",
    "allowed_latency_limit": 500 if IS_RAILWAY else 300,  # Higher for Railway
    "debug_mode": False,  # Reduced logging for production
    "initial_prompt_realtime": "Hello, how are you today? नमस्ते, आप कैसे हैं?",  # Hindi/English mixed
    "faster_whisper_vad_filter": True,
    "vad_filter": True,
    "condition_on_previous_text": True,
}

if START_STT_SERVER:
    from RealtimeSTT import AudioToTextRecorderClient
else:
    from RealtimeSTT import AudioToTextRecorder

if USE_TURN_DETECTION:
    from turndetect import TurnDetection

INT16_MAX_ABS_VALUE: float = 32768.0
SAMPLE_RATE: int = 16000


class TranscriptionResult:
    """
    Enhanced data class for transcription results with comprehensive metadata.
    """
    def __init__(
        self,
        text: str,
        confidence: float = 0.0,
        timestamp: float = None,
        language: str = "unknown",
        is_final: bool = False,
        duration: float = 0.0,
        word_count: int = 0,
        has_mixed_language: bool = False
    ):
        self.text = text
        self.confidence = confidence
        self.timestamp = timestamp or time.time()
        self.language = language
        self.is_final = is_final
        self.duration = duration
        self.word_count = word_count or len(text.split()) if text else 0
        self.has_mixed_language = has_mixed_language
        self.datetime = datetime.datetime.fromtimestamp(self.timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'datetime': self.datetime.isoformat(),
            'language': self.language,
            'is_final': self.is_final,
            'duration': self.duration,
            'word_count': self.word_count,
            'has_mixed_language': self.has_mixed_language
        }


class OptimizedTranscriptionProcessor:
    """
    Optimized transcription processor for live Hindi/English transcription.
    
    This class manages audio transcription using RealtimeSTT with focus on:
    - Hindi/English language support with code-switching detection
    - Real-time transcription with timestamps and confidence scoring
    - Export functionality for transcription results
    - Continuous transcription mode optimization
    - Automatic language detection and switching
    - Performance optimization for low-latency processing
    
    All TTS-related components have been removed for pure transcription focus.
    """
    
    # --- Constants for Optimized Processing (Railway-aware) ---
    _PIPELINE_RESERVE_TIME_MS: float = 0.025 if IS_RAILWAY else 0.015  # Railway needs more reserve
    _CONFIDENCE_THRESHOLD: float = 0.7  # Minimum confidence for reliable transcription
    _LANGUAGE_DETECTION_MIN_WORDS: int = 3  # Minimum words for language detection
    _TRANSCRIPTION_CACHE_SIZE: int = 200 if IS_RAILWAY else 1000  # Reduced cache for Railway memory
    _AUTO_SAVE_INTERVAL: int = 50 if IS_RAILWAY else 100  # More frequent saves for Railway
    _SIMILARITY_THRESHOLD: float = 0.85  # Text similarity threshold for deduplication
    
    def __init__(
        self,
        source_language: str = "en",
        realtime_transcription_callback: Optional[Callable[[TranscriptionResult], None]] = None,
        full_transcription_callback: Optional[Callable[[TranscriptionResult], None]] = None,
        language_detection_callback: Optional[Callable[[str], None]] = None,
        confidence_callback: Optional[Callable[[float], None]] = None,
        silence_active_callback: Optional[Callable[[bool], None]] = None,
        on_recording_start_callback: Optional[Callable[[], None]] = None,
        continuous_mode: bool = True,
        auto_language_switching: bool = True,
        export_path: Optional[Union[str, Path]] = None,
        local: bool = True,
        pipeline_latency: float = 0.3,  # Optimized for real-time
        recorder_config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Initialize the optimized transcription processor.

        Args:
            source_language: Language code ("en", "hi", "hi-en" for code-switching)
            realtime_transcription_callback: Callback for real-time updates (receives TranscriptionResult)
            full_transcription_callback: Callback for final results (receives TranscriptionResult)
            language_detection_callback: Callback for language detection (receives language code)
            confidence_callback: Callback for confidence updates (receives confidence float)
            silence_active_callback: Callback for silence state changes (receives boolean)
            on_recording_start_callback: Callback when recording starts
            continuous_mode: Enable continuous transcription mode vs conversation mode
            auto_language_switching: Enable automatic language switching for code-switching
            export_path: Path for auto-exporting transcription results
            local: Use local models vs remote processing
            pipeline_latency: Pipeline latency in seconds
            recorder_config: Optional custom recorder configuration
        """
        # Core configuration
        self.source_language = source_language
        self.continuous_mode = continuous_mode
        self.auto_language_switching = auto_language_switching
        self.pipeline_latency = pipeline_latency
        
        # Enhanced callbacks for transcription-only focus
        self.realtime_transcription_callback = realtime_transcription_callback
        self.full_transcription_callback = full_transcription_callback
        self.language_detection_callback = language_detection_callback
        self.confidence_callback = confidence_callback
        self.silence_active_callback = silence_active_callback
        self.on_recording_start_callback = on_recording_start_callback
        
        # Recorder and state management
        self.recorder: Optional[Union[AudioToTextRecorder, AudioToTextRecorderClient]] = None
        self.current_transcription: Optional[TranscriptionResult] = None
        self.transcription_history: List[TranscriptionResult] = []
        self.current_language: str = source_language
        self.detected_language: Optional[str] = None
        
        # Real-time processing state
        self.realtime_text: Optional[str] = None
        self.current_confidence: float = 0.0
        self.silence_time: float = 0.0
        self.silence_active: bool = False
        self.recording_start_time: Optional[float] = None
        self.last_audio_copy: Optional[np.ndarray] = None
        self._last_partial_text: str = ""
        
        # Export and persistence
        self.export_path = Path(export_path) if export_path else None
        self.auto_save_counter: int = 0
        
        # Performance tracking
        self.processing_times: List[float] = []
        self.total_processed_audio: float = 0.0
        
        # Cleanup and shutdown
        self.shutdown_performed: bool = False
        
        # Enhanced text similarity for better deduplication
        self.text_similarity = TextSimilarity(focus='end', n_words=7)
        
        # Configure recorder with language-specific optimizations
        self.recorder_config = self._prepare_recorder_config(recorder_config)
        
        # Language detection setup
        self.language_detector_enabled = langdetect is not None
        if not self.language_detector_enabled:
            logger.warning("⚠️ Language detection disabled - install langdetect package for auto-detection")
        
        # Initialize turn detection with continuous mode optimization
        if USE_TURN_DETECTION:
            logger.info(f"🔄 {Colors.YELLOW}Turn detection enabled for continuous transcription{Colors.RESET}")
            self.turn_detection = TurnDetection(
                on_new_waiting_time=self.on_new_waiting_time,
                local=local,
                pipeline_latency=pipeline_latency
            )
            # Optimize for continuous mode
            if self.continuous_mode:
                self.turn_detection.update_settings(speed_factor=0.2)  # Faster response
        
        # Initialize components
        self._create_recorder()
        self._start_silence_monitor()
        
        # Setup auto-export
        if self.export_path:
            self.export_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Auto-export enabled: {self.export_path}")
        
        logger.info(f"✅ OptimizedTranscriptionProcessor initialized for {LANGUAGE_MODELS.get(source_language, {}).get('name', 'unknown')} language")
    
    def _prepare_recorder_config(self, custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare recorder configuration with language-specific optimizations.
        """
        config = copy.deepcopy(DEFAULT_RECORDER_CONFIG)
        
        # Apply language-specific settings
        if self.source_language in LANGUAGE_MODELS:
            lang_config = LANGUAGE_MODELS[self.source_language]
            config["model"] = lang_config["model"]
            config["realtime_model_type"] = lang_config["realtime_model"]
            if lang_config["whisper_code"]:
                config["language"] = lang_config["whisper_code"]
            logger.info(f"🌐 Configured for {lang_config['name']} language")
        else:
            logger.warning(f"⚠️ Unknown language '{self.source_language}', using default config")
        
        # Optimize for continuous mode
        if self.continuous_mode:
            config["post_speech_silence_duration"] = 0.5  # Shorter pauses
            config["min_length_of_recording"] = 0.3
            config["realtime_processing_pause"] = 0.015  # Faster updates
            
        # Apply custom overrides
        if custom_config:
            config.update(custom_config)
        
        return config
    
    def _get_recorder_param(self, param_name: str, default: Any = None) -> Any:
        """Get recorder parameter with client/server abstraction."""
        if not self.recorder:
            return default
        if START_STT_SERVER:
            return self.recorder.get_parameter(param_name)
        else:
            return getattr(self.recorder, param_name, default)
    
    def _set_recorder_param(self, param_name: str, value: Any) -> None:
        """Set recorder parameter with client/server abstraction."""
        if not self.recorder:
            return
        if START_STT_SERVER:
            self.recorder.set_parameter(param_name, value)
        else:
            setattr(self.recorder, param_name, value)
    
    def _is_recorder_recording(self) -> bool:
        """Check if recorder is currently recording."""
        if not self.recorder:
            return False
        if START_STT_SERVER:
            return self.recorder.get_parameter("is_recording")
        else:
            return getattr(self.recorder, "is_recording", False)
    
    def _start_silence_monitor(self) -> None:
        """
        Optimized silence monitoring for continuous transcription mode.
        """
        def monitor():
            self.silence_time = self._get_recorder_param("speech_end_silence_start", 0.0)

            while not self.shutdown_performed:
                speech_end_silence_start = self.silence_time
                
                if self.recorder and speech_end_silence_start != 0:
                    silence_waiting_time = self._get_recorder_param("post_speech_silence_duration", 0.0)
                    time_since_silence = time.time() - speech_end_silence_start
                    
                    # Optimized timing for continuous transcription
                    finalize_threshold = silence_waiting_time - self.pipeline_latency - self._PIPELINE_RESERVE_TIME_MS
                    
                    # Trigger finalization when silence threshold is reached
                    if time_since_silence > finalize_threshold and self.realtime_text:
                        self._finalize_current_transcription()
                
                time.sleep(0.005)  # Optimized sleep interval

        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _finalize_current_transcription(self) -> None:
        """Finalize current transcription with comprehensive metadata."""
        if not self.realtime_text:
            return
        
        # Enhanced language detection for final text
        detected_lang = self.detect_language(self.realtime_text) or self.current_language
        has_mixed = self._has_mixed_scripts(self.realtime_text)
        
        # Create comprehensive result
        result = TranscriptionResult(
            text=self.realtime_text,
            confidence=self.current_confidence,
            timestamp=time.time(),
            language=detected_lang,
            is_final=True,
            duration=time.time() - (self.recording_start_time or time.time()),
            word_count=len(self.realtime_text.split()),
            has_mixed_language=has_mixed
        )
        
        # Add to history with size management
        self.transcription_history.append(result)
        if len(self.transcription_history) > self._TRANSCRIPTION_CACHE_SIZE:
            self.transcription_history = self.transcription_history[-self._TRANSCRIPTION_CACHE_SIZE:]
        
        # Trigger callback
        if self.full_transcription_callback:
            self.full_transcription_callback(result)
        
        # Auto-save check
        self._auto_save_if_needed()
        
        logger.info(f"✅ Finalized: {result.text} (conf: {result.confidence:.2f}, lang: {result.language})")
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Enhanced language detection for Hindi/English content.
        """
        if not self.language_detector_enabled or not text or len(text.split()) < self._LANGUAGE_DETECTION_MIN_WORDS:
            return None
            
        try:
            detected = langdetect.detect(text)
            # Enhanced mapping for Indian languages
            lang_mapping = {
                'hi': 'hi', 
                'en': 'en', 
                'ur': 'hi',  # Urdu often confused with Hindi
                'pa': 'hi',  # Punjabi might be detected as Hindi
                'bn': 'hi'   # Bengali might be confused
            }
            
            # Check for code-switching
            if self._has_mixed_scripts(text):
                return 'hi-en'
                
            return lang_mapping.get(detected, detected)
        except Exception as e:
            logger.debug(f"Language detection failed: {e}")
            return None
    
    def switch_language(self, new_language: str) -> bool:
        """
        Dynamic language switching with validation.
        """
        if new_language not in LANGUAGE_MODELS:
            logger.warning(f"Unsupported language: {new_language}")
            return False
            
        if new_language == self.current_language:
            return True
            
        try:
            lang_config = LANGUAGE_MODELS[new_language]
            if lang_config["whisper_code"]:
                self._set_recorder_param("language", lang_config["whisper_code"])
            
            old_language = self.current_language
            self.current_language = new_language
            
            if self.language_detection_callback:
                self.language_detection_callback(new_language)
                
            logger.info(f"🔄 Language switched: {LANGUAGE_MODELS.get(old_language, {}).get('name', old_language)} → {lang_config['name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to switch language to {new_language}: {e}")
            return False
    
    def estimate_confidence(self, text: str, audio_data: Optional[np.ndarray] = None) -> float:
        """
        Enhanced confidence estimation with multiple factors.
        """
        if not text or not text.strip():
            return 0.0
        
        confidence = 1.0
        words = text.strip().split()
        
        # Length-based confidence
        if len(words) < 2:
            confidence *= 0.7
        elif len(words) > 50:
            confidence *= 0.9
        
        # Character diversity analysis
        unique_chars = len(set(text.lower()))
        if unique_chars < 5 and len(text) > 10:
            confidence *= 0.6
        
        # Language consistency analysis
        if self._has_mixed_scripts(text):
            if self.current_language == "hi-en":
                confidence *= 0.95  # Expected for code-switching
            else:
                confidence *= 0.75  # Unexpected mixing
        
        # Repetition detection
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        max_repetition = max(word_freq.values()) if word_freq else 1
        if max_repetition > len(words) * 0.5:  # More than 50% repetition
            confidence *= 0.6
        
        # Audio-based confidence (if available)
        if audio_data is not None and len(audio_data) > 0:
            volume = np.abs(audio_data).mean()
            if volume < 0.01:  # Very quiet
                confidence *= 0.8
            elif volume > 0.5:  # Potentially clipped
                confidence *= 0.9
            
            # Signal-to-noise ratio approximation
            if len(audio_data) > 1600:  # At least 100ms at 16kHz
                snr_estimate = self._estimate_snr(audio_data)
                if snr_estimate < 10:  # Low SNR
                    confidence *= 0.85
        
        return max(0.0, min(1.0, confidence))
    
    def _estimate_snr(self, audio_data: np.ndarray) -> float:
        """Simple SNR estimation for audio quality assessment."""
        try:
            # Simple energy-based SNR estimation
            signal_power = np.mean(audio_data ** 2)
            
            # Estimate noise from quieter sections
            sorted_energy = np.sort(audio_data ** 2)
            noise_power = np.mean(sorted_energy[:len(sorted_energy)//4])  # Bottom 25%
            
            if noise_power > 0:
                snr = 10 * np.log10(signal_power / noise_power)
                return max(0, snr)
            return 30  # High SNR if no noise detected
        except:
            return 15  # Default moderate SNR
    
    def _has_mixed_scripts(self, text: str) -> bool:
        """
        Enhanced mixed script detection for Hindi/English.
        """
        has_latin = bool(re.search(r'[a-zA-Z]', text))
        has_devanagari = bool(re.search(r'[\u0900-\u097F]', text))
        
        # Additional South Asian scripts that might appear
        has_other_indic = bool(re.search(r'[\u0980-\u09FF\u0A00-\u0A7F\u0A80-\u0AFF]', text))
        
        return has_latin and (has_devanagari or has_other_indic)
    
    def _auto_save_if_needed(self) -> None:
        """Auto-save functionality with intelligent triggers."""
        if not self.export_path:
            return
            
        self.auto_save_counter += 1
        if self.auto_save_counter >= self._AUTO_SAVE_INTERVAL:
            self.export_transcriptions(self.export_path, format="json")
            self.auto_save_counter = 0
            logger.info(f"💾 Auto-saved {len(self.transcription_history)} transcriptions")
    
    def export_transcriptions(
        self, 
        path: Union[str, Path], 
        format: Literal["json", "csv", "txt"] = "json",
        filter_final_only: bool = True,
        include_metadata: bool = True
    ) -> bool:
        """
        Enhanced export functionality with multiple formats.
        """
        try:
            path = Path(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Filter and prepare data
            data = self.transcription_history
            if filter_final_only:
                data = [t for t in data if t.is_final]
            
            if format == "json":
                export_data = [t.to_dict() for t in data]
                if include_metadata:
                    export_data = {
                        "metadata": {
                            "export_timestamp": datetime.datetime.now().isoformat(),
                            "total_transcriptions": len(data),
                            "languages": list(set(t.language for t in data)),
                            "total_duration": sum(t.duration for t in data),
                            "average_confidence": sum(t.confidence for t in data) / len(data) if data else 0
                        },
                        "transcriptions": export_data
                    }
                
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            elif format == "csv":
                fieldnames = ['datetime', 'text', 'language', 'confidence', 'duration', 'word_count', 'has_mixed_language']
                with open(path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for t in data:
                        writer.writerow({
                            'datetime': t.datetime.isoformat(),
                            'text': t.text,
                            'language': t.language,
                            'confidence': t.confidence,
                            'duration': t.duration,
                            'word_count': t.word_count,
                            'has_mixed_language': t.has_mixed_language
                        })
            
            elif format == "txt":
                with open(path, 'w', encoding='utf-8') as f:
                    if include_metadata:
                        f.write(f"=== Transcription Export ===\n")
                        f.write(f"Export Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Total Transcriptions: {len(data)}\n")
                        f.write(f"Languages: {', '.join(set(t.language for t in data))}\n")
                        f.write(f"\n=== Transcriptions ===\n\n")
                    
                    for t in data:
                        timestamp_str = t.datetime.strftime('%H:%M:%S')
                        conf_str = f"({t.confidence:.2f})" if t.confidence > 0 else ""
                        lang_str = f"[{t.language}]" if t.language != "unknown" else ""
                        f.write(f"[{timestamp_str}] {lang_str} {t.text} {conf_str}\n")
            
            logger.info(f"📤 Exported {len(data)} transcriptions to {path} ({format.upper()})")
            return True
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def clear_history(self, keep_recent: int = 0) -> None:
        """
        Clear transcription history with option to keep recent items.
        """
        if keep_recent > 0:
            cleared_count = len(self.transcription_history) - keep_recent
            self.transcription_history = self.transcription_history[-keep_recent:]
        else:
            cleared_count = len(self.transcription_history)
            self.transcription_history.clear()
        
        self.auto_save_counter = 0
        logger.info(f"🗑️ Cleared {cleared_count} transcriptions from history")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Comprehensive statistics and performance metrics.
        """
        total_transcriptions = len(self.transcription_history)
        final_transcriptions = len([t for t in self.transcription_history if t.is_final])
        
        if total_transcriptions == 0:
            return {
                'total_transcriptions': 0,
                'final_transcriptions': 0,
                'average_confidence': 0.0,
                'language_distribution': {},
                'total_duration': 0.0,
                'average_processing_time': 0.0,
                'performance_metrics': {}
            }
        
        # Calculate enhanced statistics
        confidences = [t.confidence for t in self.transcription_history if t.confidence > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Language distribution
        languages = [t.language for t in self.transcription_history]
        lang_dist = {lang: languages.count(lang) for lang in set(languages)}
        
        # Duration and performance metrics
        total_duration = sum(t.duration for t in self.transcription_history)
        avg_processing_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
        
        # Mixed language statistics
        mixed_lang_count = len([t for t in self.transcription_history if t.has_mixed_language])
        
        return {
            'total_transcriptions': total_transcriptions,
            'final_transcriptions': final_transcriptions,
            'average_confidence': avg_confidence,
            'language_distribution': lang_dist,
            'mixed_language_transcriptions': mixed_lang_count,
            'total_duration': total_duration,
            'total_processed_audio': self.total_processed_audio,
            'average_processing_time': avg_processing_time,
            'current_language': self.current_language,
            'auto_language_switching': self.auto_language_switching,
            'continuous_mode': self.continuous_mode,
            'performance_metrics': {
                'avg_words_per_transcription': sum(t.word_count for t in self.transcription_history) / total_transcriptions if total_transcriptions else 0,
                'transcriptions_per_minute': (final_transcriptions / (total_duration / 60)) if total_duration > 0 else 0,
            }
        }
    
    def on_new_waiting_time(self, waiting_time: float, text: Optional[str] = None) -> None:
        """Callback for turn detection waiting time updates."""
        if self.recorder:
            current_duration = self._get_recorder_param("post_speech_silence_duration")
            if current_duration != waiting_time:
                self._set_recorder_param("post_speech_silence_duration", waiting_time)
                logger.debug(f"⏳ New waiting time: {waiting_time:.2f}s for text: {text or '(none)'}")
    
    def set_silence(self, silence_active: bool) -> None:
        """Update silence state with callback trigger."""
        if self.silence_active != silence_active:
            self.silence_active = silence_active
            if self.silence_active_callback:
                self.silence_active_callback(silence_active)
            logger.debug(f"🤫 Silence: {'ACTIVE' if silence_active else 'INACTIVE'}")
    
    def get_last_audio_copy(self) -> Optional[np.ndarray]:
        """Get last audio buffer with fallback handling."""
        audio_copy = self.get_audio_copy()
        if audio_copy is not None and len(audio_copy) > 0:
            return audio_copy
        else:
            return self.last_audio_copy
    
    def get_audio_copy(self) -> Optional[np.ndarray]:
        """
        Enhanced audio buffer retrieval with error handling.
        """
        if not self.recorder or not hasattr(self.recorder, 'frames'):
            return self.last_audio_copy
        
        try:
            # Thread-safe frame access
            with getattr(self.recorder, 'frames_lock', threading.Lock()):
                frames_data = list(self.recorder.frames)
            
            if not frames_data:
                return self.last_audio_copy
            
            # Process audio buffer
            full_audio_array = np.frombuffer(b''.join(frames_data), dtype=np.int16)
            if full_audio_array.size == 0:
                return self.last_audio_copy
            
            # Convert to float32 and normalize
            audio_copy = full_audio_array.astype(np.float32) / INT16_MAX_ABS_VALUE
            
            # Update cache and tracking
            if len(audio_copy) > 0:
                self.last_audio_copy = audio_copy
                self.total_processed_audio += len(audio_copy) / SAMPLE_RATE  # Convert to seconds
            
            return audio_copy
            
        except Exception as e:
            logger.error(f"Error getting audio copy: {e}")
            return self.last_audio_copy
    
    def _create_recorder(self) -> None:
        """
        Enhanced recorder creation with comprehensive callback setup.
        """
        def start_silence_detection():
            """Enhanced silence start detection."""
            self.set_silence(True)
            recorder_silence_start = self._get_recorder_param("speech_end_silence_start", None)
            self.silence_time = recorder_silence_start if recorder_silence_start else time.time()
        
        def stop_silence_detection():
            """Enhanced silence end detection."""
            self.set_silence(False)
            self.silence_time = 0.0
        
        def start_recording():
            """Enhanced recording start with timing and state setup."""
            self.recording_start_time = time.time()
            self.set_silence(False)
            self.silence_time = 0.0
            self._last_partial_text = ""
            
            if self.on_recording_start_callback:
                self.on_recording_start_callback()
            
            logger.info(f"▶️ Recording started (mode: {'continuous' if self.continuous_mode else 'conversation'})")
        
        def stop_recording() -> bool:
            """Enhanced recording stop with final confidence calculation."""
            if self.realtime_text:
                audio_copy = self.get_last_audio_copy()
                self.current_confidence = self.estimate_confidence(self.realtime_text, audio_copy)
                logger.debug(f"⏹️ Recording stopped - final confidence: {self.current_confidence:.2f}")
            return False
        
        def on_partial(text: Optional[str]):
            """
            Enhanced real-time transcription callback with full feature set.
            """
            if not text:
                return
            
            processing_start = time.time()
            self.realtime_text = text
            
            # Enhanced confidence estimation
            self.current_confidence = self.estimate_confidence(text, self.get_last_audio_copy())
            
            # Intelligent language detection and switching
            if self.auto_language_switching:
                detected_lang = self.detect_language(text)
                if detected_lang and detected_lang != self.current_language:
                    # Smart code-switching detection
                    if self._has_mixed_scripts(text) and self.current_language != "hi-en":
                        self.switch_language("hi-en")
                    elif detected_lang in ["hi", "en"] and not self._has_mixed_scripts(text):
                        if self.current_language == "hi-en":
                            # Only switch from code-switching if we have sustained single-language content
                            recent_detections = [self.detect_language(t.text) for t in self.transcription_history[-3:] if t.text]
                            if recent_detections.count(detected_lang) >= 2:
                                self.switch_language(detected_lang)
                        else:
                            self.switch_language(detected_lang)
            
            # Create enhanced partial result
            result = TranscriptionResult(
                text=text,
                confidence=self.current_confidence,
                timestamp=time.time(),
                language=self.current_language,
                is_final=False,
                duration=time.time() - (self.recording_start_time or time.time()),
                word_count=len(text.split()),
                has_mixed_language=self._has_mixed_scripts(text)
            )
            
            # Intelligent deduplication
            stripped_text = strip_ending_punctuation(text)
            if self.text_similarity.is_similar(self._last_partial_text, stripped_text, self._SIMILARITY_THRESHOLD):
                return
            
            self._last_partial_text = stripped_text
            
            # Trigger callbacks
            if self.realtime_transcription_callback:
                self.realtime_transcription_callback(result)
            
            if self.confidence_callback:
                self.confidence_callback(self.current_confidence)
            
            # Turn detection for continuous mode
            if USE_TURN_DETECTION and hasattr(self, 'turn_detection'):
                self.turn_detection.calculate_waiting_time(text=text)
            
            # Performance tracking
            processing_time = time.time() - processing_start
            self.processing_times.append(processing_time)
            if len(self.processing_times) > 100:  # Keep last 100 measurements
                self.processing_times = self.processing_times[-100:]
            
            logger.debug(f"📝 Partial: {text[:50]}{'...' if len(text) > 50 else ''} "
                        f"(conf: {self.current_confidence:.2f}, lang: {self.current_language}, "
                        f"proc: {processing_time*1000:.1f}ms)")
        
        def on_final(text: Optional[str]):
            """
            Enhanced final transcription callback with comprehensive processing.
            """
            if not text or not text.strip():
                logger.warning("⚠️ Final transcription empty")
                return
            
            processing_start = time.time()
            
            # Enhanced final processing
            audio_copy = self.get_last_audio_copy()
            confidence = self.estimate_confidence(text, audio_copy)
            final_language = self.detect_language(text) or self.current_language
            
            # Create comprehensive result
            result = TranscriptionResult(
                text=text,
                confidence=confidence,
                timestamp=time.time(),
                language=final_language,
                is_final=True,
                duration=time.time() - (self.recording_start_time or time.time()),
                word_count=len(text.split()),
                has_mixed_language=self._has_mixed_scripts(text)
            )
            
            # Add to history with intelligent management
            self.transcription_history.append(result)
            if len(self.transcription_history) > self._TRANSCRIPTION_CACHE_SIZE:
                self.transcription_history = self.transcription_history[-self._TRANSCRIPTION_CACHE_SIZE:]
            
            # Reset turn detection
            if USE_TURN_DETECTION and hasattr(self, 'turn_detection'):
                self.turn_detection.reset()
            
            # Trigger callbacks
            if self.full_transcription_callback:
                self.full_transcription_callback(result)
            
            # Auto-save management
            self._auto_save_if_needed()
            
            # Performance tracking
            processing_time = time.time() - processing_start
            self.processing_times.append(processing_time)
            
            logger.info(f"✅ Final: {text} (conf: {confidence:.2f}, lang: {final_language}, "
                       f"words: {result.word_count}, proc: {processing_time*1000:.1f}ms)")
        
        # Prepare enhanced recorder configuration
        active_config = self.recorder_config.copy()
        active_config.update({
            "on_realtime_transcription_update": on_partial,
            "on_turn_detection_start": start_silence_detection,
            "on_turn_detection_stop": stop_silence_detection,
            "on_recording_start": start_recording,
            "on_recording_stop": stop_recording,
        })
        
        # Configuration logging with sensitive data protection
        def safe_config_repr(config):
            safe_config = {}
            for k, v in config.items():
                if callable(v):
                    safe_config[k] = f"[callback: {v.__name__}]"
                elif isinstance(v, str) and len(v) > 60:
                    safe_config[k] = v[:60] + " [...]"
                else:
                    safe_config[k] = v
            return safe_config
        
        logger.info(f"⚙️ Creating recorder with optimized configuration")
        logger.debug(f"Configuration: {json.dumps(safe_config_repr(active_config), indent=2)}")
        
        # Create recorder instance
        try:
            if START_STT_SERVER:
                self.recorder = AudioToTextRecorderClient(**active_config)
            else:
                self.recorder = AudioToTextRecorder(**active_config)
            
            # Disable wake words for continuous transcription
            self._set_recorder_param("use_wake_words", False)
            
            logger.info(f"✅ Recorder created successfully for {LANGUAGE_MODELS.get(self.source_language, {}).get('name', 'unknown')} language")
            
        except Exception as e:
            logger.exception(f"❌ Failed to create recorder: {e}")
            self.recorder = None
    
    def transcribe_loop(self) -> None:
        """
        Set up the transcription loop with enhanced final callback.
        """
        def enhanced_on_final(text: Optional[str]):
            """Final transcription handler with all enhancements."""
            if not text or not text.strip():
                return
            
            # This will be handled by the on_final callback in _create_recorder
            # This method exists for API compatibility
            pass
        
        if self.recorder:
            if hasattr(self.recorder, 'text'):
                self.recorder.text(enhanced_on_final)
            else:
                logger.warning("⚠️ Recorder does not support text() method")
        else:
            logger.error("❌ Cannot set up transcription loop: Recorder not initialized")
    
    def force_finalize(self, audio_bytes: Optional[bytes] = None) -> None:
        """
        Force finalization of current transcription with enhanced processing.
        """
        if not self.recorder or not self.realtime_text:
            logger.warning("⚠️ Cannot force finalize: No recorder or no current text")
            return
        
        # Enhanced finalization
        audio_data = self.get_last_audio_copy()
        confidence = self.estimate_confidence(self.realtime_text, audio_data)
        detected_lang = self.detect_language(self.realtime_text) or self.current_language
        
        result = TranscriptionResult(
            text=self.realtime_text,
            confidence=confidence,
            timestamp=time.time(),
            language=detected_lang,
            is_final=True,
            duration=time.time() - (self.recording_start_time or time.time()),
            word_count=len(self.realtime_text.split()),
            has_mixed_language=self._has_mixed_scripts(self.realtime_text)
        )
        
        # Process result
        self.transcription_history.append(result)
        
        if USE_TURN_DETECTION and hasattr(self, 'turn_detection'):
            self.turn_detection.reset()
        
        if self.full_transcription_callback:
            self.full_transcription_callback(result)
        
        self._auto_save_if_needed()
        logger.info(f"⚡ Force finalized: {result.text} (confidence: {confidence:.2f})")
    
    def feed_audio(self, chunk: bytes, audio_meta_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Enhanced audio feeding with performance tracking.
        """
        if self.recorder and not self.shutdown_performed:
            try:
                self.recorder.feed_audio(chunk)
                logger.debug(f"🔊 Fed audio chunk: {len(chunk)} bytes")
            except Exception as e:
                logger.error(f"💥 Error feeding audio: {e}")
        elif not self.recorder:
            logger.warning("⚠️ Cannot feed audio: Recorder not initialized")
        elif self.shutdown_performed:
            logger.debug("🚫 Cannot feed audio: Shutdown performed")
    
    def shutdown(self) -> None:
        """
        Enhanced shutdown with comprehensive cleanup and final reporting.
        """
        if self.shutdown_performed:
            logger.info("ℹ️ Shutdown already performed")
            return
        
        logger.info("🔌 Shutting down OptimizedTranscriptionProcessor...")
        self.shutdown_performed = True
        
        # Final statistics
        stats = self.get_statistics()
        logger.info(f"📊 Final Statistics:")
        logger.info(f"   • Total transcriptions: {stats['total_transcriptions']}")
        logger.info(f"   • Final transcriptions: {stats['final_transcriptions']}")
        logger.info(f"   • Average confidence: {stats['average_confidence']:.2f}")
        logger.info(f"   • Total audio processed: {stats['total_processed_audio']:.1f}s")
        logger.info(f"   • Language distribution: {stats['language_distribution']}")
        
        # Final export if enabled
        if self.export_path and self.transcription_history:
            try:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                final_export_path = self.export_path.parent / f"{self.export_path.stem}_final_{timestamp}{self.export_path.suffix}"
                self.export_transcriptions(final_export_path, format="json", include_metadata=True)
                logger.info(f"💾 Final export saved: {final_export_path}")
            except Exception as e:
                logger.error(f"❌ Final export failed: {e}")
        
        # Shutdown recorder
        if self.recorder:
            try:
                self.recorder.shutdown()
                logger.info("✅ Recorder shutdown completed")
            except Exception as e:
                logger.error(f"❌ Recorder shutdown error: {e}")
            finally:
                self.recorder = None
        
        # Shutdown turn detection
        if USE_TURN_DETECTION and hasattr(self, 'turn_detection'):
            try:
                if hasattr(self.turn_detection, 'shutdown'):
                    self.turn_detection.shutdown()
                logger.debug("✅ Turn detection shutdown completed")
            except Exception as e:
                logger.error(f"❌ Turn detection shutdown error: {e}")
        
        logger.info("🔌 OptimizedTranscriptionProcessor shutdown completed")
    
    def _normalize_text(self, text: str) -> str:
        """
        Enhanced text normalization supporting Hindi and English.
        """
        if not text:
            return ""
        
        # Convert to lowercase and strip
        text = text.lower().strip()
        
        # Keep alphanumeric, spaces, and Devanagari/other Indic characters
        text = re.sub(r'[^a-z0-9\s\u0900-\u097F\u0980-\u09FF\u0A00-\u0A7F]', '', text)
        
        # Collapse extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def is_basically_the_same(self, text1: str, text2: str, similarity_threshold: float = None) -> bool:
        """
        Enhanced text similarity comparison.
        """
        threshold = similarity_threshold or self._SIMILARITY_THRESHOLD
        return self.text_similarity.is_similar(text1, text2, threshold)


# Maintain backward compatibility
TranscriptionProcessor = OptimizedTranscriptionProcessor

# Export the main class
__all__ = ['OptimizedTranscriptionProcessor', 'TranscriptionProcessor', 'TranscriptionResult', 'LANGUAGE_MODELS']