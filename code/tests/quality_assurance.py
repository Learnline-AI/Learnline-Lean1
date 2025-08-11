"""
Quality Assurance Framework for Live Transcription Testing
=========================================================

Comprehensive QA framework providing:
- Accuracy measurement methodologies
- Performance benchmarking tools
- Quality metrics and KPI tracking
- Test result analysis and reporting
- Automated quality validation

Author: Claude (Anthropic)
Version: 1.0 - QA Testing Framework
"""

import json
import time
import statistics
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionQualityMetrics:
    """Data class for transcription quality metrics."""
    accuracy: float
    confidence: float
    processing_time: float
    language_detection_accuracy: float
    word_error_rate: float
    character_error_rate: float
    semantic_similarity: float
    timestamp: float
    test_category: str
    language: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

@dataclass
class PerformanceMetrics:
    """Data class for performance metrics."""
    avg_processing_time: float
    max_processing_time: float
    min_processing_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_wps: float  # Words per second
    latency_ms: float
    error_rate: float
    uptime_minutes: float
    timestamp: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

@dataclass
class QualityAssuranceReport:
    """Comprehensive QA report data class."""
    report_id: str
    generated_at: datetime
    test_duration_minutes: float
    total_tests_run: int
    passed_tests: int
    failed_tests: int
    overall_accuracy: float
    performance_metrics: PerformanceMetrics
    quality_metrics: List[TranscriptionQualityMetrics]
    language_breakdown: Dict[str, Dict]
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result['generated_at'] = self.generated_at.isoformat()
        return result

class AccuracyMeasurement:
    """Comprehensive accuracy measurement tools."""
    
    @staticmethod
    def word_error_rate(reference: str, hypothesis: str) -> float:
        """Calculate Word Error Rate (WER) between reference and hypothesis."""
        ref_words = reference.lower().split()
        hyp_words = hypothesis.lower().split()
        
        if not ref_words:
            return 0.0 if not hyp_words else 1.0
        
        # Dynamic programming for edit distance
        dp = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
        
        # Initialize first row and column
        for i in range(len(ref_words) + 1):
            dp[i][0] = i
        for j in range(len(hyp_words) + 1):
            dp[0][j] = j
        
        # Fill DP table
        for i in range(1, len(ref_words) + 1):
            for j in range(1, len(hyp_words) + 1):
                if ref_words[i-1] == hyp_words[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],    # Deletion
                        dp[i][j-1],    # Insertion
                        dp[i-1][j-1]   # Substitution
                    )
        
        return dp[len(ref_words)][len(hyp_words)] / len(ref_words)
    
    @staticmethod
    def character_error_rate(reference: str, hypothesis: str) -> float:
        """Calculate Character Error Rate (CER) between reference and hypothesis."""
        if not reference:
            return 0.0 if not hypothesis else 1.0
        
        # Remove spaces for character-level comparison
        ref_chars = list(reference.lower().replace(' ', ''))
        hyp_chars = list(hypothesis.lower().replace(' ', ''))
        
        # Dynamic programming for edit distance
        dp = [[0] * (len(hyp_chars) + 1) for _ in range(len(ref_chars) + 1)]
        
        # Initialize
        for i in range(len(ref_chars) + 1):
            dp[i][0] = i
        for j in range(len(hyp_chars) + 1):
            dp[0][j] = j
        
        # Fill DP table
        for i in range(1, len(ref_chars) + 1):
            for j in range(1, len(hyp_chars) + 1):
                if ref_chars[i-1] == hyp_chars[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1])
        
        return dp[len(ref_chars)][len(hyp_chars)] / len(ref_chars)
    
    @staticmethod
    def semantic_similarity(reference: str, hypothesis: str) -> float:
        """Calculate semantic similarity using simple token overlap."""
        if not reference or not hypothesis:
            return 0.0
        
        ref_tokens = set(reference.lower().split())
        hyp_tokens = set(hypothesis.lower().split())
        
        if not ref_tokens and not hyp_tokens:
            return 1.0
        
        intersection = len(ref_tokens.intersection(hyp_tokens))
        union = len(ref_tokens.union(hyp_tokens))
        
        return intersection / union if union > 0 else 0.0
    
    @staticmethod
    def language_detection_accuracy(expected_lang: str, detected_lang: str) -> float:
        """Calculate language detection accuracy."""
        if expected_lang == detected_lang:
            return 1.0
        
        # Partial credit for close matches
        if expected_lang in ["hi", "en"] and detected_lang == "hi-en":
            return 0.8  # Code-switching detected when single language expected
        
        if expected_lang == "hi-en" and detected_lang in ["hi", "en"]:
            return 0.6  # Single language detected when code-switching expected
        
        return 0.0

