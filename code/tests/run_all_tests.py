"""
Master Test Runner for Live Transcription QA Suite
==================================================

Comprehensive test execution script that runs all test suites and generates
consolidated reports for the live transcription system.

Features:
- Sequential execution of all test suites
- Consolidated reporting and metrics
- Performance benchmarking
- Quality assurance validation
- Export of test results and recommendations

Author: Claude (Anthropic)
Version: 1.0 - QA Testing Framework
"""

import unittest
import sys
import time
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_execution.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Import all test suites
try:
    from test_transcription_accuracy import TranscriptionAccuracyTestSuite, PerformanceTestSuite
    from test_websocket_functionality import WebSocketFunctionalityTestSuite, WebSocketPerformanceTestSuite  
    from test_performance_memory import TranscriptionPerformanceTestSuite, MemoryOptimizationTestSuite
    from test_language_switching_export import (
        LanguageSwitchingTestSuite, 
        ExportFunctionalityTestSuite, 
        IntegratedLanguageExportTestSuite
    )
    from quality_assurance import QualityAssuranceManager
    from test_data_generator import TranscriptionTestDataGenerator
except ImportError as e:
    logger.error(f"Failed to import test modules: {e}")
    logger.error("Make sure all test files are in the same directory")
    sys.exit(1)

