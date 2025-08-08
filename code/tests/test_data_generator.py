"""
Test Data Generator for Live Transcription Testing
=================================================

Generates synthetic test data for transcription accuracy testing including:
- Sample Hindi and English phrases
- Code-switching scenarios
- Edge cases and challenging transcription scenarios
- Synthetic audio generation for testing
- Real-world transcription scenarios

Author: Claude (Anthropic)
Version: 1.0 - QA Testing Framework
"""

import json
import numpy as np
import wave
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import time
import random

logger = logging.getLogger(__name__)

class TranscriptionTestDataGenerator:
    """Generates comprehensive test data for transcription accuracy testing."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize test data generator."""
        self.output_dir = output_dir or Path(__file__).parent / "test_data"
        self.output_dir.mkdir(exist_ok=True)
        
        # Audio generation parameters
        self.sample_rate = 16000
        self.duration = 3.0  # Default duration for test audio
        
        logger.info(f"Test data generator initialized. Output dir: {self.output_dir}")
    
    def get_english_test_phrases(self) -> List[Dict]:
        """Get comprehensive English test phrases with metadata."""
        return [
            {
                "text": "Hello, how are you today?",
                "category": "greeting",
                "difficulty": "easy",
                "expected_confidence": 0.9,
                "word_count": 5,
                "description": "Basic greeting"
            },
            {
                "text": "The weather is beautiful outside today.",
                "category": "conversation",
                "difficulty": "easy",
                "expected_confidence": 0.9,
                "word_count": 6,
                "description": "Simple conversational statement"
            },
            {
                "text": "I would like to schedule a meeting for tomorrow afternoon.",
                "category": "business",
                "difficulty": "medium",
                "expected_confidence": 0.85,
                "word_count": 10,
                "description": "Business scheduling request"
            },
            {
                "text": "Please send me the quarterly financial report by five o'clock.",
                "category": "business",
                "difficulty": "medium",
                "expected_confidence": 0.8,
                "word_count": 10,
                "description": "Business communication with technical terms"
            },
            {
                "text": "The implementation of artificial intelligence in healthcare systems requires careful consideration of ethical implications.",
                "category": "technical",
                "difficulty": "hard",
                "expected_confidence": 0.75,
                "word_count": 15,
                "description": "Complex technical sentence"
            },
            {
                "text": "Could you please repeat that one more time? I didn't catch it.",
                "category": "clarification",
                "difficulty": "medium",
                "expected_confidence": 0.85,
                "word_count": 11,
                "description": "Request for repetition"
            },
            {
                "text": "The quick brown fox jumps over the lazy dog.",
                "category": "standard",
                "difficulty": "easy",
                "expected_confidence": 0.9,
                "word_count": 9,
                "description": "Pangram for alphabet coverage"
            },
            {
                "text": "In today's interconnected world, cybersecurity has become increasingly important.",
                "category": "technical",
                "difficulty": "hard",
                "expected_confidence": 0.8,
                "word_count": 10,
                "description": "Technical topic discussion"
            },
            {
                "text": "Um, actually, I think we should, you know, reconsider this approach.",
                "category": "hesitation",
                "difficulty": "hard",
                "expected_confidence": 0.7,
                "word_count": 11,
                "description": "Speech with hesitations and fillers"
            },
            {
                "text": "Can you hear me clearly? Is the audio quality good?",
                "category": "audio_check",
                "difficulty": "easy",
                "expected_confidence": 0.9,
                "word_count": 10,
                "description": "Audio quality check"
            }
        ]
    
    def get_hindi_test_phrases(self) -> List[Dict]:
        """Get comprehensive Hindi test phrases with metadata."""
        return [
            {
                "text": "नमस्ते, आप कैसे हैं?",
                "transliteration": "Namaste, aap kaise hain?",
                "translation": "Hello, how are you?",
                "category": "greeting",
                "difficulty": "easy",
                "expected_confidence": 0.9,
                "word_count": 4,
                "description": "Basic Hindi greeting"
            },
            {
                "text": "आज मौसम बहुत अच्छा है।",
                "transliteration": "Aaj mausam bahut accha hai.",
                "translation": "The weather is very good today.",
                "category": "conversation",
                "difficulty": "easy",
                "expected_confidence": 0.9,
                "word_count": 5,
                "description": "Simple weather comment"
            },
            {
                "text": "मुझे कल के लिए एक मीटिंग शेड्यूल करनी है।",
                "transliteration": "Mujhe kal ke liye ek meeting schedule karni hai.",
                "translation": "I need to schedule a meeting for tomorrow.",
                "category": "business",
                "difficulty": "medium",
                "expected_confidence": 0.8,
                "word_count": 9,
                "description": "Business scheduling in Hindi"
            },
            {
                "text": "कृपया मुझे रिपोर्ट पांच बजे तक भेजें।",
                "transliteration": "Kripaya mujhe report paanch baje tak bhejen.",
                "translation": "Please send me the report by five o'clock.",
                "category": "business",
                "difficulty": "medium",
                "expected_confidence": 0.8,
                "word_count": 8,
                "description": "Business request with time reference"
            },
            {
                "text": "तकनीक इस दशक में तेजी से आगे बढ़ रही है।",
                "transliteration": "Takneek is dashak mein tezi se aage badh rahi hai.",
                "translation": "Technology is advancing rapidly in this decade.",
                "category": "technical",
                "difficulty": "hard",
                "expected_confidence": 0.75,
                "word_count": 10,
                "description": "Technical discussion in Hindi"
            },
            {
                "text": "क्या आप कृपया इसे एक बार फिर से दोहरा सकते हैं?",
                "transliteration": "Kya aap kripaya ise ek baar phir se dohra sakte hain?",
                "translation": "Could you please repeat that once more?",
                "category": "clarification",
                "difficulty": "medium",
                "expected_confidence": 0.8,
                "word_count": 11,
                "description": "Polite repetition request"
            },
            {
                "text": "मुझे हिंदी भाषा सीखना बहुत पसंद है।",
                "transliteration": "Mujhe Hindi bhasha seekhna bahut pasand hai.",
                "translation": "I really like learning the Hindi language.",
                "category": "personal",
                "difficulty": "medium",
                "expected_confidence": 0.85,
                "word_count": 7,
                "description": "Personal preference about language"
            },
            {
                "text": "आपके समय और विचार के लिए धन्यवाद।",
                "transliteration": "Aapke samay aur vichar ke liye dhanyawad.",
                "translation": "Thank you for your time and consideration.",
                "category": "courtesy",
                "difficulty": "medium",
                "expected_confidence": 0.85,
                "word_count": 7,
                "description": "Formal thank you"
            },
            {
                "text": "स्वास्थ्य सेवा में कृत्रिम बुद्धिमत्ता का उपयोग नैतिक विचारों की आवश्यकता है।",
                "transliteration": "Swasthya seva mein kritrim buddhimatta ka upyog naitik vicharon ki aavashyakta hai.",
                "translation": "The use of artificial intelligence in healthcare requires ethical considerations.",
                "category": "technical",
                "difficulty": "hard",
                "expected_confidence": 0.7,
                "word_count": 12,
                "description": "Complex technical sentence in Hindi"
            },
            {
                "text": "क्या आप मुझे साफ सुनाई दे रहे हैं?",
                "transliteration": "Kya aap mujhe saaf sunaayi de rahe hain?",
                "translation": "Can you hear me clearly?",
                "category": "audio_check",
                "difficulty": "easy",
                "expected_confidence": 0.9,
                "word_count": 7,
                "description": "Audio clarity check"
            }
        ]
    
    def get_code_switching_test_phrases(self) -> List[Dict]:
        """Get Hindi-English code-switching test phrases with metadata."""
        return [
            {
                "text": "Hello नमस्ते, how are you आप कैसे हैं?",
                "category": "greeting",
                "difficulty": "medium",
                "expected_confidence": 0.8,
                "word_count": 8,
                "description": "Mixed greeting",
                "mixing_pattern": "word_level",
                "languages": ["en", "hi"]
            },
            {
                "text": "मुझे meeting schedule करनी है tomorrow के लिए।",
                "category": "business",
                "difficulty": "medium",
                "expected_confidence": 0.75,
                "word_count": 8,
                "description": "Business scheduling with English terms",
                "mixing_pattern": "noun_insertion",
                "languages": ["hi", "en"]
            },
            {
                "text": "यह report बहुत important है for the project।",
                "category": "business",
                "difficulty": "medium",
                "expected_confidence": 0.75,
                "word_count": 8,
                "description": "Project discussion with mixed languages",
                "mixing_pattern": "adjective_phrase",
                "languages": ["hi", "en"]
            },
            {
                "text": "Can you please बता सकते हैं कि time क्या है?",
                "category": "question",
                "difficulty": "hard",
                "expected_confidence": 0.7,
                "word_count": 9,
                "description": "Time inquiry with mixed languages",
                "mixing_pattern": "clause_mixing",
                "languages": ["en", "hi"]
            },
            {
                "text": "Technology का use करके हम better results पा सकते हैं।",
                "category": "technical",
                "difficulty": "hard",
                "expected_confidence": 0.7,
                "word_count": 10,
                "description": "Technical discussion with code-switching",
                "mixing_pattern": "technical_terms",
                "languages": ["en", "hi"]
            },
            {
                "text": "मैं English और हिंदी both languages में comfortable हूं।",
                "category": "personal",
                "difficulty": "medium",
                "expected_confidence": 0.8,
                "word_count": 9,
                "description": "Language preference statement",
                "mixing_pattern": "balanced_mixing",
                "languages": ["hi", "en"]
            },
            {
                "text": "Please send करें the documents जल्दी से।",
                "category": "business",
                "difficulty": "hard",
                "expected_confidence": 0.7,
                "word_count": 7,
                "description": "Business request with mixed imperative",
                "mixing_pattern": "imperative_mixing",
                "languages": ["en", "hi"]
            },
            {
                "text": "यह application user-friendly है और easy to use।",
                "category": "technical",
                "difficulty": "medium",
                "expected_confidence": 0.75,
                "word_count": 8,
                "description": "Software review with technical terms",
                "mixing_pattern": "technical_description",
                "languages": ["hi", "en"]
            },
            {
                "text": "Weekend में हम shopping जाएंगे और movie भी देखेंगे।",
                "category": "personal",
                "difficulty": "medium",
                "expected_confidence": 0.8,
                "word_count": 9,
                "description": "Weekend plans with activity terms",
                "mixing_pattern": "activity_terms",
                "languages": ["en", "hi"]
            },
            {
                "text": "Office में laptop working नहीं है, technical support चाहिए।",
                "category": "technical_support",
                "difficulty": "hard",
                "expected_confidence": 0.7,
                "word_count": 10,
                "description": "Technical support request",
                "mixing_pattern": "problem_description",
                "languages": ["en", "hi"]
            }
        ]
    
    def get_edge_case_test_phrases(self) -> List[Dict]:
        """Get edge case test phrases for challenging scenarios."""
        return [
            {
                "text": "",
                "category": "empty",
                "difficulty": "edge_case",
                "expected_confidence": 0.0,
                "word_count": 0,
                "description": "Empty input"
            },
            {
                "text": "a",
                "category": "minimal",
                "difficulty": "edge_case",
                "expected_confidence": 0.2,
                "word_count": 1,
                "description": "Single character"
            },
            {
                "text": "the the the the the",
                "category": "repetitive",
                "difficulty": "edge_case",
                "expected_confidence": 0.5,
                "word_count": 5,
                "description": "Highly repetitive text"
            },
            {
                "text": "123 456 789",
                "category": "numeric",
                "difficulty": "edge_case",
                "expected_confidence": 0.6,
                "word_count": 3,
                "description": "Numbers only"
            },
            {
                "text": "Hello@#$%^&*()world!",
                "category": "special_chars",
                "difficulty": "edge_case",
                "expected_confidence": 0.7,
                "word_count": 1,
                "description": "Text with special characters"
            },
            {
                "text": "word " * 100,
                "category": "very_long",
                "difficulty": "edge_case",
                "expected_confidence": 0.8,
                "word_count": 100,
                "description": "Very long repetitive text"
            },
            {
                "text": "Um, uh, like, you know, I think, maybe, sort of, kind of, actually.",
                "category": "fillers",
                "difficulty": "edge_case",
                "expected_confidence": 0.6,
                "word_count": 11,
                "description": "Text full of hesitations and fillers"
            },
            {
                "text": "COVID-19 API REST JSON HTTP HTTPS SSL TLS AI ML IoT 5G",
                "category": "acronyms",
                "difficulty": "edge_case",
                "expected_confidence": 0.7,
                "word_count": 11,
                "description": "Technical acronyms"
            },
            {
                "text": "one two three चार पांच six seven आठ नौ ten",
                "category": "mixed_numbers",
                "difficulty": "edge_case",
                "expected_confidence": 0.7,
                "word_count": 10,
                "description": "Mixed language numbers"
            },
            {
                "text": "WhatsApp iPhone MacBook प्रधानमंत्री McDonald's",
                "category": "proper_nouns",
                "difficulty": "edge_case",
                "expected_confidence": 0.8,
                "word_count": 5,
                "description": "Mixed proper nouns"
            }
        ]
    
    def generate_synthetic_audio(self, frequency: float = 440.0, duration: float = None) -> np.ndarray:
        """Generate synthetic audio for testing purposes."""
        duration = duration or self.duration
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples, False)
        
        # Generate composite signal with multiple components
        fundamental = np.sin(2 * np.pi * frequency * t) * 0.4
        harmonic2 = np.sin(2 * np.pi * frequency * 2 * t) * 0.2
        harmonic3 = np.sin(2 * np.pi * frequency * 3 * t) * 0.1
        
        # Add some noise for realism
        noise = np.random.normal(0, 0.05, samples)
        
        # Combine signal components
        signal = fundamental + harmonic2 + harmonic3 + noise
        
        # Apply envelope to avoid clicks
        envelope_samples = int(0.01 * self.sample_rate)  # 10ms fade
        envelope = np.ones_like(signal)
        envelope[:envelope_samples] = np.linspace(0, 1, envelope_samples)
        envelope[-envelope_samples:] = np.linspace(1, 0, envelope_samples)
        
        signal *= envelope
        
        # Normalize to prevent clipping
        signal = signal / np.max(np.abs(signal)) * 0.8
        
        return signal.astype(np.float32)
    
    def save_audio_as_wav(self, audio_data: np.ndarray, filename: str) -> Path:
        """Save audio data as WAV file."""
        filepath = self.output_dir / filename
        
        # Convert to int16 for WAV format
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(str(filepath), 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        logger.info(f"Audio saved: {filepath}")
        return filepath
    
    def generate_test_suite(self) -> Dict:
        """Generate complete test suite with all categories."""
        logger.info("Generating comprehensive test suite...")
        
        test_suite = {
            "metadata": {
                "generated_at": time.time(),
                "generator_version": "1.0.0",
                "total_test_cases": 0,
                "categories": []
            },
            "english_phrases": self.get_english_test_phrases(),
            "hindi_phrases": self.get_hindi_test_phrases(),
            "code_switching_phrases": self.get_code_switching_test_phrases(),
            "edge_cases": self.get_edge_case_test_phrases()
        }
        
        # Calculate metadata
        total_cases = (len(test_suite["english_phrases"]) + 
                      len(test_suite["hindi_phrases"]) + 
                      len(test_suite["code_switching_phrases"]) + 
                      len(test_suite["edge_cases"]))
        
        test_suite["metadata"]["total_test_cases"] = total_cases
        test_suite["metadata"]["categories"] = ["english", "hindi", "code_switching", "edge_cases"]
        
        # Save test suite
        output_file = self.output_dir / "comprehensive_test_suite.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_suite, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Test suite generated: {output_file}")
        logger.info(f"Total test cases: {total_cases}")
        
        return test_suite
    
    def generate_audio_test_files(self) -> List[Path]:
        """Generate synthetic audio files for different test scenarios."""
        logger.info("Generating synthetic audio test files...")
        
        audio_files = []
        
        # Different audio characteristics for testing
        test_scenarios = [
            {"name": "clear_speech", "frequency": 440, "duration": 2.0, "description": "Clear speech simulation"},
            {"name": "low_volume", "frequency": 220, "duration": 2.0, "description": "Low volume speech"},
            {"name": "high_pitch", "frequency": 880, "duration": 2.0, "description": "High pitch speech"},
            {"name": "noisy_environment", "frequency": 440, "duration": 3.0, "description": "Speech with background noise"},
            {"name": "short_utterance", "frequency": 440, "duration": 0.5, "description": "Very short speech"},
            {"name": "long_speech", "frequency": 440, "duration": 10.0, "description": "Extended speech"},
        ]
        
        for scenario in test_scenarios:
            audio_data = self.generate_synthetic_audio(
                frequency=scenario["frequency"],
                duration=scenario["duration"]
            )
            
            # Add specific modifications for each scenario
            if scenario["name"] == "low_volume":
                audio_data *= 0.3
            elif scenario["name"] == "noisy_environment":
                noise = np.random.normal(0, 0.15, len(audio_data))
                audio_data += noise
                audio_data = np.clip(audio_data, -1, 1)
            
            filename = f"{scenario['name']}_test.wav"
            filepath = self.save_audio_as_wav(audio_data, filename)
            audio_files.append(filepath)
            
            logger.info(f"Generated audio: {scenario['name']} - {scenario['description']}")
        
        return audio_files
    
    def create_benchmark_dataset(self) -> Dict:
        """Create a benchmark dataset for accuracy measurement."""
        logger.info("Creating benchmark dataset...")
        
        benchmark = {
            "name": "Hindi-English Transcription Benchmark v1.0",
            "description": "Comprehensive benchmark for Hindi-English transcription accuracy",
            "created_at": time.time(),
            "test_cases": []
        }
        
        # Add high-quality reference transcriptions
        english_refs = [
            {
                "id": "EN001",
                "text": "Good morning, how can I help you today?",
                "language": "en",
                "difficulty": "easy",
                "reference_accuracy": 1.0,
                "category": "customer_service"
            },
            {
                "id": "EN002", 
                "text": "The quarterly financial report shows significant improvement.",
                "language": "en",
                "difficulty": "medium",
                "reference_accuracy": 1.0,
                "category": "business"
            },
            {
                "id": "EN003",
                "text": "Implementation of machine learning algorithms requires substantial computational resources.",
                "language": "en",
                "difficulty": "hard",
                "reference_accuracy": 1.0,
                "category": "technical"
            }
        ]
        
        hindi_refs = [
            {
                "id": "HI001",
                "text": "सुप्रभात, मैं आपकी कैसे सहायता कर सकता हूं?",
                "language": "hi",
                "difficulty": "easy",
                "reference_accuracy": 1.0,
                "category": "customer_service"
            },
            {
                "id": "HI002",
                "text": "तिमाही वित्तीय रिपोर्ट में महत्वपूर्ण सुधार दिखाई दे रहा है।",
                "language": "hi", 
                "difficulty": "medium",
                "reference_accuracy": 1.0,
                "category": "business"
            },
            {
                "id": "HI003",
                "text": "मशीन लर्निंग एल्गोरिदम के कार्यान्वयन के लिए पर्याप्त कम्प्यूटेशनल संसाधन चाहिए।",
                "language": "hi",
                "difficulty": "hard", 
                "reference_accuracy": 1.0,
                "category": "technical"
            }
        ]
        
        code_switching_refs = [
            {
                "id": "CS001",
                "text": "Good morning सुप्रभात, कैसे हैं आप?",
                "language": "hi-en",
                "difficulty": "medium",
                "reference_accuracy": 1.0,
                "category": "greeting"
            },
            {
                "id": "CS002",
                "text": "यह project deadline के लिए बहुत important है।",
                "language": "hi-en",
                "difficulty": "medium",
                "reference_accuracy": 1.0,
                "category": "business"
            },
            {
                "id": "CS003",
                "text": "Machine learning का implementation इस company में revolutionary होगा।",
                "language": "hi-en",
                "difficulty": "hard",
                "reference_accuracy": 1.0,
                "category": "technical"
            }
        ]
        
        # Combine all references
        benchmark["test_cases"] = english_refs + hindi_refs + code_switching_refs
        
        # Save benchmark dataset
        benchmark_file = self.output_dir / "transcription_benchmark_v1.json"
        with open(benchmark_file, 'w', encoding='utf-8') as f:
            json.dump(benchmark, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Benchmark dataset created: {benchmark_file}")
        logger.info(f"Total benchmark cases: {len(benchmark['test_cases'])}")
        
        return benchmark


if __name__ == "__main__":
    # Initialize generator and create test data
    generator = TranscriptionTestDataGenerator()
    
    # Generate complete test suite
    test_suite = generator.generate_test_suite()
    
    # Generate synthetic audio files
    audio_files = generator.generate_audio_test_files()
    
    # Create benchmark dataset
    benchmark = generator.create_benchmark_dataset()
    
    print(f"Test data generation completed!")
    print(f"Output directory: {generator.output_dir}")
    print(f"Test cases generated: {test_suite['metadata']['total_test_cases']}")
    print(f"Audio files generated: {len(audio_files)}")
    print(f"Benchmark cases: {len(benchmark['test_cases'])}")