class PerformanceBenchmark:
    """Performance benchmarking and monitoring tools."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.start_time = None
        self.processing_times = []
        self.memory_samples = []
        self.error_count = 0
        self.total_requests = 0
        self.total_words_processed = 0
    
    @contextmanager
    def measure_processing_time(self):
        """Context manager to measure processing time."""
        start_time = time.time()
        try:
            yield
        finally:
            end_time = time.time()
            processing_time = end_time - start_time
            self.processing_times.append(processing_time)
    
    def start_monitoring(self):
        """Start performance monitoring session."""
        self.start_time = time.time()
        self.processing_times.clear()
        self.memory_samples.clear()
        self.error_count = 0
        self.total_requests = 0
        self.total_words_processed = 0
        logger.info("Performance monitoring started")
    
    def record_request(self, word_count: int, success: bool = True):
        """Record a transcription request."""
        self.total_requests += 1
        self.total_words_processed += word_count
        if not success:
            self.error_count += 1
    
    def record_memory_usage(self, memory_mb: float):
        """Record memory usage sample."""
        self.memory_samples.append(memory_mb)
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get comprehensive performance metrics."""
        if not self.start_time:
            raise RuntimeError("Monitoring not started")
        
        uptime_minutes = (time.time() - self.start_time) / 60
        
        # Processing time metrics
        avg_processing_time = statistics.mean(self.processing_times) if self.processing_times else 0.0
        max_processing_time = max(self.processing_times) if self.processing_times else 0.0
        min_processing_time = min(self.processing_times) if self.processing_times else 0.0
        
        # Memory metrics
        avg_memory = statistics.mean(self.memory_samples) if self.memory_samples else 0.0
        
        # Throughput
        throughput_wps = self.total_words_processed / (uptime_minutes * 60) if uptime_minutes > 0 else 0.0
        
        # Error rate
        error_rate = self.error_count / self.total_requests if self.total_requests > 0 else 0.0
        
        # Latency (average processing time in milliseconds)
        latency_ms = avg_processing_time * 1000
        
        return PerformanceMetrics(
            avg_processing_time=avg_processing_time,
            max_processing_time=max_processing_time,
            min_processing_time=min_processing_time,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=0.0,  # Would require psutil for actual measurement
            throughput_wps=throughput_wps,
            latency_ms=latency_ms,
            error_rate=error_rate,
            uptime_minutes=uptime_minutes,
            timestamp=time.time()
        )

