# Live Transcription QA Testing Framework

Comprehensive testing framework for the Hindi/English live transcription website, designed to ensure high-quality transcription accuracy, robust real-time performance, and reliable system operation.

## 🎯 Overview

This QA testing framework provides:

- **Transcription Accuracy Testing**: Hindi, English, and code-switching accuracy validation
- **Real-time Performance Testing**: WebSocket communication and latency benchmarks  
- **Memory & Resource Validation**: Memory leak detection and performance optimization
- **Language Switching Tests**: Dynamic language switching and detection accuracy
- **Export Functionality Tests**: JSON, CSV, and text export validation
- **Quality Assurance Metrics**: Comprehensive KPIs and benchmarking

## 📁 Framework Structure

```
tests/
├── __init__.py                           # Package initialization
├── run_all_tests.py                      # Master test runner
├── test_transcription_accuracy.py        # Transcription accuracy tests
├── test_websocket_functionality.py       # WebSocket and real-time tests
├── test_performance_memory.py            # Performance and memory tests
├── test_language_switching_export.py     # Language and export tests
├── test_data_generator.py               # Test data generation
├── quality_assurance.py                 # QA framework and metrics
├── test_data/                           # Generated test data
├── test_results/                        # Test execution results
└── README.md                           # This documentation
```

## 🚀 Quick Start

### Prerequisites

Install required dependencies:

```bash
pip install -r requirements.txt
pip install psutil websockets  # For memory monitoring and WebSocket tests
```

### Run All Tests

```bash
cd tests/
python run_all_tests.py
```

### Run Specific Test Categories

```bash
# Run only transcription accuracy tests
python run_all_tests.py --categories transcription_accuracy

# Run performance and memory tests
python run_all_tests.py --categories performance_memory

# Run multiple categories
python run_all_tests.py --categories transcription_accuracy websocket_functionality
```

### Generate Test Data

```bash
python run_all_tests.py --generate-test-data
```

## 📊 Test Categories

### 1. Transcription Accuracy Tests (`test_transcription_accuracy.py`)

**Purpose**: Validate transcription accuracy for Hindi, English, and code-switching scenarios.

**Test Cases**:
- English transcription accuracy (8 test phrases)
- Hindi transcription accuracy (8 test phrases) 
- Code-switching accuracy (8 mixed phrases)
- Confidence scoring validation
- Language detection accuracy
- Text similarity and deduplication
- Edge cases (empty input, repetitive text, special characters)

**Quality Thresholds**:
- Minimum accuracy: 85%
- Maximum WER (Word Error Rate): 15%
- Maximum CER (Character Error Rate): 10%
- Minimum confidence: 70%

**Usage**:
```bash
python -m unittest test_transcription_accuracy.TranscriptionAccuracyTestSuite
```

### 2. WebSocket Functionality Tests (`test_websocket_functionality.py`)

**Purpose**: Validate real-time WebSocket communication and message handling.

**Test Cases**:
- WebSocket connection establishment
- JSON message handling (language changes, exports)
- Audio data transmission
- Real-time transcription flow
- Language switching commands
- Export functionality via WebSocket
- Connection stability under load
- Message ordering and integrity
- Connection latency benchmarks
- Message throughput testing

**Performance Thresholds**:
- Connection latency: < 1 second average
- Message throughput: > 50 messages/second
- Error rate: < 5%

**Usage**:
```bash
python -m unittest test_websocket_functionality.WebSocketFunctionalityTestSuite
```

### 3. Performance & Memory Tests (`test_performance_memory.py`)

**Purpose**: Benchmark performance and validate memory usage patterns.

**Test Cases**:
- Baseline memory usage monitoring
- Memory usage under processing load
- Processing time performance (different text lengths)
- Concurrent processing performance
- Memory cleanup validation
- Long-running stability testing
- Memory leak detection
- Railway deployment optimization validation

**Performance Thresholds**:
- Baseline memory: < 200MB
- Peak memory: < 300MB
- Processing time: < 5ms average for text processing
- Memory growth: < 20MB after cleanup
- Concurrent processing: > 100 operations/second

