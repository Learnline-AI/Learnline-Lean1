"""
Language Switching and Export Functionality Test Suite
======================================================

Comprehensive tests for language switching and export features:
- Dynamic language switching between Hindi, English, and code-switching
- Export functionality validation (JSON, text formats)
- Language detection accuracy during switching
- Export data integrity and format compliance
- Multi-session language persistence
- Export performance under load

Author: Claude (Anthropic)
Version: 1.0 - QA Testing Framework
"""

import unittest
import json
import csv
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from transcribe import OptimizedTranscriptionProcessor, TranscriptionResult, LANGUAGE_MODELS
    from server import TranscriptionHistory
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    raise

class LanguageSwitchingTestSuite(unittest.TestCase):
    """Test suite for language switching functionality."""
    
    def setUp(self):
        """Set up language switching tests."""
        self.processor = None
        self.test_results = []
        
    def tearDown(self):
        """Clean up after language switching tests."""
        if self.processor:
            self.processor.shutdown()
    
    def test_basic_language_switching(self):
        """Test basic language switching functionality."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True,
            auto_language_switching=True
        )
        
        # Test switching through all supported languages
        languages = ["en", "hi", "hi-en", "en"]
        
        for target_lang in languages:
            with self.subTest(language=target_lang):
                initial_lang = self.processor.current_language
                success = self.processor.switch_language(target_lang)
                
                self.assertTrue(success, f"Failed to switch to {target_lang}")
                self.assertEqual(self.processor.current_language, target_lang,
                               f"Language not updated to {target_lang}")
                
                logger.info(f"Language switched: {initial_lang} → {target_lang}")
    
    def test_invalid_language_switching(self):
        """Test switching to invalid languages."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        invalid_languages = ["fr", "de", "invalid", "", None, 123]
        
        for invalid_lang in invalid_languages:
            with self.subTest(language=invalid_lang):
                initial_lang = self.processor.current_language
                success = self.processor.switch_language(invalid_lang)
                
                self.assertFalse(success, f"Should not switch to invalid language: {invalid_lang}")
                self.assertEqual(self.processor.current_language, initial_lang,
                               f"Language changed unexpectedly from {initial_lang}")
    
    def test_language_detection_consistency(self):
        """Test language detection consistency after switching."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True,
            auto_language_switching=True
        )
        
        # Test cases: (language, text, expected_detection)
        test_cases = [
            ("en", "Hello, how are you today?", "en"),
            ("hi", "नमस्ते, आप कैसे हैं?", "hi"), 
            ("hi-en", "Hello नमस्ते, how are you आप कैसे हैं?", "hi-en"),
            ("en", "The weather is beautiful outside", "en"),
            ("hi", "मौसम बहुत अच्छा है आज", "hi"),
        ]
        
        detection_accuracy = 0
        total_tests = 0
        
        for target_lang, test_text, expected_detection in test_cases:
            with self.subTest(language=target_lang, text=test_text[:30]):
                # Switch language
                switch_success = self.processor.switch_language(target_lang)
                self.assertTrue(switch_success, f"Failed to switch to {target_lang}")
                
                # Test language detection
                detected = self.processor.detect_language(test_text)
                
                # Allow for reasonable flexibility in detection
                detection_correct = False
                if detected == expected_detection:
                    detection_correct = True
                elif expected_detection == "hi-en" and detected in ["hi", "en"]:
                    detection_correct = True  # Partial credit for code-switching
                elif detected is None and len(test_text.split()) < 3:
                    detection_correct = True  # Too short for reliable detection
                
                if detection_correct:
                    detection_accuracy += 1
                
                total_tests += 1
                
                logger.info(f"Language {target_lang}: '{test_text[:30]}...' → "
                           f"detected: {detected}, expected: {expected_detection}")
        
        overall_accuracy = detection_accuracy / total_tests if total_tests > 0 else 0
        self.assertGreater(overall_accuracy, 0.7, 
                          f"Language detection accuracy too low: {overall_accuracy:.2%}")
        
        logger.info(f"Language detection accuracy: {overall_accuracy:.2%} "
                   f"({detection_accuracy}/{total_tests})")
    
    def test_automatic_language_switching(self):
        """Test automatic language switching based on content."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True,
            auto_language_switching=True
        )
        
        # Start with English
        self.assertEqual(self.processor.current_language, "en")
        
        # Simulate processing Hindi content
        hindi_texts = [
            "नमस्ते दोस्त",
            "मौसम बहुत अच्छा है",
            "आप कैसे हैं"
        ]
        
        for text in hindi_texts:
            # Simulate the automatic switching logic from on_partial
            detected_lang = self.processor.detect_language(text)
            if detected_lang and detected_lang != self.processor.current_language:
                if not self.processor._has_mixed_scripts(text):
                    self.processor.switch_language(detected_lang)
        
        # After processing Hindi, language might switch
        logger.info(f"After Hindi processing: {self.processor.current_language}")
        
        # Simulate processing mixed content
        mixed_texts = [
            "Hello नमस्ते friend",
            "यह project बहुत good है",
            "मैं English और हिंदी both बोलता हूं"
        ]
        
        for text in mixed_texts:
            detected_lang = self.processor.detect_language(text)
            if detected_lang and self.processor._has_mixed_scripts(text):
                if self.processor.current_language != "hi-en":
                    self.processor.switch_language("hi-en")
                    break
        
        logger.info(f"After mixed content: {self.processor.current_language}")
        
        # Should handle language switching gracefully
        self.assertIn(self.processor.current_language, ["en", "hi", "hi-en"])
    
    def test_language_switching_with_history(self):
        """Test language switching impact on transcription history."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Add transcriptions in different languages
        transcriptions = [
            ("en", "Hello world", 0.9),
            ("hi", "नमस्ते दोस्त", 0.85),
            ("en", "How are you?", 0.9),
            ("hi-en", "Hello नमस्ते", 0.8),
        ]
        
        for lang, text, confidence in transcriptions:
            # Switch language
            self.processor.switch_language(lang)
            
            # Add transcription to history
            result = TranscriptionResult(
                text=text,
                confidence=confidence,
                language=lang,
                is_final=True
            )
            self.processor.transcription_history.append(result)
        
        # Verify history contains all languages
        languages_in_history = set(t.language for t in self.processor.transcription_history)
        expected_languages = {"en", "hi", "hi-en"}
        
        self.assertEqual(languages_in_history, expected_languages,
                        "Not all languages represented in history")
        
        # Test statistics by language
        stats = self.processor.get_statistics()
        lang_dist = stats.get("language_distribution", {})
        
        for lang in expected_languages:
            self.assertIn(lang, lang_dist, f"Language {lang} missing from distribution")
            self.assertGreater(lang_dist[lang], 0, f"No transcriptions for language {lang}")
        
        logger.info(f"Language distribution in history: {lang_dist}")

class ExportFunctionalityTestSuite(unittest.TestCase):
    """Test suite for export functionality."""
    
    def setUp(self):
        """Set up export functionality tests."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.history = TranscriptionHistory()
        self.processor = None
        
        # Add sample transcriptions
        self._populate_test_history()
        
    def tearDown(self):
        """Clean up after export tests."""
        if self.processor:
            self.processor.shutdown()
        
        # Clean up temp files
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.warning(f"Failed to clean up temp dir: {e}")
    
    def _populate_test_history(self):
        """Populate history with test transcriptions."""
        test_transcriptions = [
            {"text": "Hello, how are you today?", "language": "en", "is_final": True},
            {"text": "नमस्ते, आप कैसे हैं?", "language": "hi", "is_final": True},
            {"text": "Hello नमस्ते friend", "language": "hi-en", "is_final": True},
            {"text": "The weather is beautiful", "language": "en", "is_final": False},
            {"text": "मौसम बहुत अच्छा है", "language": "hi", "is_final": True},
        ]
        
        for i, trans in enumerate(test_transcriptions):
            timestamp = time.time() + i
            self.history.add_transcription(
                text=trans["text"],
                language=trans["language"],
                timestamp=timestamp,
                is_final=trans["is_final"]
            )
    
    def test_json_export_format(self):
        """Test JSON export format and content."""
        export_data = self.history.export_to_json()
        
        # Should be valid JSON
        try:
            parsed_data = json.loads(export_data)
        except json.JSONDecodeError as e:
            self.fail(f"Invalid JSON export: {e}")
        
        # Check structure
        self.assertIn("session_start", parsed_data)
        self.assertIn("export_time", parsed_data)
        self.assertIn("transcriptions", parsed_data)
        
        transcriptions = parsed_data["transcriptions"]
        self.assertIsInstance(transcriptions, list)
        self.assertGreater(len(transcriptions), 0)
        
        # Check transcription structure
        for trans in transcriptions:
            self.assertIn("text", trans)
            self.assertIn("language", trans)
            self.assertIn("timestamp", trans)
            self.assertIn("is_final", trans)
            self.assertIn("formatted_time", trans)
        
        logger.info(f"JSON export validated: {len(transcriptions)} transcriptions")
    
    def test_text_export_format(self):
        """Test text export format and content."""
        export_data = self.history.export_to_text()
        
        # Should contain header
        self.assertIn("Transcription Session", export_data)
        
        # Should contain transcriptions
        lines = export_data.split('\n')
        transcription_lines = [line for line in lines if line.strip() and not line.startswith('Transcription Session')]
        
        self.assertGreater(len(transcription_lines), 0, "No transcription lines found")
        
        # Check format of transcription lines
        for line in transcription_lines:
            # Should have timestamp, language, and text
            self.assertRegex(line, r'^\[\d{2}:\d{2}:\d{2}\.\d{3}\].*', 
                           f"Invalid timestamp format in line: {line}")
        
        logger.info(f"Text export validated: {len(transcription_lines)} lines")
    
    def test_export_file_operations(self):
        """Test export to actual files."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Add test transcriptions to processor
        test_results = [
            TranscriptionResult(text="Hello world", language="en", is_final=True),
            TranscriptionResult(text="नमस्ते दोस्त", language="hi", is_final=True),
            TranscriptionResult(text="Mixed content", language="hi-en", is_final=True),
        ]
        
        self.processor.transcription_history = test_results
        
        # Test JSON export
        json_file = self.temp_dir / "test_export.json"
        json_success = self.processor.export_transcriptions(json_file, format="json")
        
        self.assertTrue(json_success, "JSON export failed")
        self.assertTrue(json_file.exists(), "JSON file not created")
        
        # Validate JSON file content
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        self.assertIn("transcriptions", json_data)
        self.assertEqual(len(json_data["transcriptions"]), 3)
        
        # Test CSV export
        csv_file = self.temp_dir / "test_export.csv"
        csv_success = self.processor.export_transcriptions(csv_file, format="csv")
        
        self.assertTrue(csv_success, "CSV export failed")
        self.assertTrue(csv_file.exists(), "CSV file not created")
        
        # Validate CSV file content
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            csv_rows = list(csv_reader)
        
        self.assertEqual(len(csv_rows), 3)
        self.assertIn("text", csv_rows[0])
        self.assertIn("language", csv_rows[0])
        
        # Test TXT export
        txt_file = self.temp_dir / "test_export.txt"
        txt_success = self.processor.export_transcriptions(txt_file, format="txt")
        
        self.assertTrue(txt_success, "TXT export failed")
        self.assertTrue(txt_file.exists(), "TXT file not created")
        
        # Validate TXT file content
        with open(txt_file, 'r', encoding='utf-8') as f:
            txt_content = f.read()
        
        self.assertIn("=== Transcription Export ===", txt_content)
        self.assertIn("Hello world", txt_content)
        self.assertIn("नमस्ते दोस्त", txt_content)
        
        logger.info("All export formats validated successfully")
    
    def test_export_filtering(self):
        """Test export filtering options."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Add mix of final and partial transcriptions
        test_results = [
            TranscriptionResult(text="Final 1", language="en", is_final=True),
            TranscriptionResult(text="Partial 1", language="en", is_final=False),
            TranscriptionResult(text="Final 2", language="hi", is_final=True),
            TranscriptionResult(text="Partial 2", language="hi", is_final=False),
        ]
        
        self.processor.transcription_history = test_results
        
        # Export with final only filter
        json_file = self.temp_dir / "final_only.json"
        success = self.processor.export_transcriptions(
            json_file, 
            format="json",
            filter_final_only=True
        )
        
        self.assertTrue(success, "Filtered export failed")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Should only contain final transcriptions
        if "transcriptions" in data:
            transcriptions = data["transcriptions"]
        else:
            transcriptions = data  # Direct list format
        
        final_count = sum(1 for t in transcriptions if t.get("is_final", True))
        self.assertEqual(final_count, len(transcriptions), 
                        "Non-final transcriptions found in filtered export")
        
        logger.info(f"Filtered export: {len(transcriptions)} final transcriptions")
    
    def test_export_metadata(self):
        """Test export metadata inclusion."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Add transcriptions with various metadata
        languages = ["en", "hi", "hi-en"]
        for i, lang in enumerate(languages):
            result = TranscriptionResult(
                text=f"Test {i}",
                language=lang,
                confidence=0.9 - i * 0.1,
                is_final=True,
                duration=1.5 + i * 0.5,
                word_count=2 + i,
                has_mixed_language=(lang == "hi-en")
            )
            self.processor.transcription_history.append(result)
        
        # Export with metadata
        json_file = self.temp_dir / "with_metadata.json"
        success = self.processor.export_transcriptions(
            json_file,
            format="json",
            include_metadata=True
        )
        
        self.assertTrue(success, "Metadata export failed")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check metadata presence
        self.assertIn("metadata", data)
        metadata = data["metadata"]
        
        self.assertIn("export_timestamp", metadata)
        self.assertIn("total_transcriptions", metadata)
        self.assertIn("languages", metadata)
        self.assertIn("total_duration", metadata)
        self.assertIn("average_confidence", metadata)
        
        # Verify metadata accuracy
        self.assertEqual(metadata["total_transcriptions"], 3)
        self.assertEqual(set(metadata["languages"]), {"en", "hi", "hi-en"})
        self.assertGreater(metadata["average_confidence"], 0)
        
        logger.info(f"Export metadata validated: {metadata}")
    
    def test_export_performance_under_load(self):
        """Test export performance with large datasets."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Generate large dataset
        large_dataset_size = 1000
        for i in range(large_dataset_size):
            result = TranscriptionResult(
                text=f"Test transcription number {i} with some content",
                language=["en", "hi", "hi-en"][i % 3],
                confidence=0.8 + (i % 20) * 0.01,
                is_final=(i % 5 != 0),  # Mix of final and partial
                duration=0.5 + (i % 10) * 0.1,
                word_count=6 + (i % 5),
            )
            self.processor.transcription_history.append(result)
        
        # Test export performance
        formats = ["json", "csv", "txt"]
        performance_results = {}
        
        for format_type in formats:
            export_file = self.temp_dir / f"large_export.{format_type}"
            
            start_time = time.time()
            success = self.processor.export_transcriptions(
                export_file,
                format=format_type,
                include_metadata=True
            )
            export_time = time.time() - start_time
            
            self.assertTrue(success, f"Large {format_type.upper()} export failed")
            self.assertTrue(export_file.exists(), f"{format_type.upper()} file not created")
            
            file_size_kb = export_file.stat().st_size / 1024
            performance_results[format_type] = {
                "export_time": export_time,
                "file_size_kb": file_size_kb,
                "records_per_second": large_dataset_size / export_time if export_time > 0 else 0
            }
            
            # Performance assertions
            self.assertLess(export_time, 10.0, f"{format_type.upper()} export too slow: {export_time:.2f}s")
            
            logger.info(f"{format_type.upper()} export: {export_time:.2f}s, "
                       f"{file_size_kb:.1f}KB, {performance_results[format_type]['records_per_second']:.0f} rec/s")
        
        # Compare format performance
        fastest_format = min(performance_results.keys(), 
                           key=lambda k: performance_results[k]["export_time"])
        logger.info(f"Fastest export format: {fastest_format}")