class QualityValidator:
    """Quality validation and threshold checking."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize quality validator with thresholds."""
        default_config = {
            "min_accuracy": 0.85,
            "max_wer": 0.15,
            "max_cer": 0.10,
            "min_confidence": 0.70,
            "max_processing_time": 2.0,
            "min_semantic_similarity": 0.75,
            "max_memory_usage_mb": 512,
            "max_error_rate": 0.05
        }
        
        self.thresholds = {**default_config, **(config or {})}
        logger.info(f"Quality validator initialized with thresholds: {self.thresholds}")
    
    def validate_transcription_quality(self, metrics: TranscriptionQualityMetrics) -> Tuple[bool, List[str]]:
        """Validate transcription quality against thresholds."""
        issues = []
        
        if metrics.accuracy < self.thresholds["min_accuracy"]:
            issues.append(f"Accuracy {metrics.accuracy:.3f} below threshold {self.thresholds['min_accuracy']}")
        
        if metrics.word_error_rate > self.thresholds["max_wer"]:
            issues.append(f"WER {metrics.word_error_rate:.3f} above threshold {self.thresholds['max_wer']}")
        
        if metrics.character_error_rate > self.thresholds["max_cer"]:
            issues.append(f"CER {metrics.character_error_rate:.3f} above threshold {self.thresholds['max_cer']}")
        
        if metrics.confidence < self.thresholds["min_confidence"]:
            issues.append(f"Confidence {metrics.confidence:.3f} below threshold {self.thresholds['min_confidence']}")
        
        if metrics.processing_time > self.thresholds["max_processing_time"]:
            issues.append(f"Processing time {metrics.processing_time:.3f}s above threshold {self.thresholds['max_processing_time']}s")
        
        if metrics.semantic_similarity < self.thresholds["min_semantic_similarity"]:
            issues.append(f"Semantic similarity {metrics.semantic_similarity:.3f} below threshold {self.thresholds['min_semantic_similarity']}")
        
        return len(issues) == 0, issues
    
    def validate_performance(self, metrics: PerformanceMetrics) -> Tuple[bool, List[str]]:
        """Validate performance metrics against thresholds."""
        issues = []
        
        if metrics.memory_usage_mb > self.thresholds["max_memory_usage_mb"]:
            issues.append(f"Memory usage {metrics.memory_usage_mb:.1f}MB above threshold {self.thresholds['max_memory_usage_mb']}MB")
        
        if metrics.error_rate > self.thresholds["max_error_rate"]:
            issues.append(f"Error rate {metrics.error_rate:.3f} above threshold {self.thresholds['max_error_rate']}")
        
        if metrics.avg_processing_time > self.thresholds["max_processing_time"]:
            issues.append(f"Average processing time {metrics.avg_processing_time:.3f}s above threshold {self.thresholds['max_processing_time']}s")
        
        return len(issues) == 0, issues
    
    def get_quality_score(self, metrics: TranscriptionQualityMetrics) -> float:
        """Calculate overall quality score (0-100)."""
        # Weighted scoring system
        accuracy_score = metrics.accuracy * 30
        wer_score = max(0, (1 - metrics.word_error_rate)) * 25
        confidence_score = metrics.confidence * 20
        semantic_score = metrics.semantic_similarity * 15
        speed_score = max(0, min(1, (2 - metrics.processing_time) / 2)) * 10
        
        total_score = accuracy_score + wer_score + confidence_score + semantic_score + speed_score
        return min(100, max(0, total_score))

