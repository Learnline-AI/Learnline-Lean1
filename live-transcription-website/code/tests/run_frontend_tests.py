#!/usr/bin/env python3
"""
Frontend Tests Master Runner

This module provides a comprehensive test runner for all frontend validation tests
for the live transcription website. It orchestrates execution of all frontend test suites
and generates consolidated reports.

Test Suites Included:
- HTML Structure and Accessibility Tests
- CSS Responsiveness and Cross-Device Tests  
- JavaScript Functionality Tests
- Language Switching UI Tests
- Export Functionality UI Tests
- Mobile Responsiveness Tests
- User Experience and Navigation Tests
- Browser Compatibility Tests
- Accessibility Validation Tests

Usage:
    python run_frontend_tests.py                    # Run all tests
    python run_frontend_tests.py --suite html       # Run specific suite
    python run_frontend_tests.py --verbose          # Verbose output
    python run_frontend_tests.py --report-only      # Generate consolidated report
"""

import sys
import os
import unittest
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Add the tests directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import all frontend test suites
try:
    from test_frontend_html_accessibility import HTMLAccessibilityTestSuite, run_html_accessibility_tests
    from test_frontend_css_responsiveness import CSSResponsivenessTestSuite, run_responsiveness_tests  
    from test_frontend_javascript_functionality import JavaScriptFunctionalityTestSuite, run_javascript_functionality_tests
    from test_frontend_language_switching_ui import LanguageSwitchingUITestSuite, run_language_switching_ui_tests
    from test_frontend_export_functionality_ui import ExportFunctionalityUITestSuite, run_export_functionality_ui_tests
