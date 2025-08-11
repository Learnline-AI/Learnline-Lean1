#!/usr/bin/env python3
"""
Frontend JavaScript Functionality Test Suite

This module provides comprehensive testing for JavaScript functionality,
WebSocket communication, audio processing, and UI interactions for the live transcription website.

Features:
- WebSocket connection and message handling validation
- Audio API and microphone functionality testing
- UI interaction and event handling verification
- JavaScript error and performance monitoring
- Audio worklet processor validation
- Real-time transcription flow testing
- Browser API compatibility checking

Usage:
    python -m unittest test_frontend_javascript_functionality.JavaScriptFunctionalityTestSuite
    python test_frontend_javascript_functionality.py --verbose
"""

import unittest
import os
import re
import json
import sys
import asyncio
import time
from pathlib import Path
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import tempfile
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class JavaScriptIssue:
    """Data class for JavaScript issues"""
    component: str
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    recommendation: str
    line_number: Optional[int] = None

class JavaScriptFunctionalityValidator:
    """Comprehensive JavaScript functionality validator"""
    
    def __init__(self, html_file_path: str, static_dir: str):
        self.html_file_path = html_file_path
        self.static_dir = Path(static_dir)
        self.soup = None
        self.js_content = {}  # filename -> content
        self.issues: List[JavaScriptIssue] = []
        
        # Expected JavaScript components for the transcription app
        self.expected_components = {
            'websocket': ['WebSocket', 'socket'],
            'audio': ['AudioContext', 'getUserMedia', 'AudioWorkletNode'],
            'ui_elements': ['getElementById', 'addEventListener'],
            'transcription': ['transcriptionHistory', 'currentPartialTranscription'],
            'export': ['exportAsText', 'exportAsJson', 'copyToClipboard'],
            'language': ['languageSelect', 'currentLanguage']
        }
        
    def load_html_and_js(self) -> bool:
        """Load HTML and extract JavaScript content"""
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.soup = BeautifulSoup(content, 'html.parser')
            
            # Extract inline JavaScript
            script_tags = self.soup.find_all('script', src=False)
            for i, script in enumerate(script_tags):
                if script.string:
                    self.js_content[f'inline_script_{i}'] = script.string
            
            # Extract external JavaScript files
            script_tags_with_src = self.soup.find_all('script', src=True)
            for script in script_tags_with_src:
                src = script.get('src')
                if src:
                    # Handle relative paths
                    js_file_path = self.static_dir / src.lstrip('/static/')
                    
                    if js_file_path.exists():
                        try:
                            with open(js_file_path, 'r', encoding='utf-8') as js_file:
                                self.js_content[js_file_path.name] = js_file.read()
                        except Exception as e:
                            logger.warning(f"Could not load JS file {js_file_path}: {e}")
                    else:
                        logger.warning(f"External JS file not found: {js_file_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading HTML/JS: {e}")
            return False
    
    def validate_websocket_implementation(self) -> Dict:
        """Validate WebSocket implementation and usage"""
        results = {
            'websocket_usage': False,
            'connection_handling': {
                'has_onopen': False,
                'has_onmessage': False,
                'has_onclose': False,
                'has_onerror': False
            },
            'message_handling': {
                'sends_json': False,
                'handles_json': False,
                'language_switching': False
            },
            'error_patterns': [],
            'best_practices': []
        }
        
        all_js = '\n'.join(self.js_content.values())
        
        # Check for WebSocket usage
        if 'new WebSocket(' in all_js or 'WebSocket(' in all_js:
            results['websocket_usage'] = True
        else:
            self.issues.append(JavaScriptIssue(
                component='websocket',
                issue_type='missing_feature',
                severity='error',
                description='WebSocket implementation not found',
                recommendation='Implement WebSocket connection for real-time communication'
            ))
        
        # Check connection event handlers
        connection_handlers = {
            'has_onopen': [r'\.onopen\s*=', r'addEventListener\s*\(\s*[\'"]open[\'"]'],
            'has_onmessage': [r'\.onmessage\s*=', r'addEventListener\s*\(\s*[\'"]message[\'"]'],
            'has_onclose': [r'\.onclose\s*=', r'addEventListener\s*\(\s*[\'"]close[\'"]'],
            'has_onerror': [r'\.onerror\s*=', r'addEventListener\s*\(\s*[\'"]error[\'"]']
        }
        
        for handler_name, patterns in connection_handlers.items():
            for pattern in patterns:
                if re.search(pattern, all_js, re.IGNORECASE):
                    results['connection_handling'][handler_name] = True
                    break
        
        # Check for missing handlers
        for handler, has_handler in results['connection_handling'].items():
            if not has_handler:
                self.issues.append(JavaScriptIssue(
                    component='websocket',
                    issue_type='missing_handler',
                    severity='warning',
                    description=f'Missing WebSocket {handler} handler',
                    recommendation=f'Add {handler} event handler for proper connection management'
                ))
        
        # Check message handling
        if 'JSON.stringify(' in all_js:
            results['message_handling']['sends_json'] = True
        if 'JSON.parse(' in all_js:
            results['message_handling']['handles_json'] = True
        
        # Check for language switching in WebSocket messages
        if 'set_language' in all_js or 'language' in all_js:
            results['message_handling']['language_switching'] = True
        
        # Check for best practices
        if 'socket.readyState === WebSocket.OPEN' in all_js:
            results['best_practices'].append('Checks WebSocket ready state before sending')
        
        if 'websocket' in all_js.lower() and 'reconnect' in all_js.lower():
            results['best_practices'].append('Implements reconnection logic')
        
        return results
    
    def validate_audio_api_implementation(self) -> Dict:
        """Validate Web Audio API implementation"""
        results = {
            'audio_context': False,
            'media_stream': False,
            'audio_worklet': False,
            'microphone_access': False,
            'audio_processing': {
                'has_getUserMedia': False,
                'has_audio_worklet_node': False,
                'has_pcm_processing': False,
                'has_cleanup': False
            },
            'browser_compatibility': [],
            'security_considerations': []
        }
        
        all_js = '\n'.join(self.js_content.values())
        
        # Check for Audio API components
        if 'AudioContext' in all_js or 'new AudioContext(' in all_js:
            results['audio_context'] = True
        else:
            self.issues.append(JavaScriptIssue(
                component='audio',
                issue_type='missing_feature',
                severity='error',
                description='AudioContext not found',
                recommendation='Implement AudioContext for audio processing'
            ))
        
        # Check for media stream access
        if 'getUserMedia' in all_js:
            results['microphone_access'] = True
            results['audio_processing']['has_getUserMedia'] = True
        else:
            self.issues.append(JavaScriptIssue(
                component='audio',
                issue_type='missing_feature',
                severity='error',
                description='getUserMedia not found',
                recommendation='Implement getUserMedia for microphone access'
            ))
        
        # Check for Audio Worklet
        if 'AudioWorkletNode' in all_js or 'audioWorklet.addModule' in all_js:
            results['audio_worklet'] = True
            results['audio_processing']['has_audio_worklet_node'] = True
        else:
            self.issues.append(JavaScriptIssue(
                component='audio',
                issue_type='missing_feature',
                severity='warning',
                description='AudioWorklet not found',
                recommendation='Consider using AudioWorklet for better audio processing performance'
            ))
        
        # Check for PCM processing
        if 'Int16Array' in all_js and ('Float32Array' in all_js or 'PCM' in all_js):
            results['audio_processing']['has_pcm_processing'] = True
        
        # Check for resource cleanup
        cleanup_patterns = ['audioContext.close()', 'disconnect()', 'track.stop()']
        for pattern in cleanup_patterns:
            if pattern in all_js:
                results['audio_processing']['has_cleanup'] = True
                break
        
        if not results['audio_processing']['has_cleanup']:
            self.issues.append(JavaScriptIssue(
                component='audio',
                issue_type='resource_management',
                severity='warning',
                description='Audio resource cleanup not found',
                recommendation='Implement proper cleanup for audio resources'
            ))
        
        # Check browser compatibility considerations
        if 'navigator.mediaDevices' in all_js:
            results['browser_compatibility'].append('Uses modern mediaDevices API')
        
        # Check security considerations
        if 'https:' in all_js or 'secure context' in all_js.lower():
            results['security_considerations'].append('Handles HTTPS requirements')
        
        return results
    
    def validate_ui_interactions(self) -> Dict:
        """Validate UI interaction handling"""
        results = {
            'event_listeners': [],
            'dom_manipulation': {
                'element_selection': 0,
                'content_updates': 0,
                'class_manipulation': 0,
                'style_changes': 0
            },
            'button_handlers': {
                'start_button': False,
                'stop_button': False,
                'clear_button': False,
                'export_buttons': False
            },
            'form_handling': [],
            'accessibility_support': [],
            'ui_feedback': []
        }
        
        all_js = '\n'.join(self.js_content.values())
        
        # Count DOM manipulation methods
        dom_methods = {
            'element_selection': ['getElementById', 'querySelector', 'getElementsBy'],
            'content_updates': ['textContent', 'innerHTML', 'innerText', 'appendChild'],
            'class_manipulation': ['classList.add', 'classList.remove', 'classList.toggle', 'className'],
            'style_changes': ['.style.', 'setAttribute']
        }
        
        for category, methods in dom_methods.items():
            count = 0
            for method in methods:
                count += len(re.findall(re.escape(method), all_js, re.IGNORECASE))
            results['dom_manipulation'][category] = count
        
        # Check for event listeners
        event_patterns = [
            r'addEventListener\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'\.on(\w+)\s*='
        ]
        
        for pattern in event_patterns:
            matches = re.findall(pattern, all_js, re.IGNORECASE)
            results['event_listeners'].extend(matches)
        
        # Check specific button handlers
        button_handlers = {
            'start_button': ['startBtn', 'start.*onclick', 'start.*addEventListener'],
            'stop_button': ['stopBtn', 'stop.*onclick', 'stop.*addEventListener'],
            'clear_button': ['clearBtn', 'clear.*onclick', 'clear.*addEventListener'],
            'export_buttons': ['exportTxtBtn', 'exportJsonBtn', 'copyBtn']
        }
        
        for button_type, patterns in button_handlers.items():
            for pattern in patterns:
                if re.search(pattern, all_js, re.IGNORECASE):
                    results['button_handlers'][button_type] = True
                    break
        
        # Check for missing button handlers
        for button, has_handler in results['button_handlers'].items():
            if not has_handler:
                self.issues.append(JavaScriptIssue(
                    component='ui',
                    issue_type='missing_handler',
                    severity='warning',
                    description=f'Missing handler for {button}',
                    recommendation=f'Add event handler for {button} functionality'
                ))
        
        # Check UI feedback patterns
        feedback_patterns = [
            ('visual_feedback', ['classList.add', 'style.display', 'disabled']),
            ('status_updates', ['statusText', 'updateStatus', 'status']),
            ('loading_states', ['loading', 'pending', 'processing'])
        ]
        
        for feedback_type, patterns in feedback_patterns:
            for pattern in patterns:
                if pattern in all_js:
                    results['ui_feedback'].append(feedback_type)
                    break
        
        # Check accessibility support
        accessibility_patterns = [
            ('aria_updates', ['aria-label', 'setAttribute.*aria']),
            ('keyboard_support', ['keydown', 'keypress', 'Enter', 'Space']),
            ('focus_management', ['focus()', 'blur()', 'tabindex'])
        ]
        
        for access_type, patterns in accessibility_patterns:
            for pattern in patterns:
                if re.search(pattern, all_js, re.IGNORECASE):
                    results['accessibility_support'].append(access_type)
                    break
        
        return results
    
    def validate_transcription_logic(self) -> Dict:
        """Validate transcription-specific logic"""
        results = {
            'transcription_state': {
                'has_history': False,
                'has_partial_handling': False,
                'has_final_handling': False,
                'has_language_detection': False
            },
            'data_structures': [],
            'message_processing': {
                'handles_partial': False,
                'handles_final': False,
                'handles_timestamps': False
            },
            'ui_updates': {
                'renders_transcriptions': False,
                'auto_scroll': False,
                'entry_creation': False
            }
        }
        
        all_js = '\n'.join(self.js_content.values())
        
        # Check transcription state management
        state_checks = {
            'has_history': ['transcriptionHistory', 'history'],
            'has_partial_handling': ['currentPartialTranscription', 'partial'],
            'has_final_handling': ['final_transcription', 'final'],
            'has_language_detection': ['language', 'detected_language']
        }
        
        for state_type, patterns in state_checks.items():
            for pattern in patterns:
                if pattern in all_js:
                    results['transcription_state'][state_type] = True
                    break
        
        # Check message processing
        if 'partial_transcription' in all_js:
            results['message_processing']['handles_partial'] = True
        if 'final_transcription' in all_js:
            results['message_processing']['handles_final'] = True
        if 'timestamp' in all_js:
            results['message_processing']['handles_timestamps'] = True
        
        # Check UI update functions
        if 'renderTranscriptions' in all_js or 'render' in all_js:
            results['ui_updates']['renders_transcriptions'] = True
        if 'scrollTop' in all_js or 'scrollHeight' in all_js:
            results['ui_updates']['auto_scroll'] = True
        if 'createTranscriptionEntry' in all_js or 'createElement' in all_js:
            results['ui_updates']['entry_creation'] = True
        
        # Validate critical transcription components
        critical_missing = []
        if not results['transcription_state']['has_history']:
            critical_missing.append('transcription history management')
        if not results['message_processing']['handles_partial']:
            critical_missing.append('partial transcription handling')
        if not results['ui_updates']['renders_transcriptions']:
            critical_missing.append('transcription rendering')
        
        for missing in critical_missing:
            self.issues.append(JavaScriptIssue(
                component='transcription',
                issue_type='missing_feature',
                severity='error',
                description=f'Missing {missing}',
                recommendation=f'Implement {missing} for proper transcription functionality'
            ))
        
        return results
    
    def validate_export_functionality(self) -> Dict:
        """Validate export functionality"""
        results = {
            'export_formats': {
                'text': False,
                'json': False,
                'clipboard': False
            },
            'export_methods': [],
            'data_formatting': {
                'has_timestamps': False,
                'has_metadata': False,
                'proper_structure': False
            },
            'browser_apis': {
                'blob_api': False,
                'download_api': False,
                'clipboard_api': False
            }
        }
        
        all_js = '\n'.join(self.js_content.values())
        
        # Check export formats
        if 'exportAsText' in all_js or 'text/plain' in all_js:
            results['export_formats']['text'] = True
        if 'exportAsJson' in all_js or 'application/json' in all_js:
            results['export_formats']['json'] = True
        if 'copyToClipboard' in all_js or 'navigator.clipboard' in all_js:
            results['export_formats']['clipboard'] = True
        
        # Check for missing export formats
        for format_name, has_format in results['export_formats'].items():
            if not has_format:
                self.issues.append(JavaScriptIssue(
                    component='export',
                    issue_type='missing_feature',
                    severity='info',
                    description=f'Missing {format_name} export functionality',
                    recommendation=f'Consider implementing {format_name} export for better user experience'
                ))
        
        # Check browser APIs
        if 'new Blob(' in all_js:
            results['browser_apis']['blob_api'] = True
        if 'URL.createObjectURL' in all_js or 'download=' in all_js:
            results['browser_apis']['download_api'] = True
        if 'navigator.clipboard.writeText' in all_js:
            results['browser_apis']['clipboard_api'] = True
        
        # Check data formatting
        if 'timestamp' in all_js and ('entry.timestamp' in all_js or 'formatTimestamp' in all_js):
            results['data_formatting']['has_timestamps'] = True
        if 'session' in all_js and ('metadata' in all_js or 'startTime' in all_js):
            results['data_formatting']['has_metadata'] = True
        if 'JSON.stringify' in all_js and 'null, 2' in all_js:
            results['data_formatting']['proper_structure'] = True
        
        return results
    
    def validate_error_handling(self) -> Dict:
        """Validate error handling patterns"""
        results = {
            'try_catch_blocks': 0,
            'error_logging': 0,
            'user_feedback': 0,
            'async_error_handling': 0,
            'common_patterns': [],
            'missing_error_handling': []
        }
        
        all_js = '\n'.join(self.js_content.values())
        
        # Count error handling patterns
        results['try_catch_blocks'] = len(re.findall(r'try\s*{', all_js, re.IGNORECASE))
        results['error_logging'] = len(re.findall(r'console\.error|console\.warn|logger\.error', all_js, re.IGNORECASE))
        results['user_feedback'] = len(re.findall(r'updateStatus.*error|alert\(|showError', all_js, re.IGNORECASE))
        results['async_error_handling'] = len(re.findall(r'\.catch\(|catch\s*\(', all_js, re.IGNORECASE))
        
        # Check common error handling patterns
        patterns = [
            ('websocket_errors', r'socket\.onerror|ws.*error'),
            ('audio_errors', r'getUserMedia.*catch|audio.*error'),
            ('network_errors', r'fetch.*catch|xhr.*error'),
            ('generic_errors', r'catch\s*\(\s*\w*err')
        ]
        
        for pattern_name, pattern in patterns:
            if re.search(pattern, all_js, re.IGNORECASE):
                results['common_patterns'].append(pattern_name)
        
        # Check for potential missing error handling
        risky_operations = [
            ('websocket', 'new WebSocket'),
            ('audio', 'getUserMedia'),
            ('json', 'JSON.parse'),
            ('dom', 'getElementById')
        ]
        
        for operation_type, operation in risky_operations:
            if operation in all_js and operation_type not in results['common_patterns']:
                results['missing_error_handling'].append(operation_type)
                self.issues.append(JavaScriptIssue(
                    component='error_handling',
                    issue_type='missing_error_handling',
                    severity='warning',
                    description=f'Missing error handling for {operation_type} operations',
                    recommendation=f'Add try-catch blocks or .catch() for {operation_type} operations'
                ))
        
        return results
    
    def validate_performance_considerations(self) -> Dict:
        """Validate performance considerations in JavaScript"""
        results = {
            'performance_issues': [],
            'optimizations': [],
            'memory_management': {
                'has_cleanup': False,
                'removes_listeners': False,
                'clears_intervals': False
            },
            'async_patterns': {
                'uses_promises': False,
                'uses_async_await': False,
                'proper_async_handling': False
            }
        }
        
        all_js = '\n'.join(self.js_content.values())
        
        # Check for potential performance issues
        performance_issues = [
            ('frequent_dom_queries', r'getElementById.*getElementById'),
            ('inline_functions', r'addEventListener\([^)]*function\s*\('),
            ('global_variables', r'window\.\w+\s*='),
            ('nested_loops', r'for.*for.*{')
        ]
        
        for issue_type, pattern in performance_issues:
            if re.search(pattern, all_js, re.IGNORECASE):
                results['performance_issues'].append(issue_type)
        
        # Check for optimizations
        optimizations = [
            ('event_delegation', r'addEventListener.*click.*target'),
            ('efficient_selectors', r'querySelector|getElementsByClassName'),
            ('cached_elements', r'const.*Element.*getElementById'),
            ('batch_dom_updates', r'documentFragment|innerHTML.*\+=')
        ]
        
        for opt_type, pattern in optimizations:
            if re.search(pattern, all_js, re.IGNORECASE):
                results['optimizations'].append(opt_type)
        
        # Check memory management
        if any(pattern in all_js for pattern in ['removeEventListener', 'cleanup', 'destroy']):
            results['memory_management']['removes_listeners'] = True
        if any(pattern in all_js for pattern in ['clearInterval', 'clearTimeout']):
            results['memory_management']['clears_intervals'] = True
        if any(pattern in all_js for pattern in ['close()', 'disconnect()', 'stop()']):
            results['memory_management']['has_cleanup'] = True
        
        # Check async patterns
        if 'new Promise(' in all_js or '.then(' in all_js:
            results['async_patterns']['uses_promises'] = True
        if 'async ' in all_js and 'await ' in all_js:
            results['async_patterns']['uses_async_await'] = True
        if '.catch(' in all_js or 'try.*await' in all_js:
            results['async_patterns']['proper_async_handling'] = True
        
        return results
    
    def check_code_quality(self) -> Dict:
        """Check JavaScript code quality and best practices"""
        results = {
            'code_organization': {
                'uses_modules': False,
                'functions_defined': 0,
                'global_scope_pollution': 0,
                'iife_usage': False
            },
            'naming_conventions': {
                'camelCase_functions': 0,
                'descriptive_names': 0,
                'const_usage': 0,
                'let_usage': 0,
                'var_usage': 0
            },
            'best_practices': [],
            'code_smells': []
        }
        
        all_js = '\n'.join(self.js_content.values())
        
        # Check code organization
        results['code_organization']['functions_defined'] = len(re.findall(r'function\s+\w+|const\s+\w+\s*=.*=>', all_js))
        results['code_organization']['global_scope_pollution'] = len(re.findall(r'var\s+\w+\s*=|window\.\w+\s*=', all_js))
        
        if re.search(r'\(function\s*\(|\(\s*\(\)\s*=>', all_js):
            results['code_organization']['iife_usage'] = True
        
        # Check variable declarations
        results['naming_conventions']['const_usage'] = len(re.findall(r'\bconst\s+', all_js))
        results['naming_conventions']['let_usage'] = len(re.findall(r'\blet\s+', all_js))
        results['naming_conventions']['var_usage'] = len(re.findall(r'\bvar\s+', all_js))
        
        # Check naming conventions
        camelCase_functions = re.findall(r'function\s+([a-z][a-zA-Z0-9]*)\s*\(', all_js)
        results['naming_conventions']['camelCase_functions'] = len([name for name in camelCase_functions if name[0].islower()])
        
        # Check best practices
        if "'use strict'" in all_js or '"use strict"' in all_js:
            results['best_practices'].append('uses_strict_mode')
        
        if results['naming_conventions']['const_usage'] > results['naming_conventions']['var_usage']:
            results['best_practices'].append('prefers_const_over_var')
        
        # Check for code smells
        if results['code_organization']['global_scope_pollution'] > 5:
            results['code_smells'].append('excessive_global_variables')
        
        if 'eval(' in all_js:
            results['code_smells'].append('uses_eval')
            self.issues.append(JavaScriptIssue(
                component='code_quality',
                issue_type='security',
                severity='error',
                description='Use of eval() function detected',
                recommendation='Avoid eval() for security reasons, use safer alternatives'
            ))
        
        return results
    
    def generate_functionality_report(self) -> Dict:
        """Generate comprehensive JavaScript functionality report"""
        if not self.js_content:
            self.load_html_and_js()
        
        report = {
            'file_path': self.html_file_path,
            'javascript_files': list(self.js_content.keys()),
            'total_js_lines': sum(len(content.split('\n')) for content in self.js_content.values()),
            'websocket_implementation': self.validate_websocket_implementation(),
            'audio_api_implementation': self.validate_audio_api_implementation(),
            'ui_interactions': self.validate_ui_interactions(),
            'transcription_logic': self.validate_transcription_logic(),
            'export_functionality': self.validate_export_functionality(),
            'error_handling': self.validate_error_handling(),
            'performance_considerations': self.validate_performance_considerations(),
            'code_quality': self.check_code_quality(),
            'issues': [
                {
                    'component': issue.component,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'recommendation': issue.recommendation,
                    'line_number': issue.line_number
                }
                for issue in self.issues
            ],
            'statistics': self._calculate_functionality_stats()
        }
        
        return report
    
    def _calculate_functionality_stats(self) -> Dict:
        """Calculate JavaScript functionality statistics"""
        error_count = sum(1 for issue in self.issues if issue.severity == 'error')
        warning_count = sum(1 for issue in self.issues if issue.severity == 'warning')
        info_count = sum(1 for issue in self.issues if issue.severity == 'info')
        
        total_issues = len(self.issues)
        
        # Calculate functionality score
        max_score = 100
        deductions = error_count * 20 + warning_count * 10 + info_count * 5
        functionality_score = max(0, max_score - deductions)
        
        return {
            'total_issues': total_issues,
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'functionality_score': functionality_score,
            'implementation_status': self._get_implementation_status(functionality_score)
        }
    
    def _get_implementation_status(self, score: int) -> str:
        """Determine implementation status based on score"""
        if score >= 90:
            return 'Excellent Implementation'
        elif score >= 75:
            return 'Good Implementation'
        elif score >= 60:
            return 'Acceptable Implementation'
        else:
            return 'Needs Improvement'


