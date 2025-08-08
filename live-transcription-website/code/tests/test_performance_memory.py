"""
Performance and Memory Validation Test Suite
============================================

Comprehensive tests for performance benchmarking and memory usage validation:
- Memory usage monitoring and leak detection
- Processing time benchmarks
- Resource utilization under load
- Connection scalability testing
- Memory optimization validation
- Performance regression detection

Author: Claude (Anthropic)
Version: 1.0 - QA Testing Framework
"""

import unittest
import asyncio
import time
import threading
import gc
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import numpy as np

logger = logging.getLogger(__name__)

# Import memory monitoring
try:
    import psutil
    MEMORY_MONITORING_AVAILABLE = True
except ImportError:
    MEMORY_MONITORING_AVAILABLE = False
    logger.warning("psutil not available - memory monitoring will be limited")

# Import transcription components
try:
    from transcribe import OptimizedTranscriptionProcessor, TranscriptionResult
    from server import app
    from quality_assurance import PerformanceBenchmark
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    raise

@dataclass
class MemorySnapshot:
    """Memory usage snapshot."""
    timestamp: float
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    percent: float  # Memory percentage
    available_mb: float
    context: str

@dataclass
class PerformanceSnapshot:
    """Performance metrics snapshot."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    processing_time_ms: float
    active_threads: int
    context: str

class SystemResourceMonitor:
    """Monitor system resources during testing."""
    
    def __init__(self):
        """Initialize resource monitor."""
        self.memory_snapshots: List[MemorySnapshot] = []
        self.performance_snapshots: List[PerformanceSnapshot] = []
        self.monitoring = False
        self.monitor_thread = None
        self.monitor_interval = 0.1  # 100ms intervals
        
    def start_monitoring(self):
        """Start resource monitoring."""
        if not MEMORY_MONITORING_AVAILABLE:
            logger.warning("Memory monitoring not available")
            return
            
        self.monitoring = True
        self.memory_snapshots.clear()
        self.performance_snapshots.clear()
        
        def monitor_loop():
            process = psutil.Process()
            while self.monitoring:
                try:
                    # Memory info
                    memory_info = process.memory_info()
                    memory_percent = process.memory_percent()
                    system_memory = psutil.virtual_memory()
                    
                    # CPU info
                    cpu_percent = process.cpu_percent()
                    
                    # Thread count
                    thread_count = process.num_threads()
                    
                    # Record snapshots
                    memory_snapshot = MemorySnapshot(
                        timestamp=time.time(),
                        rss_mb=memory_info.rss / 1024 / 1024,
                        vms_mb=memory_info.vms / 1024 / 1024,
                        percent=memory_percent,
                        available_mb=system_memory.available / 1024 / 1024,
                        context="monitoring"
                    )
                    
                    performance_snapshot = PerformanceSnapshot(
                        timestamp=time.time(),
                        cpu_percent=cpu_percent,
                        memory_mb=memory_info.rss / 1024 / 1024,
                        processing_time_ms=0,  # Will be set by specific operations
                        active_threads=thread_count,
                        context="monitoring"
                    )
                    
                    self.memory_snapshots.append(memory_snapshot)
                    self.performance_snapshots.append(performance_snapshot)
                    
                except Exception as e:
                    logger.error(f"Error in resource monitoring: {e}")
                
                time.sleep(self.monitor_interval)
        
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info(f"Resource monitoring stopped. Collected {len(self.memory_snapshots)} snapshots")
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory usage statistics."""
        if not self.memory_snapshots:
            return {}
        
        rss_values = [s.rss_mb for s in self.memory_snapshots]
        vms_values = [s.vms_mb for s in self.memory_snapshots]
        
        return {
            "rss_min_mb": min(rss_values),
            "rss_max_mb": max(rss_values),
            "rss_avg_mb": sum(rss_values) / len(rss_values),
            "rss_final_mb": rss_values[-1],
            "vms_min_mb": min(vms_values),
            "vms_max_mb": max(vms_values),
            "vms_avg_mb": sum(vms_values) / len(vms_values),
            "memory_growth_mb": rss_values[-1] - rss_values[0] if len(rss_values) > 1 else 0,
            "peak_memory_mb": max(rss_values)
        }
    
    def detect_memory_leaks(self, threshold_mb: float = 10.0) -> Tuple[bool, str]:
        """Detect potential memory leaks."""
        if len(self.memory_snapshots) < 10:
            return False, "Insufficient data for leak detection"
        
        # Check for consistent growth pattern
        rss_values = [s.rss_mb for s in self.memory_snapshots]
        growth = rss_values[-1] - rss_values[0]
        
        # Check for monotonic growth over time
        growth_points = 0
        for i in range(1, len(rss_values)):
            if rss_values[i] > rss_values[i-1]:
                growth_points += 1
        
        growth_ratio = growth_points / (len(rss_values) - 1)
        
        if growth > threshold_mb and growth_ratio > 0.7:
            return True, f"Memory leak detected: {growth:.1f}MB growth, {growth_ratio:.2%} growth points"
        
        return False, f"No significant leak detected: {growth:.1f}MB growth"