**Usage**:
```bash
python -m unittest test_performance_memory.TranscriptionPerformanceTestSuite
```

### 4. Language Switching & Export Tests (`test_language_switching_export.py`)

**Purpose**: Validate language switching and data export functionality.

**Test Cases**:
- Basic language switching (en ↔ hi ↔ hi-en)
- Invalid language handling
- Language detection consistency
- Automatic language switching
- JSON export format validation
- Text export format validation
- CSV export format validation
- Export filtering options
- Export metadata inclusion
- Multi-session language persistence

**Quality Thresholds**:
- Language switching success: 100%
- Export format compliance: 100%
- Language detection accuracy: > 70%

**Usage**:
```bash
python -m unittest test_language_switching_export.LanguageSwitchingTestSuite
```

## 🔧 Test Data Generation

The framework includes comprehensive test data generation:

### Generate Test Suite
```bash
python test_data_generator.py
```

**Generated Data**:
- English test phrases (10 categories)
- Hindi test phrases (10 categories) 
- Code-switching phrases (10 categories)
- Edge case scenarios (10 categories)
- Synthetic audio files (6 scenarios)
- Benchmark dataset with reference accuracy

**Test Data Categories**:
- **Greeting**: Basic conversational phrases
- **Business**: Professional communication
- **Technical**: Technology-related content
- **Conversational**: Everyday speech
- **Edge Cases**: Challenging scenarios

## 📈 Quality Assurance Framework

The QA framework (`quality_assurance.py`) provides:

### Accuracy Measurement
- **Word Error Rate (WER)**: Industry-standard accuracy metric
- **Character Error Rate (CER)**: Character-level accuracy
- **Semantic Similarity**: Content preservation measurement
- **Language Detection Accuracy**: Multi-language validation

### Performance Benchmarking
- Processing time measurement
- Memory usage monitoring  
- Throughput calculation
- Resource utilization tracking

### Quality Validation
- Automated threshold checking
- Quality score calculation (0-100)
- Performance regression detection
- Recommendation generation

### Usage Example
```python
from quality_assurance import QualityAssuranceManager

qa_manager = QualityAssuranceManager()
qa_manager.start_qa_session()

# Evaluate transcription
metrics = qa_manager.evaluate_transcription(
    reference="Hello world",
    hypothesis="Hello world", 
    expected_language="en",
    detected_language="en",
    confidence=0.95,
    processing_time=0.1
)

# Generate comprehensive report
report = qa_manager.generate_comprehensive_report()
qa_manager.save_report(report)
```

## 📋 Test Execution Results

### Result Files
- `test_execution_results_YYYYMMDD_HHMMSS.json`: Detailed JSON results
- `test_summary_YYYYMMDD_HHMMSS.txt`: Human-readable summary
- `qa_report_YYYYMMDD_HHMMSS.json`: Quality assurance analysis

### Sample Summary Report
```
============================================
  LIVE TRANSCRIPTION QA TEST EXECUTION SUMMARY
============================================

Execution Time: 2024-01-15T10:30:00 to 2024-01-15T10:35:45
Total Duration: 345.2 seconds
Overall Success: ✓ PASSED

TEST STATISTICS
----------------
Total Tests Run: 45
Passed: 42
Failed: 2
Errors: 1
Skipped: 0
Pass Rate: 93.3%

CATEGORY BREAKDOWN
------------------
Transcription Accuracy: ✓ PASSED
  Tests: 12, Duration: 45.2s, Failures: 0, Errors: 0

WebSocket Functionality: ✓ PASSED  
  Tests: 10, Duration: 89.7s, Failures: 1, Errors: 0

Performance Memory: ✗ FAILED
  Tests: 15, Duration: 156.3s, Failures: 1, Errors: 1

Language Export: ✓ PASSED
  Tests: 8, Duration: 54.0s, Failures: 0, Errors: 0

RECOMMENDATIONS
---------------
1. Fix memory leak in long-running stability test
2. Address WebSocket connection timeout under load
3. Review performance optimization for Railway deployment
```