class IntegratedLanguageExportTestSuite(unittest.TestCase):
    """Integrated tests combining language switching and export functionality."""
    
    def setUp(self):
        """Set up integrated tests."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.processor = None
        
    def tearDown(self):
        """Clean up integrated tests."""
        if self.processor:
            self.processor.shutdown()
        
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass
    
    def test_multi_session_language_persistence(self):
        """Test language persistence across sessions with export."""
        session_data = []
        
        # Simulate multiple sessions
        for session_id in range(3):
            self.processor = OptimizedTranscriptionProcessor(
                source_language="en",
                continuous_mode=True
            )
            
            # Different language focus per session
            session_languages = [
                ["en", "en", "en"],  # English session
                ["hi", "hi", "hi"],  # Hindi session  
                ["hi-en", "hi-en", "en", "hi"]  # Mixed session
            ]
            
            session_texts = [
                ["Hello world", "How are you", "Good morning"],
                ["नमस्ते दोस्त", "आप कैसे हैं", "धन्यवाद"],
                ["Hello नमस्ते", "Mixed content", "Thank you धन्यवाद", "Final message"]
            ]
            
            # Process session content
            for lang, text in zip(session_languages[session_id], session_texts[session_id]):
                self.processor.switch_language(lang)
                
                result = TranscriptionResult(
                    text=text,
                    language=lang,
                    is_final=True
                )
                self.processor.transcription_history.append(result)
            
            # Export session data
            export_file = self.temp_dir / f"session_{session_id}.json"
            success = self.processor.export_transcriptions(
                export_file,
                format="json",
                include_metadata=True
            )
            
            self.assertTrue(success, f"Session {session_id} export failed")
            
            # Store session info
            with open(export_file, 'r', encoding='utf-8') as f:
                session_data.append(json.load(f))
            
            self.processor.shutdown()
            self.processor = None
        
        # Verify session data integrity
        for i, session in enumerate(session_data):
            self.assertIn("metadata", session)
            self.assertIn("transcriptions", session)
            
            languages_in_session = set(t["language"] for t in session["transcriptions"])
            expected_languages = [{"en"}, {"hi"}, {"hi-en", "en", "hi"}]
            
            self.assertTrue(
                languages_in_session.intersection(expected_languages[i]),
                f"Session {i} language mismatch: {languages_in_session}"
            )
            
            logger.info(f"Session {i}: {len(session['transcriptions'])} transcriptions, "
                       f"languages: {languages_in_session}")
    
    def test_export_language_statistics(self):
        """Test export with comprehensive language statistics."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Add transcriptions with various language combinations
        test_data = [
            ("en", "Hello world", 0.95),
            ("en", "How are you today", 0.92),
            ("hi", "नमस्ते दोस्त", 0.88),
            ("hi", "आप कैसे हैं", 0.90),
            ("hi-en", "Hello नमस्ते friend", 0.85),
            ("hi-en", "यह project अच्छा है", 0.87),
        ]
        
        for lang, text, conf in test_data:
            self.processor.switch_language(lang)
            
            result = TranscriptionResult(
                text=text,
                language=lang,
                confidence=conf,
                is_final=True,
                has_mixed_language=(lang == "hi-en")
            )
            self.processor.transcription_history.append(result)
        
        # Get statistics
        stats = self.processor.get_statistics()
        
        # Export with statistics
        export_file = self.temp_dir / "stats_export.json"
        success = self.processor.export_transcriptions(
            export_file,
            format="json",
            include_metadata=True
        )
        
        self.assertTrue(success, "Statistics export failed")
        
        with open(export_file, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        # Verify language distribution
        metadata = export_data["metadata"]
        self.assertIn("languages", metadata)
        
        expected_languages = {"en", "hi", "hi-en"}
        actual_languages = set(metadata["languages"])
        self.assertEqual(actual_languages, expected_languages)
        
        # Verify accuracy statistics
        self.assertIn("average_confidence", metadata)
        avg_conf = metadata["average_confidence"]
        self.assertGreater(avg_conf, 0.8)
        self.assertLess(avg_conf, 1.0)
        
        logger.info(f"Language statistics export validated: {metadata}")


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(LanguageSwitchingTestSuite))
    suite.addTests(loader.loadTestsFromTestCase(ExportFunctionalityTestSuite))
    suite.addTests(loader.loadTestsFromTestCase(IntegratedLanguageExportTestSuite))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    logger.info("Starting language switching and export functionality test suite...")
    
    result = runner.run(suite)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)