class JavaScriptFunctionalityTestSuite(unittest.TestCase):
    """Test suite for JavaScript functionality validation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.static_dir = Path(__file__).parent.parent / 'static'
        cls.html_file = cls.static_dir / 'index.html'
        cls.validator = None
        
        if not cls.html_file.exists():
            raise FileNotFoundError(f"HTML file not found: {cls.html_file}")
    
    def setUp(self):
        """Set up individual tests"""
        self.validator = JavaScriptFunctionalityValidator(str(self.html_file), str(self.static_dir))
        self.assertTrue(self.validator.load_html_and_js(), "Failed to load HTML and JavaScript")
    
    def test_websocket_implementation(self):
        """Test WebSocket implementation"""
        logger.info("Testing WebSocket implementation")
        
        results = self.validator.validate_websocket_implementation()
        
        self.assertTrue(results['websocket_usage'], "WebSocket implementation not found")
        
        # Check connection handlers
        connection_handlers = results['connection_handling']
        self.assertTrue(connection_handlers['has_onopen'], "Missing WebSocket onopen handler")
        self.assertTrue(connection_handlers['has_onmessage'], "Missing WebSocket onmessage handler")
        self.assertTrue(connection_handlers['has_onclose'], "Missing WebSocket onclose handler")
        
        # Check message handling
        message_handling = results['message_handling']
        self.assertTrue(message_handling['sends_json'] or message_handling['handles_json'],
                       "WebSocket should handle JSON messages")
        
        logger.info(f"WebSocket implementation validated. Handlers: {sum(connection_handlers.values())}/4")
    
    def test_audio_api_implementation(self):
        """Test Web Audio API implementation"""
        logger.info("Testing Web Audio API implementation")
        
        results = self.validator.validate_audio_api_implementation()
        
        self.assertTrue(results['audio_context'], "AudioContext implementation not found")
        self.assertTrue(results['microphone_access'], "getUserMedia implementation not found")
        
        # Check audio processing
        audio_processing = results['audio_processing']
        self.assertTrue(audio_processing['has_getUserMedia'], "getUserMedia not properly implemented")
        
        # Audio worklet is preferred but not strictly required
        if results['audio_worklet']:
            logger.info("AudioWorklet found - excellent for performance")
        else:
            logger.info("AudioWorklet not found - consider implementing for better performance")
        
        logger.info(f"Audio API implementation validated. Features: {sum(1 for v in results.values() if v)}")
    
    def test_ui_interactions(self):
        """Test UI interaction handling"""
        logger.info("Testing UI interactions")
        
        results = self.validator.validate_ui_interactions()
        
        # Should have event listeners
        self.assertGreater(len(results['event_listeners']), 0, "No event listeners found")
        
        # Check DOM manipulation
        dom_manipulation = results['dom_manipulation']
        self.assertGreater(dom_manipulation['element_selection'], 0, "No DOM element selection found")
        self.assertGreater(dom_manipulation['content_updates'], 0, "No DOM content updates found")
        
        # Check button handlers
        button_handlers = results['button_handlers']
        self.assertTrue(button_handlers['start_button'], "Start button handler missing")
        self.assertTrue(button_handlers['stop_button'], "Stop button handler missing")
        
        logger.info(f"UI interactions validated. Event listeners: {len(results['event_listeners'])}")
    
    def test_transcription_logic(self):
        """Test transcription-specific logic"""
        logger.info("Testing transcription logic")
        
        results = self.validator.validate_transcription_logic()
        
        # Check transcription state
        transcription_state = results['transcription_state']
        self.assertTrue(transcription_state['has_history'], "Transcription history management not found")
        self.assertTrue(transcription_state['has_partial_handling'], "Partial transcription handling not found")
        
        # Check message processing
        message_processing = results['message_processing']
        self.assertTrue(message_processing['handles_partial'] or message_processing['handles_final'],
                       "Transcription message processing not found")
        
        # Check UI updates
        ui_updates = results['ui_updates']
        self.assertTrue(ui_updates['renders_transcriptions'], "Transcription rendering not found")
        
        logger.info(f"Transcription logic validated. State management: {sum(transcription_state.values())}/4")
    
    def test_export_functionality(self):
        """Test export functionality"""
        logger.info("Testing export functionality")
        
        results = self.validator.validate_export_functionality()
        
        export_formats = results['export_formats']
        
        # Should have at least one export format
        has_exports = any(export_formats.values())
        self.assertTrue(has_exports, "No export functionality found")
        
        # Check browser API usage
        browser_apis = results['browser_apis']
        if export_formats['text'] or export_formats['json']:
            self.assertTrue(browser_apis['blob_api'], "Blob API required for file downloads")
            self.assertTrue(browser_apis['download_api'], "Download API required for file exports")
        
        if export_formats['clipboard']:
            self.assertTrue(browser_apis['clipboard_api'], "Clipboard API required for copy functionality")
        
        logger.info(f"Export functionality validated. Formats: {sum(export_formats.values())}")
    
    def test_error_handling(self):
        """Test error handling patterns"""
        logger.info("Testing error handling patterns")
        
        results = self.validator.validate_error_handling()
        
        # Should have some error handling
        total_error_handling = (results['try_catch_blocks'] + 
                               results['async_error_handling'] + 
                               results['error_logging'])
        
        self.assertGreater(total_error_handling, 0, "No error handling patterns found")
        
        # Should have minimal missing error handling for critical operations
        self.assertLessEqual(len(results['missing_error_handling']), 2,
                           f"Too many operations without error handling: {results['missing_error_handling']}")
        
        logger.info(f"Error handling validated. Patterns: try-catch: {results['try_catch_blocks']}, "
                   f"async: {results['async_error_handling']}")
    
    def test_performance_considerations(self):
        """Test performance considerations"""
        logger.info("Testing performance considerations")
        
        results = self.validator.validate_performance_considerations()
        
        # Should have some optimizations
        self.assertGreater(len(results['optimizations']), 0, "No performance optimizations found")
        
        # Memory management is important for long-running apps
        memory_management = results['memory_management']
        has_memory_management = any(memory_management.values())
        self.assertTrue(has_memory_management, "No memory management patterns found")
        
        # Should have proper async handling
        async_patterns = results['async_patterns']
        self.assertTrue(async_patterns['uses_promises'] or async_patterns['uses_async_await'],
                       "No modern async patterns found")
        
        logger.info(f"Performance considerations validated. Optimizations: {len(results['optimizations'])}")
    
    def test_code_quality(self):
        """Test code quality and best practices"""
        logger.info("Testing code quality")
        
        results = self.validator.check_code_quality()
        
        code_organization = results['code_organization']
        self.assertGreater(code_organization['functions_defined'], 0, "No functions defined")
        
        # Should prefer const/let over var
        naming = results['naming_conventions']
        modern_declarations = naming['const_usage'] + naming['let_usage']
        self.assertGreaterEqual(modern_declarations, naming['var_usage'],
                               "Should prefer const/let over var")
        
        # Check for code smells
        self.assertNotIn('uses_eval', results['code_smells'], "Avoid using eval() for security")
        
        logger.info(f"Code quality validated. Functions: {code_organization['functions_defined']}, "
                   f"Best practices: {len(results['best_practices'])}")
    
    def test_overall_functionality_score(self):
        """Test overall functionality score"""
        logger.info("Calculating overall functionality score")
        
        report = self.validator.generate_functionality_report()
        stats = report['statistics']
        
        # Should achieve good functionality score
        self.assertGreaterEqual(stats['functionality_score'], 60,
                               f"Functionality score too low: {stats['functionality_score']}")
        
        # Should have minimal critical errors
        self.assertLessEqual(stats['errors'], 5,
                            f"Too many JavaScript functionality errors: {stats['errors']}")
        
        implementation_status = stats['implementation_status']
        self.assertNotEqual(implementation_status, 'Needs Improvement',
                           f"Implementation status unacceptable: {implementation_status}")
        
        logger.info(f"Functionality score: {stats['functionality_score']}/100 - {implementation_status}")
    
    def test_generate_full_functionality_report(self):
        """Generate and validate full functionality report"""
        logger.info("Generating comprehensive JavaScript functionality report")
        
        report = self.validator.generate_functionality_report()
        
        # Validate report structure
        required_sections = [
            'websocket_implementation', 'audio_api_implementation', 'ui_interactions',
            'transcription_logic', 'export_functionality', 'error_handling',
            'performance_considerations', 'code_quality', 'statistics'
        ]
        
        for section in required_sections:
            self.assertIn(section, report, f"Missing report section: {section}")
        
        # Save report for manual review
        report_file = Path(__file__).parent / f'javascript_functionality_report_{Path(self.html_file).stem}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Full functionality report saved to: {report_file}")
        
        # Print summary
        stats = report['statistics']
        print(f"\n{'='*60}")
        print(f"JAVASCRIPT FUNCTIONALITY VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"Files: {', '.join(report['javascript_files'])}")
        print(f"Total JS Lines: {report['total_js_lines']}")
        print(f"Functionality Score: {stats['functionality_score']}/100")
        print(f"Implementation Status: {stats['implementation_status']}")
        print(f"Total Issues: {stats['total_issues']}")
        print(f"  - Errors: {stats['errors']}")
        print(f"  - Warnings: {stats['warnings']}")
        print(f"  - Info: {stats['info']}")
        
        # Feature summary
        websocket = report['websocket_implementation']
        audio = report['audio_api_implementation']
        ui = report['ui_interactions']
        
        print(f"\nFeature Implementation:")
        print(f"  WebSocket: {'✓' if websocket['websocket_usage'] else '✗'}")
        print(f"  Audio API: {'✓' if audio['audio_context'] else '✗'}")
        print(f"  UI Interactions: {'✓' if len(ui['event_listeners']) > 0 else '✗'}")
        print(f"  Export Functions: {'✓' if any(report['export_functionality']['export_formats'].values()) else '✗'}")
        
        if report['issues']:
            print(f"\nTop Issues:")
            for i, issue in enumerate(report['issues'][:5], 1):
                print(f"  {i}. [{issue['severity'].upper()}] {issue['description']}")
                print(f"     Component: {issue['component']}")
        
        print(f"{'='*60}")


def run_javascript_functionality_tests(verbose=False):
    """Run JavaScript functionality tests with optional verbose output"""
    
    # Setup test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(JavaScriptFunctionalityTestSuite)
    
    # Run tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='JavaScript Functionality Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    success = run_javascript_functionality_tests(verbose=args.verbose)
    sys.exit(0 if success else 1)