class TranscriptionPerformanceTestSuite(unittest.TestCase):
    """Performance tests for transcription processing."""
    
    def setUp(self):
        """Set up performance tests."""
        self.monitor = SystemResourceMonitor()
        self.test_results = []
        self.processor = None
    
    def tearDown(self):
        """Clean up after performance tests."""
        if self.processor:
            self.processor.shutdown()
        self.monitor.stop_monitoring()
    
    def test_memory_usage_baseline(self):
        """Test baseline memory usage without processing."""
        if not MEMORY_MONITORING_AVAILABLE:
            self.skipTest("Memory monitoring not available")
        
        self.monitor.start_monitoring()
        
        # Create processor
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Let it stabilize
        time.sleep(2)
        
        # Get baseline stats
        baseline_stats = self.monitor.get_memory_stats()
        
        # Should not use excessive memory
        self.assertLess(baseline_stats.get("rss_avg_mb", 0), 200, 
                       "Baseline memory usage too high")
        
        logger.info(f"Baseline memory usage: {baseline_stats.get('rss_avg_mb', 0):.1f}MB")
        
        self.test_results.append({
            "test": "baseline_memory",
            "memory_mb": baseline_stats.get("rss_avg_mb", 0),
            "passed": baseline_stats.get("rss_avg_mb", 0) < 200
        })
    
    def test_memory_usage_under_load(self):
        """Test memory usage under processing load."""
        if not MEMORY_MONITORING_AVAILABLE:
            self.skipTest("Memory monitoring not available")
        
        self.monitor.start_monitoring()
        
        # Create processor
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Simulate continuous processing
        test_phrases = [
            "Hello, how are you today?",
            "The weather is beautiful outside.",
            "I would like to schedule a meeting.",
            "Please send me the report by five o'clock.",
            "Technology is advancing rapidly."
        ] * 20  # Repeat for more load
        
        start_time = time.time()
        
        for phrase in test_phrases:
            # Simulate transcription processing
            confidence = self.processor.estimate_confidence(phrase)
            detected_lang = self.processor.detect_language(phrase)
            normalized = self.processor._normalize_text(phrase)
            
            # Small delay to simulate real processing
            time.sleep(0.01)
        
        processing_time = time.time() - start_time
        
        # Let memory stabilize
        time.sleep(1)
        
        # Get load stats
        load_stats = self.monitor.get_memory_stats()
        
        # Check for memory leaks
        has_leak, leak_info = self.monitor.detect_memory_leaks(threshold_mb=20)
        
        logger.info(f"Load test completed in {processing_time:.2f}s")
        logger.info(f"Peak memory usage: {load_stats.get('peak_memory_mb', 0):.1f}MB")
        logger.info(f"Memory growth: {load_stats.get('memory_growth_mb', 0):.1f}MB")
        logger.info(f"Leak detection: {leak_info}")
        
        # Assertions
        self.assertLess(load_stats.get("peak_memory_mb", 0), 300, "Peak memory usage too high")
        self.assertFalse(has_leak, f"Memory leak detected: {leak_info}")
        
        self.test_results.append({
            "test": "load_memory",
            "peak_memory_mb": load_stats.get("peak_memory_mb", 0),
            "memory_growth_mb": load_stats.get("memory_growth_mb", 0),
            "has_leak": has_leak,
            "processing_time": processing_time,
            "phrases_processed": len(test_phrases)
        })
    
    def test_processing_time_performance(self):
        """Test processing time performance benchmarks."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Test different complexity levels
        test_cases = [
            ("short", "Hello world"),
            ("medium", "The weather is beautiful outside today and everyone is happy"),
            ("long", "This is a very long sentence that contains many words and should test the processing speed of the transcription system when handling larger amounts of text content that might be typical in real-world scenarios"),
            ("hindi", "नमस्ते दोस्त, आप कैसे हैं आज? मौसम बहुत अच्छा है।"),
            ("mixed", "Hello नमस्ते, how are you आप कैसे हैं today?")
        ]
        
        results = {}
        
        for category, text in test_cases:
            times = []
            
            # Run multiple iterations for statistical significance
            for i in range(100):
                start_time = time.time()
                
                # Perform typical processing operations
                confidence = self.processor.estimate_confidence(text)
                detected_lang = self.processor.detect_language(text)
                normalized = self.processor._normalize_text(text)
                has_mixed = self.processor._has_mixed_scripts(text)
                
                end_time = time.time()
                times.append((end_time - start_time) * 1000)  # Convert to milliseconds
            
            # Calculate statistics
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            
            results[category] = {
                "avg_ms": avg_time,
                "max_ms": max_time,
                "min_ms": min_time,
                "text_length": len(text),
                "word_count": len(text.split())
            }
            
            # Performance assertions
            self.assertLess(avg_time, 5.0, f"{category} processing too slow: {avg_time:.2f}ms")
            self.assertLess(max_time, 20.0, f"{category} max processing too slow: {max_time:.2f}ms")
            
            logger.info(f"{category.capitalize()} processing: avg {avg_time:.2f}ms, "
                       f"max {max_time:.2f}ms, words: {len(text.split())}")
        
        self.test_results.append({
            "test": "processing_performance",
            "results": results
        })
    
    def test_concurrent_processing_performance(self):
        """Test performance under concurrent processing load."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        test_text = "This is a test sentence for concurrent processing evaluation."
        num_threads = 5
        operations_per_thread = 50
        
        def worker_function(thread_id: int) -> Dict[str, Any]:
            """Worker function for concurrent processing."""
            times = []
            errors = 0
            
            for i in range(operations_per_thread):
                try:
                    start_time = time.time()
                    
                    # Perform processing operations
                    confidence = self.processor.estimate_confidence(f"{test_text} {thread_id}-{i}")
                    detected_lang = self.processor.detect_language(test_text)
                    
                    end_time = time.time()
                    times.append((end_time - start_time) * 1000)
                    
                except Exception as e:
                    errors += 1
                    logger.error(f"Error in thread {thread_id}, iteration {i}: {e}")
            
            return {
                "thread_id": thread_id,
                "avg_time_ms": sum(times) / len(times) if times else 0,
                "max_time_ms": max(times) if times else 0,
                "errors": errors,
                "operations_completed": len(times)
            }
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Run concurrent test
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_function, i) for i in range(num_threads)]
            thread_results = [future.result() for future in futures]
        
        total_time = time.time() - start_time
        
        # Analyze results
        total_operations = sum(r["operations_completed"] for r in thread_results)
        total_errors = sum(r["errors"] for r in thread_results)
        avg_times = [r["avg_time_ms"] for r in thread_results if r["avg_time_ms"] > 0]
        
        overall_avg_time = sum(avg_times) / len(avg_times) if avg_times else 0
        operations_per_second = total_operations / total_time if total_time > 0 else 0
        error_rate = total_errors / (total_operations + total_errors) if (total_operations + total_errors) > 0 else 0
        
        # Get resource usage during concurrent processing
        resource_stats = self.monitor.get_memory_stats()
        
        logger.info(f"Concurrent processing: {total_operations} operations in {total_time:.2f}s")
        logger.info(f"Throughput: {operations_per_second:.1f} ops/sec")
        logger.info(f"Average processing time: {overall_avg_time:.2f}ms")
        logger.info(f"Error rate: {error_rate:.2%}")
        logger.info(f"Peak memory: {resource_stats.get('peak_memory_mb', 0):.1f}MB")
        
        # Performance assertions
        self.assertLess(error_rate, 0.05, f"Too many errors in concurrent processing: {error_rate:.2%}")
        self.assertGreater(operations_per_second, 100, f"Throughput too low: {operations_per_second:.1f} ops/sec")
        self.assertLess(overall_avg_time, 10.0, f"Average processing time too high: {overall_avg_time:.2f}ms")
        
        self.test_results.append({
            "test": "concurrent_processing",
            "total_operations": total_operations,
            "total_time_s": total_time,
            "operations_per_second": operations_per_second,
            "avg_processing_time_ms": overall_avg_time,
            "error_rate": error_rate,
            "peak_memory_mb": resource_stats.get("peak_memory_mb", 0),
            "thread_results": thread_results
        })
    
    def test_memory_cleanup_after_processing(self):
        """Test memory cleanup after processing completes."""
        if not MEMORY_MONITORING_AVAILABLE:
            self.skipTest("Memory monitoring not available")
        
        self.monitor.start_monitoring()
        
        # Get baseline memory
        time.sleep(0.5)
        baseline_memory = self.monitor.memory_snapshots[-1].rss_mb if self.monitor.memory_snapshots else 0
        
        # Create and use processor
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Perform intensive processing
        large_text = "This is a test sentence. " * 1000
        for i in range(50):
            confidence = self.processor.estimate_confidence(large_text)
            detected_lang = self.processor.detect_language(large_text[:100])  # Limit for language detection
        
        # Get peak memory during processing
        peak_memory = max(s.rss_mb for s in self.monitor.memory_snapshots[-20:])
        
        # Shutdown processor and cleanup
        self.processor.shutdown()
        self.processor = None
        
        # Force garbage collection
        gc.collect()
        
        # Wait for cleanup
        time.sleep(2)
        
        # Get final memory
        final_memory = self.monitor.memory_snapshots[-1].rss_mb if self.monitor.memory_snapshots else 0
        
        memory_released = peak_memory - final_memory
        memory_growth_from_baseline = final_memory - baseline_memory
        
        logger.info(f"Memory cleanup test:")
        logger.info(f"  Baseline: {baseline_memory:.1f}MB")
        logger.info(f"  Peak: {peak_memory:.1f}MB")
        logger.info(f"  Final: {final_memory:.1f}MB")
        logger.info(f"  Released: {memory_released:.1f}MB")
        logger.info(f"  Growth from baseline: {memory_growth_from_baseline:.1f}MB")
        
        # Assertions
        self.assertGreater(memory_released, 0, "No memory was released after cleanup")
        self.assertLess(memory_growth_from_baseline, 20, "Too much memory retained after cleanup")
        
        self.test_results.append({
            "test": "memory_cleanup",
            "baseline_mb": baseline_memory,
            "peak_mb": peak_memory,
            "final_mb": final_memory,
            "released_mb": memory_released,
            "growth_from_baseline_mb": memory_growth_from_baseline
        })
    
    def test_long_running_stability(self):
        """Test stability during long-running operations."""
        if not MEMORY_MONITORING_AVAILABLE:
            self.skipTest("Memory monitoring not available")
        
        self.monitor.start_monitoring()
        
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Run for extended period (reduced for testing)
        test_duration = 30  # seconds
        operation_interval = 0.1  # 100ms between operations
        
        test_phrases = [
            "Hello world",
            "नमस्ते दोस्त",
            "Hello नमस्ते mixed",
            "The weather is beautiful",
            "मौसम बहुत अच्छा है"
        ]
        
        start_time = time.time()
        operations_completed = 0
        errors = []
        
        while time.time() - start_time < test_duration:
            try:
                phrase = test_phrases[operations_completed % len(test_phrases)]
                
                # Perform operations
                confidence = self.processor.estimate_confidence(phrase)
                detected_lang = self.processor.detect_language(phrase)
                
                operations_completed += 1
                
                # Add some transcription history
                if operations_completed % 10 == 0:
                    from transcribe import TranscriptionResult
                    result = TranscriptionResult(
                        text=phrase,
                        confidence=confidence,
                        language=detected_lang or "en",
                        is_final=True
                    )
                    self.processor.transcription_history.append(result)
                
                time.sleep(operation_interval)
                
            except Exception as e:
                errors.append((operations_completed, str(e)))
                logger.error(f"Error in long-running test at operation {operations_completed}: {e}")
        
        actual_duration = time.time() - start_time
        
        # Analyze stability
        final_stats = self.monitor.get_memory_stats()
        has_leak, leak_info = self.monitor.detect_memory_leaks(threshold_mb=15)
        
        operations_per_second = operations_completed / actual_duration
        error_rate = len(errors) / max(1, operations_completed)
        
        logger.info(f"Long-running stability test:")
        logger.info(f"  Duration: {actual_duration:.1f}s")
        logger.info(f"  Operations: {operations_completed}")
        logger.info(f"  Rate: {operations_per_second:.1f} ops/sec")
        logger.info(f"  Errors: {len(errors)} ({error_rate:.2%})")
        logger.info(f"  Memory growth: {final_stats.get('memory_growth_mb', 0):.1f}MB")
        logger.info(f"  History size: {len(self.processor.transcription_history)}")
        
        # Stability assertions
        self.assertLess(error_rate, 0.01, f"Too many errors in long-running test: {error_rate:.2%}")
        self.assertFalse(has_leak, f"Memory leak in long-running test: {leak_info}")
        self.assertLess(final_stats.get("memory_growth_mb", 0), 25, "Excessive memory growth")
        
        self.test_results.append({
            "test": "long_running_stability",
            "duration_s": actual_duration,
            "operations_completed": operations_completed,
            "operations_per_second": operations_per_second,
            "error_count": len(errors),
            "error_rate": error_rate,
            "memory_growth_mb": final_stats.get("memory_growth_mb", 0),
            "has_memory_leak": has_leak,
            "history_size": len(self.processor.transcription_history)
        })

