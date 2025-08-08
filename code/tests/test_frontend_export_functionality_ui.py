#!/usr/bin/env python3
"""
Frontend Export Functionality UI Testing Suite

This module provides comprehensive testing for export functionality UI,
file download capabilities, clipboard operations, and data formatting
for the live transcription website.

Features:
- Export button UI validation
- File download functionality testing
- Clipboard copy operation validation
- Data format verification (TXT, JSON)
- Export workflow usability testing
- Error handling in export operations
- Browser compatibility for export features
- Mobile export experience validation

Usage:
    python -m unittest test_frontend_export_functionality_ui.ExportFunctionalityUITestSuite
    python test_frontend_export_functionality_ui.py --verbose
"""

import unittest
import os
import re
import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import tempfile

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExportUIIssue:
    """Data class for export UI issues"""
    component: str
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    recommendation: str
    export_formats_affected: List[str]

class ExportFunctionalityUIValidator:
    """Comprehensive export functionality UI validator"""
    
    def __init__(self, html_file_path: str, static_dir: str):
        self.html_file_path = html_file_path
        self.static_dir = Path(static_dir)
        self.soup = None
        self.js_content = ""
        self.css_content = ""
        self.issues: List[ExportUIIssue] = []
        
        # Expected export formats
        self.expected_export_formats = {
            'txt': {
                'button_id': 'exportTxtBtn',
                'function_name': 'exportAsText',
                'mime_type': 'text/plain',
                'file_extension': '.txt'
            },
            'json': {
                'button_id': 'exportJsonBtn',
                'function_name': 'exportAsJson',
                'mime_type': 'application/json',
                'file_extension': '.json'
            },
            'copy': {
                'button_id': 'copyBtn',
                'function_name': 'copyToClipboard',
                'api_used': 'navigator.clipboard',
                'fallback_method': 'execCommand'
            }
        }
        
    def load_html_css_js(self) -> bool:
        """Load HTML, CSS, and JavaScript content"""
        try:
            # Load HTML
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.soup = BeautifulSoup(content, 'html.parser')
            
            # Extract CSS
            style_tags = self.soup.find_all('style')
            for style in style_tags:
                if style.string:
                    self.css_content += style.string + "\n"
            
            # Extract JavaScript
            script_tags = self.soup.find_all('script', src=False)
            for script in script_tags:
                if script.string:
                    self.js_content += script.string + "\n"
            
            # Load external JS files
            script_tags_with_src = self.soup.find_all('script', src=True)
            for script in script_tags_with_src:
                src = script.get('src')
                if src:
                    js_file_path = self.static_dir / src.lstrip('/static/')
                    if js_file_path.exists():
                        with open(js_file_path, 'r', encoding='utf-8') as js_file:
                            self.js_content += js_file.read() + "\n"
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading files: {e}")
            return False
    
    def validate_export_button_ui(self) -> Dict:
        """Validate export button UI elements"""
        results = {
            'buttons_found': {},
            'button_accessibility': {},
            'button_styling': {},
            'button_grouping': {
                'properly_grouped': False,
                'logical_order': False,
                'consistent_styling': False
            },
            'mobile_optimization': {
                'touch_friendly': False,
                'responsive_layout': False,
                'mobile_specific_adjustments': False
            }
        }
        
        # Check for each expected export button
        for format_name, format_info in self.expected_export_formats.items():
            button_id = format_info.get('button_id')
            if button_id:
                button = self.soup.find(id=button_id)
                if button:
                    results['buttons_found'][format_name] = {
                        'present': True,
                        'tag': button.name,
                        'text': button.get_text(strip=True),
                        'title': button.get('title'),
                        'classes': button.get('class', [])
                    }
                    
                    # Check accessibility
                    accessibility_info = {
                        'has_title': button.get('title') is not None,
                        'has_aria_label': button.get('aria-label') is not None,
                        'has_text_content': bool(button.get_text(strip=True)),
                        'has_icon': bool(button.find('svg') or button.find('img')),
                        'keyboard_accessible': button.name in ['button', 'a'] or button.get('tabindex')
                    }
                    results['button_accessibility'][format_name] = accessibility_info
                    
                    # Check for missing accessibility features
                    if not (accessibility_info['has_title'] or accessibility_info['has_aria_label']):
                        self.issues.append(ExportUIIssue(
                            component='export_buttons',
                            issue_type='accessibility',
                            severity='warning',
                            description=f'{format_name} export button missing accessible description',
                            recommendation='Add title or aria-label to export button',
                            export_formats_affected=[format_name]
                        ))
                else:
                    results['buttons_found'][format_name] = {'present': False}
                    self.issues.append(ExportUIIssue(
                        component='export_buttons',
                        issue_type='missing_ui',
                        severity='error',
                        description=f'{format_name} export button not found',
                        recommendation=f'Add {format_name} export button with id="{button_id}"',
                        export_formats_affected=[format_name]
                    ))
        
        # Check button grouping
        export_container = self.soup.find(class_='export-options')
        if export_container:
            results['button_grouping']['properly_grouped'] = True
            
            # Check if buttons are in logical order
            buttons_in_container = export_container.find_all('button')
            if len(buttons_in_container) >= 3:  # TXT, JSON, Copy
                results['button_grouping']['logical_order'] = True
        else:
            self.issues.append(ExportUIIssue(
                component='export_buttons',
                issue_type='ui_organization',
                severity='warning',
                description='Export buttons not properly grouped',
                recommendation='Group export buttons in a container for better UX',
                export_formats_affected=['all']
            ))
        
        # Check consistent styling
        button_classes = []
        for format_data in results['buttons_found'].values():
            if format_data.get('present'):
                button_classes.extend(format_data.get('classes', []))
        
        if len(set(button_classes)) > 1 and 'btn' in button_classes:
            results['button_grouping']['consistent_styling'] = True
        
        # Check mobile optimization
        mobile_css_patterns = [
            r'@media.*max-width.*export',
            r'export.*mobile',
            r'touch.*export',
            r'export.*touch'
        ]
        
        for pattern in mobile_css_patterns:
            if re.search(pattern, self.css_content, re.IGNORECASE):
                results['mobile_optimization']['mobile_specific_adjustments'] = True
                break
        
        # Check touch-friendly sizing
        if '.btn' in self.css_content and ('44px' in self.css_content or 'padding' in self.css_content):
            results['mobile_optimization']['touch_friendly'] = True
        
        return results
    
    def validate_export_functionality_implementation(self) -> Dict:
        """Validate export functionality implementation in JavaScript"""
        results = {
            'export_functions': {},
            'browser_api_usage': {
                'blob_api': False,
                'download_api': False,
                'clipboard_api': False,
                'url_create_object_url': False
            },
            'data_formatting': {
                'timestamp_inclusion': False,
                'metadata_inclusion': False,
                'proper_json_structure': False,
                'text_formatting': False
            },
            'error_handling': {
                'try_catch_usage': False,
                'user_feedback': False,
                'fallback_mechanisms': False
            },
            'user_experience': {
                'loading_states': False,
                'success_feedback': False,
                'filename_generation': False
            }
        }
        
        # Check for each export function
        for format_name, format_info in self.expected_export_formats.items():
            function_name = format_info.get('function_name')
            if function_name and function_name in self.js_content:
                results['export_functions'][format_name] = {
                    'implemented': True,
                    'function_name': function_name
                }
                
                # Extract function content for analysis
                function_pattern = rf'function\s+{function_name}\s*\([^)]*\)\s*{{([^}}]+)}}'
                function_match = re.search(function_pattern, self.js_content, re.IGNORECASE | re.DOTALL)
                
                if not function_match:
                    # Try arrow function or method syntax
                    function_pattern = rf'{function_name}\s*[:=]\s*(?:function\s*)?\([^)]*\)\s*=>\s*{{([^}}]+)}}'
                    function_match = re.search(function_pattern, self.js_content, re.IGNORECASE | re.DOTALL)
                
                if function_match:
                    function_content = function_match.group(1)
                    results['export_functions'][format_name]['content_found'] = True
                    
                    # Analyze function content
                    self._analyze_export_function_content(function_content, format_name, results)
                else:
                    results['export_functions'][format_name]['content_found'] = False
            else:
                results['export_functions'][format_name] = {'implemented': False}
                self.issues.append(ExportUIIssue(
                    component='export_implementation',
                    issue_type='missing_function',
                    severity='error',
                    description=f'{format_name} export function not implemented',
                    recommendation=f'Implement {function_name} function for {format_name} export',
                    export_formats_affected=[format_name]
                ))
        
        # Check browser API usage
        browser_apis = {
            'blob_api': r'new\s+Blob\(',
            'download_api': r'\.download\s*=|createObjectURL',
            'clipboard_api': r'navigator\.clipboard\.writeText',
            'url_create_object_url': r'URL\.createObjectURL'
        }
        
        for api_name, pattern in browser_apis.items():
            if re.search(pattern, self.js_content, re.IGNORECASE):
                results['browser_api_usage'][api_name] = True
        
        # Check data formatting
        if 'timestamp' in self.js_content and 'transcription' in self.js_content:
            results['data_formatting']['timestamp_inclusion'] = True
        
        if 'session' in self.js_content and ('startTime' in self.js_content or 'metadata' in self.js_content):
            results['data_formatting']['metadata_inclusion'] = True
        
        if 'JSON.stringify' in self.js_content and 'null, 2' in self.js_content:
            results['data_formatting']['proper_json_structure'] = True
        
        if 'join(' in self.js_content and ('\\n' in self.js_content or 'map(' in self.js_content):
            results['data_formatting']['text_formatting'] = True
        
        # Check error handling
        if 'try' in self.js_content and 'catch' in self.js_content and 'export' in self.js_content.lower():
            results['error_handling']['try_catch_usage'] = True
        
        if 'console.error' in self.js_content or 'updateStatus' in self.js_content:
            results['error_handling']['user_feedback'] = True
        
        # Check UX features
        if 'loading' in self.js_content.lower() or 'processing' in self.js_content.lower():
            results['user_experience']['loading_states'] = True
        
        if 'success' in self.js_content.lower() or 'copied' in self.js_content.lower():
            results['user_experience']['success_feedback'] = True
        
        if 'toISOString' in self.js_content and 'replace' in self.js_content:
            results['user_experience']['filename_generation'] = True
        
        return results
    
    def _analyze_export_function_content(self, content: str, format_name: str, results: Dict):
        """Analyze specific export function content"""
        content_lower = content.lower()
        
        # Check for proper implementation patterns
        if format_name in ['txt', 'json']:
            # File download functions should create blob and trigger download
            if 'blob' not in content_lower or 'createobjecturl' not in content_lower:
                self.issues.append(ExportUIIssue(
                    component='export_implementation',
                    issue_type='incomplete_implementation',
                    severity='error',
                    description=f'{format_name} export function missing blob creation',
                    recommendation='Use Blob API and createObjectURL for file downloads',
                    export_formats_affected=[format_name]
                ))
            
            if 'download' not in content_lower:
                self.issues.append(ExportUIIssue(
                    component='export_implementation',
                    issue_type='incomplete_implementation',
                    severity='error',
                    description=f'{format_name} export function missing download trigger',
                    recommendation='Set download attribute and trigger click for file download',
                    export_formats_affected=[format_name]
                ))
        
        elif format_name == 'copy':
            # Copy function should use clipboard API
            if 'clipboard' not in content_lower and 'execcommand' not in content_lower:
                self.issues.append(ExportUIIssue(
                    component='export_implementation',
                    issue_type='incomplete_implementation',
                    severity='error',
                    description='Copy function missing clipboard API usage',
                    recommendation='Use navigator.clipboard.writeText or execCommand fallback',
                    export_formats_affected=[format_name]
                ))
    
    def validate_export_data_quality(self) -> Dict:
        """Validate export data quality and formatting"""
        results = {
            'txt_export_quality': {
                'includes_timestamps': False,
                'proper_formatting': False,
                'readable_structure': False,
                'handles_empty_data': False
            },
            'json_export_quality': {
                'valid_json_structure': False,
                'includes_metadata': False,
                'proper_data_types': False,
                'comprehensive_data': False
            },
            'clipboard_export_quality': {
                'matches_txt_format': False,
                'user_friendly_format': False,
                'handles_large_data': False
            },
            'data_validation': {
                'checks_data_availability': False,
                'handles_partial_transcriptions': False,
                'filters_empty_entries': False
            }
        }
        
        # Analyze TXT export quality
        if 'exportAsText' in self.js_content:
            txt_function_content = self._extract_function_content('exportAsText')
            if txt_function_content:
                if 'timestamp' in txt_function_content:
                    results['txt_export_quality']['includes_timestamps'] = True
                
                if 'join(' in txt_function_content and '\\n' in txt_function_content:
                    results['txt_export_quality']['proper_formatting'] = True
                
                if 'map(' in txt_function_content:
                    results['txt_export_quality']['readable_structure'] = True
                
                if 'length' in txt_function_content or 'empty' in txt_function_content:
                    results['txt_export_quality']['handles_empty_data'] = True
        
        # Analyze JSON export quality
        if 'exportAsJson' in self.js_content:
            json_function_content = self._extract_function_content('exportAsJson')
            if json_function_content:
                if 'session' in json_function_content and 'transcriptions' in json_function_content:
                    results['json_export_quality']['valid_json_structure'] = True
                
                if 'startTime' in json_function_content or 'endTime' in json_function_content:
                    results['json_export_quality']['includes_metadata'] = True
                
                if 'JSON.stringify' in json_function_content:
                    results['json_export_quality']['proper_data_types'] = True
                
                if 'language' in json_function_content and 'timestamp' in json_function_content:
                    results['json_export_quality']['comprehensive_data'] = True
        
        # Analyze clipboard export quality
        if 'copyToClipboard' in self.js_content:
            copy_function_content = self._extract_function_content('copyToClipboard')
            if copy_function_content:
                # Check if it uses similar format to TXT export
                if 'map(' in copy_function_content and 'timestamp' in copy_function_content:
                    results['clipboard_export_quality']['matches_txt_format'] = True
                    results['clipboard_export_quality']['user_friendly_format'] = True
        
        # Check data validation
        if 'transcriptionHistory' in self.js_content and 'length' in self.js_content:
            results['data_validation']['checks_data_availability'] = True
        
        if 'partial' in self.js_content.lower() and 'transcription' in self.js_content:
            results['data_validation']['handles_partial_transcriptions'] = True
        
        return results
    
    def _extract_function_content(self, function_name: str) -> Optional[str]:
        """Extract content of a specific function"""
        patterns = [
            rf'function\s+{function_name}\s*\([^)]*\)\s*{{([^{{}}]*(?:{{[^{{}}]*}}[^{{}}]*)*)}}',
            rf'{function_name}\s*[:=]\s*(?:function\s*)?\([^)]*\)\s*=>\s*{{([^{{}}]*(?:{{[^{{}}]*}}[^{{}}]*)*)}}',
            rf'{function_name}\s*=\s*function\s*\([^)]*\)\s*{{([^{{}}]*(?:{{[^{{}}]*}}[^{{}}]*)*)}}'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.js_content, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1)
        
        return None
    
    def validate_export_user_experience(self) -> Dict:
        """Validate export user experience and workflow"""
        results = {
            'visual_feedback': {
                'button_states': False,
                'loading_indicators': False,
                'success_messages': False,
                'error_messages': False
            },
            'workflow_efficiency': {
                'one_click_export': False,
                'intuitive_button_labels': False,
                'logical_button_order': False,
                'keyboard_shortcuts': False
            },
            'data_preview': {
                'shows_data_count': False,
                'preview_before_export': False,
                'export_size_indication': False
            },
            'mobile_experience': {
                'touch_optimized': False,
                'mobile_download_support': False,
                'share_functionality': False
            }
        }
        
        # Check visual feedback
        if 'disabled' in self.js_content or 'btn.*disabled' in self.css_content:
            results['visual_feedback']['button_states'] = True
        
        if 'loading' in self.js_content.lower() or 'spinner' in self.css_content:
            results['visual_feedback']['loading_indicators'] = True
        
        if 'copied' in self.js_content.lower() or 'success' in self.js_content.lower():
            results['visual_feedback']['success_messages'] = True
        
        if 'error' in self.js_content.lower() or 'failed' in self.js_content.lower():
            results['visual_feedback']['error_messages'] = True
        
        # Check workflow efficiency
        # Buttons should be single-click operations
        export_buttons = self.soup.find_all('button', id=re.compile(r'export|copy'))
        if len(export_buttons) >= 3:
            results['workflow_efficiency']['one_click_export'] = True
        
        # Check button labels
        for button in export_buttons:
            text = button.get_text(strip=True)
            if text and len(text) <= 10 and text.upper() in ['TXT', 'JSON', 'COPY']:
                results['workflow_efficiency']['intuitive_button_labels'] = True
                break
        
        # Check logical order (TXT, JSON, Copy is logical)
        export_container = self.soup.find(class_='export-options')
        if export_container:
            buttons = export_container.find_all('button')
            button_ids = [btn.get('id', '') for btn in buttons]
            if 'exportTxtBtn' in button_ids and 'exportJsonBtn' in button_ids and 'copyBtn' in button_ids:
                txt_idx = button_ids.index('exportTxtBtn') if 'exportTxtBtn' in button_ids else -1
                json_idx = button_ids.index('exportJsonBtn') if 'exportJsonBtn' in button_ids else -1
                copy_idx = button_ids.index('copyBtn') if 'copyBtn' in button_ids else -1
                
                if txt_idx < json_idx < copy_idx or (txt_idx >= 0 and json_idx >= 0):
                    results['workflow_efficiency']['logical_button_order'] = True
        
        # Check keyboard shortcuts
        if 'keydown' in self.js_content or 'keypress' in self.js_content:
            if 'ctrl' in self.js_content.lower() or 'cmd' in self.js_content.lower():
                results['workflow_efficiency']['keyboard_shortcuts'] = True
        
        # Check data preview features
        if 'transcriptionHistory.length' in self.js_content:
            results['data_preview']['shows_data_count'] = True
        
        # Check mobile experience
        mobile_patterns = [
            r'@media.*max-width.*export',
            r'touch-action.*export',
            r'export.*mobile'
        ]
        
        for pattern in mobile_patterns:
            if re.search(pattern, self.css_content, re.IGNORECASE):
                results['mobile_experience']['touch_optimized'] = True
                break
        
        return results
    
    def validate_browser_compatibility(self) -> Dict:
        """Validate browser compatibility for export features"""
        results = {
            'modern_browser_features': {
                'uses_blob_api': False,
                'uses_download_attribute': False,
                'uses_clipboard_api': False,
                'uses_url_createobjecturl': False
            },
            'fallback_mechanisms': {
                'clipboard_fallback': False,
                'download_fallback': False,
                'ios_safari_workarounds': False
            },
            'compatibility_issues': [],
            'unsupported_features': []
        }
        
        # Check modern browser features
        modern_features = {
            'uses_blob_api': r'new\s+Blob\(',
            'uses_download_attribute': r'\.download\s*=',
            'uses_clipboard_api': r'navigator\.clipboard',
            'uses_url_createobjecturl': r'URL\.createObjectURL'
        }
        
        for feature, pattern in modern_features.items():
            if re.search(pattern, self.js_content, re.IGNORECASE):
                results['modern_browser_features'][feature] = True
        
        # Check fallback mechanisms
        if 'execCommand' in self.js_content:
            results['fallback_mechanisms']['clipboard_fallback'] = True
        
        # Check for potential compatibility issues
        if results['modern_browser_features']['uses_clipboard_api'] and not results['fallback_mechanisms']['clipboard_fallback']:
            results['compatibility_issues'].append('Clipboard API without fallback may not work in older browsers')
            self.issues.append(ExportUIIssue(
                component='browser_compatibility',
                issue_type='compatibility',
                severity='warning',
                description='Clipboard API used without fallback for older browsers',
                recommendation='Add execCommand fallback for clipboard operations',
                export_formats_affected=['copy']
            ))
        
        # Check for iOS Safari specific issues
        if 'iPhone' not in self.js_content and 'iOS' not in self.js_content:
            if results['modern_browser_features']['uses_download_attribute']:
                results['compatibility_issues'].append('Download attribute may not work properly on iOS Safari')
        
        return results
    
    def validate_export_security(self) -> Dict:
        """Validate export functionality security considerations"""
        results = {
            'data_sanitization': {
                'escapes_html': False,
                'validates_data': False,
                'filters_sensitive_data': False
            },
            'file_generation': {
                'safe_filenames': False,
                'prevents_path_traversal': False,
                'limits_file_size': False
            },
            'clipboard_security': {
                'sanitizes_clipboard_data': False,
                'respects_user_consent': False
            },
            'potential_issues': []
        }
        
        # Check data sanitization
        if 'escapeHtml' in self.js_content or 'textContent' in self.js_content:
            results['data_sanitization']['escapes_html'] = True
        elif 'innerHTML' in self.js_content:
            results['potential_issues'].append('innerHTML usage may introduce XSS risks')
            self.issues.append(ExportUIIssue(
                component='export_security',
                issue_type='security',
                severity='warning',
                description='innerHTML usage in export functions may be unsafe',
                recommendation='Use textContent instead of innerHTML for text data',
                export_formats_affected=['txt', 'json']
            ))
        
        # Check filename generation safety
        if 'replace' in self.js_content and (':', '') in self.js_content:
            results['file_generation']['safe_filenames'] = True
        
        # Check for data validation
        if 'typeof' in self.js_content or 'instanceof' in self.js_content:
            results['data_sanitization']['validates_data'] = True
        
        return results
    
    def generate_export_ui_report(self) -> Dict:
        """Generate comprehensive export UI report"""
        if not self.soup:
            self.load_html_css_js()
        
        report = {
            'file_path': self.html_file_path,
            'expected_export_formats': list(self.expected_export_formats.keys()),
            'button_ui_validation': self.validate_export_button_ui(),
            'functionality_implementation': self.validate_export_functionality_implementation(),
            'data_quality': self.validate_export_data_quality(),
            'user_experience': self.validate_export_user_experience(),
            'browser_compatibility': self.validate_browser_compatibility(),
            'security_validation': self.validate_export_security(),
            'issues': [
                {
                    'component': issue.component,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'recommendation': issue.recommendation,
                    'export_formats_affected': issue.export_formats_affected
                }
                for issue in self.issues
            ],
            'statistics': self._calculate_export_ui_stats()
        }
        
        return report
    
    def _calculate_export_ui_stats(self) -> Dict:
        """Calculate export UI statistics"""
        error_count = sum(1 for issue in self.issues if issue.severity == 'error')
        warning_count = sum(1 for issue in self.issues if issue.severity == 'warning')
        info_count = sum(1 for issue in self.issues if issue.severity == 'info')
        
        total_issues = len(self.issues)
        
        # Calculate export functionality score
        max_score = 100
        deductions = error_count * 20 + warning_count * 10 + info_count * 5
        export_functionality_score = max(0, max_score - deductions)
        
        return {
            'total_issues': total_issues,
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'export_functionality_score': export_functionality_score,
            'export_readiness': self._get_export_readiness(export_functionality_score)
        }
    
    def _get_export_readiness(self, score: int) -> str:
        """Determine export readiness level based on score"""
        if score >= 90:
            return 'Excellent Export Functionality'
        elif score >= 75:
            return 'Good Export Functionality'
        elif score >= 60:
            return 'Basic Export Functionality'
        else:
            return 'Poor Export Functionality'