## 🎯 Quality Benchmarks & KPIs

### Accuracy Benchmarks
| Metric | Hindi | English | Code-Switching | Target |
|--------|--------|---------|----------------|---------|
| WER | < 15% | < 10% | < 20% | Industry Standard |
| CER | < 10% | < 8% | < 15% | High Quality |
| Confidence | > 80% | > 85% | > 75% | Reliable |
| Language Detection | > 90% | > 95% | > 80% | Accurate |

### Performance Benchmarks  
| Metric | Target | Critical Threshold |
|--------|--------|-------------------|
| Processing Latency | < 100ms | < 500ms |
| Memory Usage | < 200MB | < 512MB |
| Connection Latency | < 1s | < 5s |
| Throughput | > 100 ops/s | > 50 ops/s |

### System Health KPIs
- **Uptime**: > 99.9%
- **Error Rate**: < 1%
- **Memory Growth**: < 10MB/hour
- **CPU Usage**: < 70%

## 🔍 Debugging & Troubleshooting

### Common Issues

**1. WebSocket Connection Failures**
```bash
# Check if server is running
curl http://localhost:8000/api/status

# Run WebSocket tests in isolation
python -m unittest test_websocket_functionality.WebSocketFunctionalityTestSuite.test_connection_establishment
```

**2. Memory Monitoring Unavailable**
```bash
# Install psutil for memory monitoring
pip install psutil

# Verify installation
python -c "import psutil; print(psutil.virtual_memory())"
```

**3. Test Data Missing**
```bash
# Generate test data
python test_data_generator.py

# Verify generation
ls test_data/
```

**4. Import Errors**
```bash
# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Install missing dependencies
pip install -r requirements.txt
```

### Verbose Logging
```bash
python run_all_tests.py --verbose
```

### Custom Test Configuration
```python
# Custom quality thresholds
config = {
    "min_accuracy": 0.90,  # Higher accuracy requirement
    "max_wer": 0.10,       # Lower error tolerance
    "max_processing_time": 1.0  # Faster processing requirement
}

qa_manager = QualityAssuranceManager(config=config)
```

## 📚 Advanced Usage

### Running Individual Tests
```python
import unittest
from test_transcription_accuracy import TranscriptionAccuracyTestSuite

# Run specific test method
suite = unittest.TestSuite()
suite.addTest(TranscriptionAccuracyTestSuite('test_hindi_transcription_accuracy'))
runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
```

### Custom Test Data
```python
from test_data_generator import TranscriptionTestDataGenerator

generator = TranscriptionTestDataGenerator(output_dir=Path("custom_test_data"))

# Add custom test phrases
custom_phrases = [
    {
        "text": "Custom test phrase",
        "language": "en", 
        "category": "custom",
        "expected_confidence": 0.9
    }
]

# Generate with custom data
generator.generate_test_suite()
```

### Continuous Integration
```yaml
# .github/workflows/qa-tests.yml
name: QA Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -r requirements.txt
      - run: cd tests && python run_all_tests.py
```

## 🤝 Contributing

### Adding New Tests
1. Create test class inheriting from `unittest.TestCase`
2. Use descriptive test method names starting with `test_`
3. Include docstrings describing test purpose
4. Add appropriate assertions and logging
5. Update test registration in `run_all_tests.py`

### Quality Guidelines
- Tests should be independent and repeatable
- Use meaningful assertions with descriptive messages
- Include both positive and negative test cases
- Add performance measurements where applicable
- Document expected behavior and thresholds

## 📞 Support

For questions or issues with the testing framework:

1. Check the troubleshooting section above
2. Review test execution logs in `test_execution.log`
3. Run tests in verbose mode: `--verbose`
4. Check individual test files for specific functionality

## 📄 License

This testing framework is part of the Live Transcription Website project and follows the same licensing terms.