class QualityAssuranceManager:
    """Main QA management class orchestrating all quality assurance activities."""
    
    def __init__(self, output_dir: Optional[Path] = None, config: Optional[Dict] = None):
        """Initialize QA manager."""
        self.output_dir = output_dir or Path(__file__).parent / "qa_results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.accuracy_measurer = AccuracyMeasurement()
        self.performance_monitor = PerformanceBenchmark()
        self.quality_validator = QualityValidator(config)
        
        self.test_results = []
        self.quality_metrics = []
        self.session_start_time = None
        
        logger.info(f"QA Manager initialized. Output dir: {self.output_dir}")
    
    def start_qa_session(self):
        """Start a new QA testing session."""
        self.session_start_time = datetime.now()
        self.performance_monitor.start_monitoring()
        self.test_results.clear()
        self.quality_metrics.clear()
        logger.info("QA session started")
    
    def evaluate_transcription(self, reference: str, hypothesis: str, 
                             expected_language: str, detected_language: str,
                             confidence: float, processing_time: float,
                             test_category: str = "general") -> TranscriptionQualityMetrics:
        """Comprehensive transcription evaluation."""
        
        # Calculate all accuracy metrics
        accuracy = 1 - self.accuracy_measurer.word_error_rate(reference, hypothesis)
        wer = self.accuracy_measurer.word_error_rate(reference, hypothesis)
        cer = self.accuracy_measurer.character_error_rate(reference, hypothesis)
        semantic_sim = self.accuracy_measurer.semantic_similarity(reference, hypothesis)
        lang_acc = self.accuracy_measurer.language_detection_accuracy(expected_language, detected_language)
        
        # Create quality metrics
        metrics = TranscriptionQualityMetrics(
            accuracy=accuracy,
            confidence=confidence,
            processing_time=processing_time,
            language_detection_accuracy=lang_acc,
            word_error_rate=wer,
            character_error_rate=cer,
            semantic_similarity=semantic_sim,
            timestamp=time.time(),
            test_category=test_category,
            language=expected_language
        )
        
        # Record for performance monitoring
        word_count = len(reference.split())
        self.performance_monitor.record_request(word_count, success=accuracy > 0.5)
        
        # Store metrics
        self.quality_metrics.append(metrics)
        
        # Validate quality
        is_valid, issues = self.quality_validator.validate_transcription_quality(metrics)
        quality_score = self.quality_validator.get_quality_score(metrics)
        
        logger.info(f"Transcription evaluated - Accuracy: {accuracy:.3f}, "
                   f"WER: {wer:.3f}, Quality Score: {quality_score:.1f}, "
                   f"Valid: {is_valid}")
        
        if issues:
            logger.warning(f"Quality issues: {', '.join(issues)}")
        
        return metrics
    
    def get_language_breakdown(self) -> Dict[str, Dict]:
        """Get performance breakdown by language."""
        breakdown = {}
        
        for lang in ["en", "hi", "hi-en"]:
            lang_metrics = [m for m in self.quality_metrics if m.language == lang]
            
            if lang_metrics:
                breakdown[lang] = {
                    "count": len(lang_metrics),
                    "avg_accuracy": statistics.mean([m.accuracy for m in lang_metrics]),
                    "avg_wer": statistics.mean([m.word_error_rate for m in lang_metrics]),
                    "avg_confidence": statistics.mean([m.confidence for m in lang_metrics]),
                    "avg_processing_time": statistics.mean([m.processing_time for m in lang_metrics]),
                    "quality_score": statistics.mean([self.quality_validator.get_quality_score(m) for m in lang_metrics])
                }
        
        return breakdown
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if not self.quality_metrics:
            return ["No test data available for recommendations"]
        
        # Overall accuracy analysis
        avg_accuracy = statistics.mean([m.accuracy for m in self.quality_metrics])
        if avg_accuracy < 0.85:
            recommendations.append(f"Overall accuracy ({avg_accuracy:.3f}) is below threshold. Consider model fine-tuning.")
        
        # WER analysis
        avg_wer = statistics.mean([m.word_error_rate for m in self.quality_metrics])
        if avg_wer > 0.15:
            recommendations.append(f"Word Error Rate ({avg_wer:.3f}) is high. Review audio quality and noise reduction.")
        
        # Processing time analysis
        avg_processing_time = statistics.mean([m.processing_time for m in self.quality_metrics])
        if avg_processing_time > 2.0:
            recommendations.append(f"Processing time ({avg_processing_time:.2f}s) is slow. Consider optimization.")
        
        # Language-specific analysis
        lang_breakdown = self.get_language_breakdown()
        
        for lang, stats in lang_breakdown.items():
            if stats["avg_accuracy"] < 0.8:
                lang_name = {"en": "English", "hi": "Hindi", "hi-en": "Code-switching"}[lang]
                recommendations.append(f"{lang_name} accuracy ({stats['avg_accuracy']:.3f}) needs improvement.")
        
        # Confidence analysis
        low_confidence_count = len([m for m in self.quality_metrics if m.confidence < 0.7])
        if low_confidence_count > len(self.quality_metrics) * 0.2:
            recommendations.append("High number of low-confidence transcriptions. Review confidence calibration.")
        
        return recommendations if recommendations else ["System performance meets quality standards."]
    
    def generate_comprehensive_report(self) -> QualityAssuranceReport:
        """Generate comprehensive QA report."""
        if not self.session_start_time:
            raise RuntimeError("QA session not started")
        
        # Calculate test statistics
        total_tests = len(self.quality_metrics)
        passed_tests = len([m for m in self.quality_metrics 
                          if self.quality_validator.validate_transcription_quality(m)[0]])
        failed_tests = total_tests - passed_tests
        
        # Overall accuracy
        overall_accuracy = statistics.mean([m.accuracy for m in self.quality_metrics]) if self.quality_metrics else 0.0
        
        # Performance metrics
        performance_metrics = self.performance_monitor.get_performance_metrics()
        
        # Test duration
        test_duration = (datetime.now() - self.session_start_time).total_seconds() / 60
        
        # Generate report
        report = QualityAssuranceReport(
            report_id=f"QA_{int(time.time())}",
            generated_at=datetime.now(),
            test_duration_minutes=test_duration,
            total_tests_run=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            overall_accuracy=overall_accuracy,
            performance_metrics=performance_metrics,
            quality_metrics=self.quality_metrics,
            language_breakdown=self.get_language_breakdown(),
            recommendations=self.generate_recommendations()
        )
        
        return report
    
    def save_report(self, report: QualityAssuranceReport) -> Path:
        """Save QA report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"qa_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"QA report saved: {report_file}")
        return report_file
    
    def create_summary_dashboard(self, report: QualityAssuranceReport) -> str:
        """Create a text-based summary dashboard."""
        dashboard = f"""