class TestSuiteRunner:
    """Master test suite runner with comprehensive reporting."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """Initialize test suite runner."""
        self.output_dir = output_dir or Path(__file__).parent / "test_results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.test_suites = {}
        self.execution_results = {}
        self.overall_start_time = None
        self.overall_end_time = None
        
        logger.info(f"Test suite runner initialized. Results dir: {self.output_dir}")
    
    def register_test_suites(self):
        """Register all available test suites."""
        self.test_suites = {
            "transcription_accuracy": {
                "suites": [TranscriptionAccuracyTestSuite, PerformanceTestSuite],
                "description": "Transcription accuracy and basic performance tests",
                "priority": 1
            },
            "websocket_functionality": {
                "suites": [WebSocketFunctionalityTestSuite, WebSocketPerformanceTestSuite],
                "description": "WebSocket communication and real-time functionality tests", 
                "priority": 2
            },
            "performance_memory": {
                "suites": [TranscriptionPerformanceTestSuite, MemoryOptimizationTestSuite],
                "description": "Performance benchmarking and memory validation tests",
                "priority": 3
            },
            "language_export": {
                "suites": [LanguageSwitchingTestSuite, ExportFunctionalityTestSuite, IntegratedLanguageExportTestSuite],
                "description": "Language switching and export functionality tests",
                "priority": 4
            }
        }
        
        logger.info(f"Registered {len(self.test_suites)} test suite categories")
    
    def run_test_suite_category(self, category: str) -> Dict[str, Any]:
        """Run a specific test suite category."""
        if category not in self.test_suites:
            raise ValueError(f"Unknown test suite category: {category}")
        
        category_info = self.test_suites[category]
        logger.info(f"Running {category}: {category_info['description']}")
        
        category_start_time = time.time()
        category_results = {
            "category": category,
            "description": category_info["description"],
            "start_time": category_start_time,
            "suite_results": [],
            "total_tests": 0,
            "total_failures": 0,
            "total_errors": 0,
            "total_skipped": 0,
            "success": True
        }
        
        # Run each test suite in the category
        for suite_class in category_info["suites"]:
            logger.info(f"  Running {suite_class.__name__}...")
            
            suite_start_time = time.time()
            
            # Create test suite
            loader = unittest.TestLoader()
            suite = loader.loadTestsFromTestCase(suite_class)
            
            # Run tests with custom result collector
            result = unittest.TestResult()
            suite.run(result)
            
            suite_end_time = time.time()
            suite_duration = suite_end_time - suite_start_time
            
            # Collect suite results
            suite_result = {
                "suite_name": suite_class.__name__,
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "skipped": len(result.skipped),
                "duration": suite_duration,
                "success": result.wasSuccessful(),
                "failure_details": [{"test": str(test), "error": error} for test, error in result.failures],
                "error_details": [{"test": str(test), "error": error} for test, error in result.errors]
            }
            
            category_results["suite_results"].append(suite_result)
            category_results["total_tests"] += result.testsRun
            category_results["total_failures"] += len(result.failures)
            category_results["total_errors"] += len(result.errors)
            category_results["total_skipped"] += len(result.skipped)
            
            if not result.wasSuccessful():
                category_results["success"] = False
            
            logger.info(f"    {suite_class.__name__}: {result.testsRun} tests, "
                       f"{len(result.failures)} failures, {len(result.errors)} errors, "
                       f"{suite_duration:.2f}s")
        
        category_end_time = time.time()
        category_results["end_time"] = category_end_time
        category_results["duration"] = category_end_time - category_start_time
        
        logger.info(f"Completed {category}: {category_results['total_tests']} total tests, "
                   f"{category_results['duration']:.2f}s")
        
        return category_results
    
    def run_all_tests(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run all test suites or specified categories."""
        self.overall_start_time = time.time()
        
        # Determine which categories to run
        if categories:
            categories_to_run = [cat for cat in categories if cat in self.test_suites]
            if not categories_to_run:
                raise ValueError(f"No valid categories found in: {categories}")
        else:
            categories_to_run = sorted(self.test_suites.keys(), 
                                     key=lambda x: self.test_suites[x]["priority"])
        
        logger.info(f"Running test categories: {categories_to_run}")
        
        # Run each category
        for category in categories_to_run:
            try:
                result = self.run_test_suite_category(category)
                self.execution_results[category] = result
            except Exception as e:
                logger.error(f"Failed to run category {category}: {e}")
                self.execution_results[category] = {
                    "category": category,
                    "error": str(e),
                    "success": False
                }
        
        self.overall_end_time = time.time()
        
        # Generate overall results
        overall_results = self.generate_overall_results()
        return overall_results
    
    def generate_overall_results(self) -> Dict[str, Any]:
        """Generate overall test execution results."""
        if not self.overall_start_time or not self.overall_end_time:
            raise RuntimeError("Test execution not completed")
        
        # Calculate totals
        total_tests = sum(r.get("total_tests", 0) for r in self.execution_results.values())
        total_failures = sum(r.get("total_failures", 0) for r in self.execution_results.values())
        total_errors = sum(r.get("total_errors", 0) for r in self.execution_results.values())
        total_skipped = sum(r.get("total_skipped", 0) for r in self.execution_results.values())
        
        successful_categories = len([r for r in self.execution_results.values() if r.get("success", False)])
        total_categories = len(self.execution_results)
        
        overall_success = (total_failures == 0 and total_errors == 0 and 
                          successful_categories == total_categories)
        
        # Calculate pass rate
        pass_rate = ((total_tests - total_failures - total_errors) / max(1, total_tests)) * 100
        
        overall_results = {
            "execution_summary": {
                "start_time": datetime.fromtimestamp(self.overall_start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.overall_end_time).isoformat(),
                "duration_seconds": self.overall_end_time - self.overall_start_time,
                "categories_run": list(self.execution_results.keys()),
                "overall_success": overall_success
            },
            "test_statistics": {
                "total_tests": total_tests,
                "total_failures": total_failures,
                "total_errors": total_errors,
                "total_skipped": total_skipped,
                "pass_rate_percent": pass_rate,
                "successful_categories": successful_categories,
                "total_categories": total_categories
            },
            "category_results": self.execution_results,
            "recommendations": self.generate_recommendations()
        }
        
        return overall_results
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Analyze failures and errors
        total_failures = sum(r.get("total_failures", 0) for r in self.execution_results.values())
        total_errors = sum(r.get("total_errors", 0) for r in self.execution_results.values())
        
        if total_failures > 0:
            recommendations.append(f"Address {total_failures} test failures before deployment")
        
        if total_errors > 0:
            recommendations.append(f"Fix {total_errors} test errors that indicate system issues")
        
        # Category-specific recommendations
        for category, result in self.execution_results.values():
            if not result.get("success", True):
                category_name = category.replace("_", " ").title()
                recommendations.append(f"Review {category_name} functionality - tests failed")
        
        # Performance recommendations
        if "performance_memory" in self.execution_results:
            perf_result = self.execution_results["performance_memory"]
            if perf_result.get("duration", 0) > 300:  # 5 minutes
                recommendations.append("Performance tests taking too long - optimize test execution")
        
        # WebSocket recommendations
        if "websocket_functionality" in self.execution_results:
            ws_result = self.execution_results["websocket_functionality"]
            if not ws_result.get("success", True):
                recommendations.append("WebSocket functionality issues detected - check real-time communication")
        
        # Default recommendation if all passed
        if not recommendations:
            recommendations.append("All tests passed - system ready for deployment")
        
        return recommendations
    
    def save_results(self, results: Dict[str, Any]) -> Path:
        """Save test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.output_dir / f"test_execution_results_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Test results saved: {results_file}")
        return results_file
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable summary report."""
        summary = f"""
{'='*60}
    LIVE TRANSCRIPTION QA TEST EXECUTION SUMMARY
{'='*60}

Execution Time: {results['execution_summary']['start_time']} to {results['execution_summary']['end_time']}
Total Duration: {results['execution_summary']['duration_seconds']:.1f} seconds
Overall Success: {'✓ PASSED' if results['execution_summary']['overall_success'] else '✗ FAILED'}

TEST STATISTICS
{'-'*20}
Total Tests Run: {results['test_statistics']['total_tests']}
Passed: {results['test_statistics']['total_tests'] - results['test_statistics']['total_failures'] - results['test_statistics']['total_errors']}
Failed: {results['test_statistics']['total_failures']}
Errors: {results['test_statistics']['total_errors']}
Skipped: {results['test_statistics']['total_skipped']}
Pass Rate: {results['test_statistics']['pass_rate_percent']:.1f}%

CATEGORY BREAKDOWN
{'-'*20}"""
        
        for category, result in results['category_results'].items():
            status = "✓ PASSED" if result.get('success', False) else "✗ FAILED"
            category_name = category.replace('_', ' ').title()
            
            summary += f"""
{category_name}: {status}
  Tests: {result.get('total_tests', 0)}
  Duration: {result.get('duration', 0):.1f}s
  Failures: {result.get('total_failures', 0)}
  Errors: {result.get('total_errors', 0)}"""
        
        summary += f"""

RECOMMENDATIONS
{'-'*20}"""
        for i, rec in enumerate(results['recommendations'], 1):
            summary += f"\n{i}. {rec}"
        
        summary += f"\n\n{'='*60}\n"
        
        return summary

