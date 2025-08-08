"""
Example Usage of Optimized Transcription Processor

This script demonstrates how to use the optimized transcription processor
for live Hindi/English transcription with all the new features.
"""

import logging
from pathlib import Path
from transcribe import OptimizedTranscriptionProcessor, TranscriptionResult

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def on_realtime_transcription(result: TranscriptionResult):
    """Callback for real-time transcription updates."""
    print(f"🔄 Real-time: {result.text} (confidence: {result.confidence:.2f}, lang: {result.language})")

def on_final_transcription(result: TranscriptionResult):
    """Callback for final transcription results."""
    print(f"✅ Final: {result.text}")
    print(f"   📊 Confidence: {result.confidence:.2f}")
    print(f"   🌐 Language: {result.language}")
    print(f"   ⏱️ Duration: {result.duration:.2f}s")
    print(f"   📝 Words: {result.word_count}")
    print(f"   🔀 Mixed Language: {result.has_mixed_language}")
    print("---")

def on_language_detection(language: str):
    """Callback for language detection events."""
    print(f"🔍 Language detected/switched: {language}")

def on_confidence_update(confidence: float):
    """Callback for confidence score updates."""
    if confidence < 0.5:
        print(f"⚠️ Low confidence: {confidence:.2f}")

def on_silence_change(is_silent: bool):
    """Callback for silence state changes."""
    print(f"🤫 Silence: {'ON' if is_silent else 'OFF'}")

def on_recording_start():
    """Callback when recording starts."""
    print("▶️ Recording started!")

def main():
    """
    Main example demonstrating the optimized transcription processor.
    """
    print("🎙️ Optimized Transcription Processor Demo")
    print("=========================================")
    
    # Example 1: Basic English transcription
    print("\n📝 Example 1: English Transcription")
    processor_en = OptimizedTranscriptionProcessor(
        source_language="en",
        realtime_transcription_callback=on_realtime_transcription,
        full_transcription_callback=on_final_transcription,
        continuous_mode=True
    )
    
    # Example 2: Hindi transcription with auto-export
    print("\n📝 Example 2: Hindi Transcription with Export")
    export_path = Path("./transcriptions/hindi_session.json")
    
    processor_hi = OptimizedTranscriptionProcessor(
        source_language="hi",
        realtime_transcription_callback=on_realtime_transcription,
        full_transcription_callback=on_final_transcription,
        language_detection_callback=on_language_detection,
        confidence_callback=on_confidence_update,
        export_path=export_path,
        continuous_mode=True
    )
    
    # Example 3: Code-switching (Hindi-English) with all callbacks
    print("\n📝 Example 3: Hindi-English Code-Switching")
    processor_mixed = OptimizedTranscriptionProcessor(
        source_language="hi-en",
        realtime_transcription_callback=on_realtime_transcription,
        full_transcription_callback=on_final_transcription,
        language_detection_callback=on_language_detection,
        confidence_callback=on_confidence_update,
        silence_active_callback=on_silence_change,
        on_recording_start_callback=on_recording_start,
        continuous_mode=True,
        auto_language_switching=True,
        export_path=Path("./transcriptions/mixed_session.json")
    )
    
    # Example usage of advanced features
    print("\n🔧 Advanced Features Demo")
    
    # Get current statistics
    stats = processor_mixed.get_statistics()
    print(f"📊 Current Statistics: {stats}")
    
    # Manual language switching
    if processor_mixed.switch_language("en"):
        print("✅ Successfully switched to English")
    
    # Export transcriptions in different formats
    processor_mixed.export_transcriptions(
        Path("./transcriptions/export_example.json"),
        format="json",
        include_metadata=True
    )
    
    processor_mixed.export_transcriptions(
        Path("./transcriptions/export_example.csv"),
        format="csv"
    )
    
    processor_mixed.export_transcriptions(
        Path("./transcriptions/export_example.txt"),
        format="txt",
        include_metadata=True
    )
    
    # Clear old transcriptions but keep recent ones
    processor_mixed.clear_history(keep_recent=50)
    
    print("\n🎯 Key Features Demonstrated:")
    print("✅ Multi-language support (English, Hindi, Hindi-English)")
    print("✅ Real-time transcription with confidence scoring")
    print("✅ Automatic language detection and switching") 
    print("✅ Comprehensive transcription metadata")
    print("✅ Auto-export functionality (JSON, CSV, TXT)")
    print("✅ Performance tracking and statistics")
    print("✅ Continuous transcription mode optimization")
    print("✅ Enhanced error handling and logging")
    
    print("\n📋 Usage Tips:")
    print("• Use 'en' for English-only transcription")
    print("• Use 'hi' for Hindi-only transcription")
    print("• Use 'hi-en' for code-switching scenarios")
    print("• Enable auto_language_switching for dynamic language detection")
    print("• Set export_path for automatic transcription saving")
    print("• Use continuous_mode=True for real-time applications")
    print("• Monitor confidence scores to assess transcription quality")
    
    print("\n⚠️ Installation Requirements:")
    print("• pip install RealtimeSTT")
    print("• pip install langdetect  # For automatic language detection")
    print("• pip install torch transformers  # For turn detection")
    print("• pip install scipy numpy  # For audio processing")
    
    # Cleanup
    print("\n🧹 Cleaning up...")
    processor_en.shutdown()
    processor_hi.shutdown() 
    processor_mixed.shutdown()
    
    print("✅ Demo completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")