class MemoryOptimizationTestSuite(unittest.TestCase):
    """Tests for memory optimization features."""
    
    def setUp(self):
        """Set up memory optimization tests."""
        self.monitor = SystemResourceMonitor()
        self.processor = None
        
    def tearDown(self):
        """Clean up memory optimization tests."""
        if self.processor:
            self.processor.shutdown()
        self.monitor.stop_monitoring()
    
    def test_transcription_history_management(self):
        """Test transcription history size management."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Check initial history size limit
        cache_limit = self.processor._TRANSCRIPTION_CACHE_SIZE
        self.assertGreater(cache_limit, 0, "Cache size limit not set")
        
        # Add many transcriptions to test limit enforcement
        from transcribe import TranscriptionResult
        
        initial_count = len(self.processor.transcription_history)
        
        # Add more than the cache limit
        for i in range(cache_limit + 50):
            result = TranscriptionResult(
                text=f"Test transcription {i}",
                confidence=0.9,
                language="en",
                is_final=True
            )
            self.processor.transcription_history.append(result)
        
        final_count = len(self.processor.transcription_history)
        
        # Should not exceed cache limit
        self.assertLessEqual(final_count, cache_limit, 
                           f"History size {final_count} exceeds limit {cache_limit}")
        
        # Should have trimmed to cache limit
        self.assertEqual(final_count, cache_limit, 
                        f"History not properly managed: {final_count} vs {cache_limit}")
        
        logger.info(f"History management: {initial_count} → {final_count} (limit: {cache_limit})")
    
    def test_processing_times_buffer_management(self):
        """Test processing times buffer management."""
        self.processor = OptimizedTranscriptionProcessor(
            source_language="en",
            continuous_mode=True
        )
        
        # Add many processing time measurements
        initial_count = len(self.processor.processing_times)
        
        for i in range(150):  # More than typical buffer limit
            self.processor.processing_times.append(0.001 * i)
        
        # Should be limited to reasonable size (typically 100)
        final_count = len(self.processor.processing_times)
        self.assertLessEqual(final_count, 100, 
                           f"Processing times buffer too large: {final_count}")
        
        logger.info(f"Processing times buffer: {initial_count} → {final_count}")
    
    def test_railway_memory_optimization(self):
        """Test Railway deployment memory optimizations."""
        # Test with Railway environment simulation
        import os
        original_railway = os.environ.get("RAILWAY_DEPLOYMENT")
        
        try:
            os.environ["RAILWAY_DEPLOYMENT"] = "true"
            
            # Import should pick up Railway optimizations
            from transcribe import OptimizedTranscriptionProcessor, DEFAULT_RECORDER_CONFIG
            
            processor = OptimizedTranscriptionProcessor(
                source_language="en",
                continuous_mode=True
            )
            
            # Check Railway-specific optimizations
            cache_size = processor._TRANSCRIPTION_CACHE_SIZE
            auto_save_interval = processor._AUTO_SAVE_INTERVAL
            
            # Should have smaller cache for Railway
            self.assertLessEqual(cache_size, 200, "Cache size not optimized for Railway")
            self.assertLessEqual(auto_save_interval, 50, "Auto-save interval not optimized for Railway")
            
            # Check recorder config optimizations
            config = processor.recorder_config
            self.assertLessEqual(config.get("beam_size", 5), 3, "Beam size not optimized for Railway")
            
            logger.info(f"Railway optimizations: cache={cache_size}, auto_save={auto_save_interval}")
            
            processor.shutdown()
            
        finally:
            if original_railway is None:
                os.environ.pop("RAILWAY_DEPLOYMENT", None)
            else:
                os.environ["RAILWAY_DEPLOYMENT"] = original_railway


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TranscriptionPerformanceTestSuite))
    suite.addTests(loader.loadTestsFromTestCase(MemoryOptimizationTestSuite))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    logger.info("Starting performance and memory validation test suite...")
    
    result = runner.run(suite)
    
    # Print summary
    if hasattr(result, 'test_results'):
        print("\n=== PERFORMANCE TEST SUMMARY ===")
        for test_result in result.test_results:
            print(f"Test: {test_result}")
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)