def main():
    """Main entry point for test execution."""
    parser = argparse.ArgumentParser(description="Live Transcription QA Test Suite")
    parser.add_argument("--categories", nargs="+", 
                       choices=["transcription_accuracy", "websocket_functionality", 
                               "performance_memory", "language_export"],
                       help="Specific test categories to run")
    parser.add_argument("--output-dir", type=Path, 
                       help="Output directory for test results")
    parser.add_argument("--generate-test-data", action="store_true",
                       help="Generate test data before running tests")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Live Transcription QA Test Suite")
    
    # Generate test data if requested
    if args.generate_test_data:
        logger.info("Generating test data...")
        try:
            generator = TranscriptionTestDataGenerator()
            generator.generate_test_suite()
            generator.generate_audio_test_files()
            generator.create_benchmark_dataset()
            logger.info("Test data generation completed")
        except Exception as e:
            logger.error(f"Test data generation failed: {e}")
            return 1
    
    # Initialize test runner
    try:
        runner = TestSuiteRunner(output_dir=args.output_dir)
        runner.register_test_suites()
        
        # Run tests
        results = runner.run_all_tests(categories=args.categories)
        
        # Save results
        results_file = runner.save_results(results)
        
        # Generate and display summary
        summary = runner.generate_summary_report(results)
        print(summary)
        
        # Save summary report
        summary_file = runner.output_dir / f"test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        logger.info(f"Summary report saved: {summary_file}")
        
        # Exit with appropriate code
        exit_code = 0 if results['execution_summary']['overall_success'] else 1
        logger.info(f"Test execution completed with exit code: {exit_code}")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())