========================================
    TRANSCRIPTION QA SUMMARY REPORT
========================================

Report ID: {report.report_id}
Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}
Test Duration: {report.test_duration_minutes:.1f} minutes

TEST RESULTS SUMMARY
--------------------
Total Tests: {report.total_tests_run}
Passed: {report.passed_tests} ({report.passed_tests/max(1,report.total_tests_run)*100:.1f}%)
Failed: {report.failed_tests} ({report.failed_tests/max(1,report.total_tests_run)*100:.1f}%)
Overall Accuracy: {report.overall_accuracy:.3f} ({report.overall_accuracy*100:.1f}%)

PERFORMANCE METRICS
-------------------
Average Processing Time: {report.performance_metrics.avg_processing_time*1000:.1f} ms
Latency: {report.performance_metrics.latency_ms:.1f} ms
Throughput: {report.performance_metrics.throughput_wps:.1f} words/second
Memory Usage: {report.performance_metrics.memory_usage_mb:.1f} MB
Error Rate: {report.performance_metrics.error_rate*100:.2f}%
System Uptime: {report.performance_metrics.uptime_minutes:.1f} minutes

LANGUAGE BREAKDOWN
------------------"""
        
        for lang, stats in report.language_breakdown.items():
            lang_name = {"en": "English", "hi": "Hindi", "hi-en": "Code-switching"}[lang]
            dashboard += f"""
{lang_name}:
  Tests: {stats['count']}
  Accuracy: {stats['avg_accuracy']:.3f} ({stats['avg_accuracy']*100:.1f}%)
  WER: {stats['avg_wer']:.3f}
  Confidence: {stats['avg_confidence']:.3f}
  Quality Score: {stats['quality_score']:.1f}/100
"""
        
        dashboard += "\nRECOMMENDATIONS\n" + "-" * 15 + "\n"
        for i, rec in enumerate(report.recommendations, 1):
            dashboard += f"{i}. {rec}\n"
        
        dashboard += "\n" + "=" * 40 + "\n"
        
        return dashboard


if __name__ == "__main__":
    # Example usage and testing
    qa_manager = QualityAssuranceManager()
    qa_manager.start_qa_session()
    
    # Simulate some test cases
    test_cases = [
        ("Hello world", "Hello world", "en", "en", 0.95, 0.1),
        ("नमस्ते दोस्त", "नमस्ते दोस्त", "hi", "hi", 0.9, 0.15),
        ("Hello नमस्ते", "Hello नमस्ते", "hi-en", "hi-en", 0.85, 0.2),
    ]
    
    for ref, hyp, exp_lang, det_lang, conf, proc_time in test_cases:
        metrics = qa_manager.evaluate_transcription(
            reference=ref,
            hypothesis=hyp,
            expected_language=exp_lang,
            detected_language=det_lang,
            confidence=conf,
            processing_time=proc_time
        )
    
    # Generate and save report
    report = qa_manager.generate_comprehensive_report()
    report_file = qa_manager.save_report(report)
    
    # Display dashboard
    dashboard = qa_manager.create_summary_dashboard(report)
    print(dashboard)
    
    print(f"Full report saved to: {report_file}")