except ImportError as e:
    print(f"Error importing test suites: {e}")
    print("Make sure all frontend test files are present in the tests directory")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrontendTestRunner:
    """Comprehensive frontend test runner"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.test_suites = {
            'html': {
                'name': 'HTML Structure & Accessibility',
                'test_class': HTMLAccessibilityTestSuite,
                'runner_function': run_html_accessibility_tests,
                'description': 'Validates HTML structure, semantics, and accessibility compliance'
            },
            'css': {
                'name': 'CSS Responsiveness & Cross-Device',
                'test_class': CSSResponsivenessTestSuite,
                'runner_function': run_responsiveness_tests,
                'description': 'Tests CSS responsiveness, mobile optimization, and cross-device compatibility'
            },
            'javascript': {
                'name': 'JavaScript Functionality',
                'test_class': JavaScriptFunctionalityTestSuite,
                'runner_function': run_javascript_functionality_tests,
                'description': 'Validates JavaScript functionality, WebSocket, audio processing, and UI interactions'
            },
            'language': {
                'name': 'Language Switching UI',
                'test_class': LanguageSwitchingUITestSuite,
                'runner_function': run_language_switching_ui_tests,
                'description': 'Tests Hindi/English language switching and multilingual support'
            },
            'export': {
                'name': 'Export Functionality UI',
                'test_class': ExportFunctionalityUITestSuite,
                'runner_function': run_export_functionality_ui_tests,
                'description': 'Validates export functionality, file downloads, and clipboard operations'
            }
        }
        
        self.results = {}
        self.start_time = None
        self.end_time = None
        
    def run_all_tests(self, selected_suites: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run all or selected frontend test suites"""
        logger.info("Starting comprehensive frontend tests...")
        self.start_time = datetime.now()
        
        suites_to_run = selected_suites if selected_suites else list(self.test_suites.keys())
        
        for suite_key in suites_to_run:
            if suite_key not in self.test_suites:
                logger.warning(f"Unknown test suite: {suite_key}")
                continue
                
            suite_info = self.test_suites[suite_key]
            logger.info(f"\n{'='*60}")
            logger.info(f"Running {suite_info['name']} Tests")
            logger.info(f"{'='*60}")
            logger.info(f"Description: {suite_info['description']}")
            
            suite_start_time = time.time()
            
            try:
                # Run the test suite
                success = suite_info['runner_function'](verbose=self.verbose)
                suite_end_time = time.time()
                
                self.results[suite_key] = {
                    'name': suite_info['name'],
                    'success': success,
                    'duration': suite_end_time - suite_start_time,
                    'timestamp': datetime.now().isoformat()
                }
                
                status = "PASSED" if success else "FAILED"
                logger.info(f"{suite_info['name']}: {status} (Duration: {suite_end_time - suite_start_time:.2f}s)")
                
            except Exception as e:
                suite_end_time = time.time()
                logger.error(f"Error running {suite_info['name']}: {str(e)}")
                
                self.results[suite_key] = {
                    'name': suite_info['name'],
                    'success': False,
                    'error': str(e),
                    'duration': suite_end_time - suite_start_time,
                    'timestamp': datetime.now().isoformat()
                }
        
        self.end_time = datetime.now()
        return self.results
    
    def generate_consolidated_report(self) -> Dict[str, Any]:
        """Generate consolidated frontend test report"""
        if not self.results:
            logger.warning("No test results available for report generation")
            return {}
        
        total_duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        # Calculate overall statistics
        total_suites = len(self.results)
        passed_suites = sum(1 for result in self.results.values() if result['success'])
        failed_suites = total_suites - passed_suites
        
        report = {
            'execution_summary': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'total_duration_seconds': total_duration,
                'total_test_suites': total_suites,
                'passed_suites': passed_suites,
                'failed_suites': failed_suites,
                'success_rate': (passed_suites / total_suites * 100) if total_suites > 0 else 0
            },
            'test_suite_results': self.results,
            'frontend_readiness': self._calculate_frontend_readiness(),
            'recommendations': self._generate_recommendations(),
            'next_steps': self._generate_next_steps()
        }
        
        return report
    
    def _calculate_frontend_readiness(self) -> Dict[str, Any]:
        """Calculate overall frontend readiness score"""
        if not self.results:
            return {'score': 0, 'level': 'Not Ready'}
        
        # Weight different test suites based on importance
        suite_weights = {
            'html': 0.25,      # HTML structure and accessibility
            'css': 0.20,       # Responsive design
            'javascript': 0.30, # Core functionality
            'language': 0.15,  # Multilingual support
            'export': 0.10     # Export features
        }
        
        weighted_score = 0
        total_weight = 0
        
        for suite_key, result in self.results.items():
            if suite_key in suite_weights:
                weight = suite_weights[suite_key]
                score = 100 if result['success'] else 0
                weighted_score += score * weight
                total_weight += weight
        
        final_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Determine readiness level
        if final_score >= 90:
            level = 'Production Ready'
        elif final_score >= 75:
            level = 'Nearly Ready'
        elif final_score >= 60:
            level = 'Needs Minor Fixes'
        elif final_score >= 40:
            level = 'Needs Major Fixes'
        else:
            level = 'Not Ready'
        
        return {
            'score': round(final_score, 1),
            'level': level,
            'breakdown': {
                suite_key: {
                    'weight': suite_weights.get(suite_key, 0),
                    'passed': result['success'],
                    'contribution': suite_weights.get(suite_key, 0) * (100 if result['success'] else 0)
                }
                for suite_key, result in self.results.items()
            }
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        for suite_key, result in self.results.items():
            if not result['success']:
                suite_name = result['name']
                
                if suite_key == 'html':
                    recommendations.append(f"Fix HTML structure and accessibility issues in {suite_name}")
                    recommendations.append("Ensure proper semantic HTML5 markup and ARIA labels")
                
                elif suite_key == 'css':
                    recommendations.append(f"Address responsive design issues in {suite_name}")
                    recommendations.append("Optimize CSS for mobile devices and different screen sizes")
                
                elif suite_key == 'javascript':
                    recommendations.append(f"Fix JavaScript functionality issues in {suite_name}")
                    recommendations.append("Ensure WebSocket, audio processing, and UI interactions work correctly")
                
                elif suite_key == 'language':
                    recommendations.append(f"Improve multilingual support in {suite_name}")
                    recommendations.append("Ensure proper Hindi/English language switching and font support")
                
                elif suite_key == 'export':
                    recommendations.append(f"Fix export functionality issues in {suite_name}")
                    recommendations.append("Ensure TXT, JSON, and clipboard export functions work properly")
        
        if not recommendations:
            recommendations.append("All frontend tests passed! Consider running additional manual testing.")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generate next steps based on test results"""
        next_steps = []
        
        passed_count = sum(1 for result in self.results.values() if result['success'])
        total_count = len(self.results)
        
        if passed_count == total_count:
            next_steps.extend([
                "All automated frontend tests passed!",
                "Proceed with manual browser testing across different devices",
                "Conduct user experience testing with real users",
                "Test with screen readers and assistive technologies",
                "Perform load testing with actual transcription data",
                "Validate Hindi text rendering on different operating systems"
            ])
        else:
            failed_suites = [suite_key for suite_key, result in self.results.items() if not result['success']]
            next_steps.extend([
                f"Address failing test suites: {', '.join(failed_suites)}",
                "Review individual test reports for detailed issues",
                "Fix critical errors before proceeding to manual testing",
                "Re-run tests after implementing fixes"
            ])
        
        return next_steps
    
    def save_report(self, report: Dict[str, Any], output_dir: Optional[Path] = None) -> Path:
        """Save consolidated report to file"""
        if output_dir is None:
            output_dir = Path(__file__).parent
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f'frontend_test_report_{timestamp}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report_file
    
    def print_summary(self, report: Dict[str, Any]):
        """Print test summary to console"""
        print(f"\n{'='*80}")
        print(f"FRONTEND VALIDATION TEST SUMMARY")
        print(f"{'='*80}")
        
        summary = report['execution_summary']
        readiness = report['frontend_readiness']
        
        print(f"Execution Time: {summary['start_time']} to {summary['end_time']}")
        print(f"Total Duration: {summary['total_duration_seconds']:.2f} seconds")
        print(f"Test Suites Run: {summary['total_test_suites']}")
        print(f"Passed: {summary['passed_suites']}")
        print(f"Failed: {summary['failed_suites']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        
        print(f"\nFRONTEND READINESS")
        print(f"Overall Score: {readiness['score']}/100")
        print(f"Readiness Level: {readiness['level']}")
        
        print(f"\nTEST SUITE BREAKDOWN")
        print("-" * 60)
        for suite_key, result in report['test_suite_results'].items():
            status = "PASS" if result['success'] else "FAIL"
            duration = result['duration']
            print(f"{result['name']:<35} | {status:<4} | {duration:>6.2f}s")
        
        if report['recommendations']:
            print(f"\nRECOMMENDATIONS")
            print("-" * 40)
            for i, rec in enumerate(report['recommendations'][:10], 1):
                print(f"{i}. {rec}")
        
        if report['next_steps']:
            print(f"\nNEXT STEPS")
            print("-" * 20)
            for i, step in enumerate(report['next_steps'][:8], 1):
                print(f"{i}. {step}")
        
        print(f"{'='*80}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Frontend Tests Master Runner')
    parser.add_argument('--suite', '-s', choices=['html', 'css', 'javascript', 'language', 'export'],
                       help='Run specific test suite only')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--report-only', '-r', action='store_true',
                       help='Generate consolidated report from existing test results')
    parser.add_argument('--output-dir', '-o', type=Path,
                       help='Output directory for reports')
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = FrontendTestRunner(verbose=args.verbose)
    
    if not args.report_only:
        # Run tests
        selected_suites = [args.suite] if args.suite else None
        results = runner.run_all_tests(selected_suites)
        
        if not results:
            print("No test results available")
            sys.exit(1)
    
    # Generate consolidated report
    report = runner.generate_consolidated_report()
    
    if report:
        # Save report
        report_file = runner.save_report(report, args.output_dir)
        print(f"\nDetailed report saved to: {report_file}")
        
        # Print summary
        runner.print_summary(report)
        
        # Exit with appropriate code
        execution_summary = report['execution_summary']
        success = execution_summary['failed_suites'] == 0
        sys.exit(0 if success else 1)
    else:
        print("Failed to generate report")
        sys.exit(1)


if __name__ == '__main__':
    main()