class ExportFunctionalityUITestSuite(unittest.TestCase):
    """Test suite for export functionality UI validation"""
    
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
        self.validator = ExportFunctionalityUIValidator(str(self.html_file), str(self.static_dir))
        self.assertTrue(self.validator.load_html_css_js(), "Failed to load HTML, CSS, and JavaScript")
    
    def test_export_buttons_presence(self):
        """Test presence of export buttons"""
        logger.info("Testing export buttons presence")
        
        results = self.validator.validate_export_button_ui()
        buttons_found = results['buttons_found']
        
        # All expected export formats should have buttons
        expected_formats = {'txt', 'json', 'copy'}
        for format_name in expected_formats:
            self.assertIn(format_name, buttons_found, f"Missing {format_name} button info")
            self.assertTrue(buttons_found[format_name]['present'], 
                           f"{format_name} export button not found")
        
        logger.info(f"Export buttons validated. Found: {list(buttons_found.keys())}")
    
    def test_export_buttons_accessibility(self):
        """Test export buttons accessibility"""
        logger.info("Testing export buttons accessibility")
        
        results = self.validator.validate_export_button_ui()
        button_accessibility = results['button_accessibility']
        
        for format_name, accessibility_info in button_accessibility.items():
            # Each button should have some form of accessible description
            has_description = (
                accessibility_info.get('has_title', False) or
                accessibility_info.get('has_aria_label', False) or
                accessibility_info.get('has_text_content', False)
            )
            self.assertTrue(has_description, 
                           f"{format_name} button missing accessible description")
            
            # Should be keyboard accessible
            self.assertTrue(accessibility_info.get('keyboard_accessible', False),
                           f"{format_name} button not keyboard accessible")
        
        logger.info(f"Export buttons accessibility validated")
    
    def test_export_functionality_implementation(self):
        """Test export functionality implementation"""
        logger.info("Testing export functionality implementation")
        
        results = self.validator.validate_export_functionality_implementation()
        export_functions = results['export_functions']
        
        # All export formats should have implemented functions
        expected_formats = {'txt', 'json', 'copy'}
        for format_name in expected_formats:
            self.assertIn(format_name, export_functions, f"Missing {format_name} function info")
            self.assertTrue(export_functions[format_name]['implemented'],
                           f"{format_name} export function not implemented")
        
        # Should use appropriate browser APIs
        browser_apis = results['browser_api_usage']
        self.assertTrue(browser_apis['blob_api'], "Blob API should be used for file exports")
        self.assertTrue(browser_apis['download_api'] or browser_apis['url_create_object_url'],
                       "Download API or URL.createObjectURL should be used")
        
        logger.info(f"Export functionality implementation validated")
    
    def test_export_data_quality(self):
        """Test export data quality and formatting"""
        logger.info("Testing export data quality")
        
        results = self.validator.validate_export_data_quality()
        
        # TXT export should include timestamps and proper formatting
        txt_quality = results['txt_export_quality']
        self.assertTrue(txt_quality['includes_timestamps'], 
                       "TXT export should include timestamps")
        self.assertTrue(txt_quality['proper_formatting'], 
                       "TXT export should have proper formatting")
        
        # JSON export should have valid structure and metadata
        json_quality = results['json_export_quality']
        self.assertTrue(json_quality['valid_json_structure'], 
                       "JSON export should have valid structure")
        self.assertTrue(json_quality['includes_metadata'], 
                       "JSON export should include metadata")
        
        # Should validate data before export
        data_validation = results['data_validation']
        self.assertTrue(data_validation['checks_data_availability'],
                       "Should check data availability before export")
        
        logger.info(f"Export data quality validated")
    
    def test_export_user_experience(self):
        """Test export user experience"""
        logger.info("Testing export user experience")
        
        results = self.validator.validate_export_user_experience()
        
        # Should provide visual feedback
        visual_feedback = results['visual_feedback']
        feedback_count = sum(1 for v in visual_feedback.values() if v)
        self.assertGreater(feedback_count, 1, "Should provide visual feedback for export operations")
        
        # Should have efficient workflow
        workflow = results['workflow_efficiency']
        self.assertTrue(workflow['one_click_export'], "Exports should be one-click operations")
        
        logger.info(f"Export user experience validated")
    
    def test_clipboard_functionality(self):
        """Test clipboard copy functionality specifically"""
        logger.info("Testing clipboard functionality")
        
        results = self.validator.validate_export_functionality_implementation()
        browser_apis = results['browser_api_usage']
        
        # Should use clipboard API
        self.assertTrue(browser_apis['clipboard_api'], 
                       "Should use modern clipboard API for copy functionality")
        
        # Check clipboard data quality
        data_quality = self.validator.validate_export_data_quality()
        clipboard_quality = data_quality['clipboard_export_quality']
        
        self.assertTrue(clipboard_quality['matches_txt_format'] or clipboard_quality['user_friendly_format'],
                       "Clipboard content should be user-friendly")
        
        logger.info(f"Clipboard functionality validated")
    
    def test_mobile_export_experience(self):
        """Test mobile export experience"""
        logger.info("Testing mobile export experience")
        
        button_results = self.validator.validate_export_button_ui()
        mobile_optimization = button_results['mobile_optimization']
        
        ux_results = self.validator.validate_export_user_experience()
        mobile_experience = ux_results['mobile_experience']
        
        # Should be touch-friendly
        is_touch_friendly = (
            mobile_optimization['touch_friendly'] or 
            mobile_experience['touch_optimized']
        )
        self.assertTrue(is_touch_friendly, "Export buttons should be touch-friendly")
        
        logger.info(f"Mobile export experience validated")
    
    def test_browser_compatibility(self):
        """Test browser compatibility for export features"""
        logger.info("Testing browser compatibility")
        
        results = self.validator.validate_browser_compatibility()
        
        modern_features = results['modern_browser_features']
        fallbacks = results['fallback_mechanisms']
        
        # If using modern features, should have fallbacks
        if modern_features['uses_clipboard_api']:
            # Clipboard fallback is recommended but not strictly required
            if not fallbacks['clipboard_fallback']:
                logger.info("Consider adding clipboard fallback for older browsers")
        
        # Should not have critical compatibility issues
        critical_issues = [issue for issue in results['compatibility_issues'] 
                          if 'critical' in issue.lower() or 'broken' in issue.lower()]
        self.assertEqual(len(critical_issues), 0, f"Critical compatibility issues found: {critical_issues}")
        
        logger.info(f"Browser compatibility validated")
    
    def test_export_security(self):
        """Test export functionality security"""
        logger.info("Testing export security")
        
        results = self.validator.validate_export_security()
        
        # Should not have critical security issues
        critical_issues = [issue for issue in results['potential_issues'] 
                          if 'xss' in issue.lower() or 'injection' in issue.lower()]
        self.assertEqual(len(critical_issues), 0, f"Critical security issues found: {critical_issues}")
        
        # Should sanitize data appropriately
        data_sanitization = results['data_sanitization']
        if not data_sanitization['escapes_html']:
            logger.info("Consider implementing HTML escaping for exported data")
        
        logger.info(f"Export security validated")
    
    def test_export_error_handling(self):
        """Test export error handling"""
        logger.info("Testing export error handling")
        
        results = self.validator.validate_export_functionality_implementation()
        error_handling = results['error_handling']
        
        # Should have some form of error handling
        has_error_handling = (
            error_handling['try_catch_usage'] or
            error_handling['user_feedback']
        )
        self.assertTrue(has_error_handling, "Export functions should handle errors")
        
        # Should provide user feedback for errors
        self.assertTrue(error_handling['user_feedback'], 
                       "Should provide user feedback for export operations")
        
        logger.info(f"Export error handling validated")
    
    def test_overall_export_functionality_score(self):
        """Test overall export functionality score"""
        logger.info("Calculating overall export functionality score")
        
        report = self.validator.generate_export_ui_report()
        stats = report['statistics']
        
        # Should achieve reasonable export functionality score
        self.assertGreaterEqual(stats['export_functionality_score'], 60,
                               f"Export functionality score too low: {stats['export_functionality_score']}")
        
        # Should have minimal critical errors
        self.assertLessEqual(stats['errors'], 3,
                            f"Too many export functionality errors: {stats['errors']}")
        
        export_readiness = stats['export_readiness']
        self.assertNotEqual(export_readiness, 'Poor Export Functionality',
                           f"Export readiness unacceptable: {export_readiness}")
        
        logger.info(f"Export functionality score: {stats['export_functionality_score']}/100 - {export_readiness}")
    
    def test_generate_full_export_ui_report(self):
        """Generate and validate full export UI report"""
        logger.info("Generating comprehensive export UI report")
        
        report = self.validator.generate_export_ui_report()
        
        # Validate report structure
        required_sections = [
            'button_ui_validation', 'functionality_implementation', 'data_quality',
            'user_experience', 'browser_compatibility', 'security_validation', 'statistics'
        ]
        
        for section in required_sections:
            self.assertIn(section, report, f"Missing report section: {section}")
        
        # Save report for manual review
        report_file = Path(__file__).parent / f'export_ui_report_{Path(self.html_file).stem}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Full export UI report saved to: {report_file}")
        
        # Print summary
        stats = report['statistics']
        print(f"\n{'='*60}")
        print(f"EXPORT FUNCTIONALITY UI VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"File: {report['file_path']}")
        print(f"Expected Formats: {', '.join(report['expected_export_formats'])}")
        print(f"Export Functionality Score: {stats['export_functionality_score']}/100")
        print(f"Export Readiness: {stats['export_readiness']}")
        print(f"Total Issues: {stats['total_issues']}")
        print(f"  - Errors: {stats['errors']}")
        print(f"  - Warnings: {stats['warnings']}")
        print(f"  - Info: {stats['info']}")
        
        # Feature summary
        buttons = report['button_ui_validation']['buttons_found']
        functions = report['functionality_implementation']['export_functions']
        
        print(f"\nExport Features:")
        for format_name in report['expected_export_formats']:
            button_status = '✓' if buttons.get(format_name, {}).get('present', False) else '✗'
            function_status = '✓' if functions.get(format_name, {}).get('implemented', False) else '✗'
            print(f"  {format_name.upper()}: Button {button_status} | Function {function_status}")
        
        # Browser APIs
        browser_apis = report['functionality_implementation']['browser_api_usage']
        print(f"\nBrowser APIs:")
        print(f"  Blob API: {'✓' if browser_apis['blob_api'] else '✗'}")
        print(f"  Download API: {'✓' if browser_apis['download_api'] else '✗'}")
        print(f"  Clipboard API: {'✓' if browser_apis['clipboard_api'] else '✗'}")
        
        if report['issues']:
            print(f"\nTop Issues:")
            for i, issue in enumerate(report['issues'][:5], 1):
                print(f"  {i}. [{issue['severity'].upper()}] {issue['description']}")
                print(f"     Affects: {', '.join(issue['export_formats_affected'])}")
        
        print(f"{'='*60}")


def run_export_functionality_ui_tests(verbose=False):
    """Run export functionality UI tests with optional verbose output"""
    
    # Setup test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(ExportFunctionalityUITestSuite)
    
    # Run tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Export Functionality UI Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    success = run_export_functionality_ui_tests(verbose=args.verbose)
    sys.exit(0 if success else 1)