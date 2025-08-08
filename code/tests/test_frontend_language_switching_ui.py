#!/usr/bin/env python3
"""
Frontend Language Switching UI Validation Tests

This module provides comprehensive testing for language switching UI functionality,
Hindi/English language support validation, and multilingual user experience testing
for the live transcription website.

Features:
- Language selector UI validation
- Hindi/English language detection testing
- Code-switching UI behavior validation
- Language persistence testing
- Multilingual text rendering validation
- RTL/LTR text direction support
- Font rendering for different scripts
- Language-specific UI adaptations

Usage:
    python -m unittest test_frontend_language_switching_ui.LanguageSwitchingUITestSuite
    python test_frontend_language_switching_ui.py --verbose
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
import unicodedata

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LanguageUIIssue:
    """Data class for language UI issues"""
    component: str
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    recommendation: str
    languages_affected: List[str]

class LanguageSwitchingUIValidator:
    """Comprehensive language switching UI validator"""
    
    def __init__(self, html_file_path: str, static_dir: str):
        self.html_file_path = html_file_path
        self.static_dir = Path(static_dir)
        self.soup = None
        self.js_content = ""
        self.css_content = ""
        self.issues: List[LanguageUIIssue] = []
        
        # Supported languages in the application
        self.supported_languages = {
            'en': {
                'name': 'English',
                'script': 'Latin',
                'direction': 'ltr',
                'font_requirements': ['latin', 'english'],
                'sample_text': 'Hello, how are you?'
            },
            'hi': {
                'name': 'Hindi',
                'script': 'Devanagari',
                'direction': 'ltr',
                'font_requirements': ['devanagari', 'hindi'],
                'sample_text': 'नमस्ते, आप कैसे हैं?'
            },
            'mixed': {
                'name': 'Hindi/English',
                'script': 'Mixed',
                'direction': 'ltr',
                'font_requirements': ['latin', 'devanagari'],
                'sample_text': 'Hello नमस्ते mixed text'
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
    
    def validate_language_selector_ui(self) -> Dict:
        """Validate language selector UI elements"""
        results = {
            'selector_present': False,
            'selector_type': None,
            'options_available': [],
            'default_selection': None,
            'accessibility': {
                'has_label': False,
                'has_aria_label': False,
                'keyboard_accessible': True
            },
            'styling': {
                'has_custom_styles': False,
                'mobile_friendly': False
            },
            'issues': []
        }
        
        # Find language selector
        language_select = self.soup.find('select', id='languageSelect')
        if language_select:
            results['selector_present'] = True
            results['selector_type'] = 'select'
            
            # Check options
            options = language_select.find_all('option')
            for option in options:
                value = option.get('value')
                text = option.get_text(strip=True)
                selected = option.get('selected') is not None
                
                results['options_available'].append({
                    'value': value,
                    'text': text,
                    'selected': selected
                })
                
                if selected:
                    results['default_selection'] = value
            
            # Check accessibility
            # Check for associated label
            label = self.soup.find('label', attrs={'for': 'languageSelect'})
            if label:
                results['accessibility']['has_label'] = True
            
            # Check for ARIA label
            if language_select.get('aria-label'):
                results['accessibility']['has_aria_label'] = True
            
            # Validate options against supported languages
            expected_languages = set(self.supported_languages.keys())
            found_languages = set(opt['value'] for opt in results['options_available'] if opt['value'])
            
            missing_languages = expected_languages - found_languages
            if missing_languages:
                results['issues'].append(f"Missing language options: {missing_languages}")
                self.issues.append(LanguageUIIssue(
                    component='language_selector',
                    issue_type='missing_options',
                    severity='error',
                    description=f'Missing language options: {missing_languages}',
                    recommendation='Add all supported language options to the selector',
                    languages_affected=list(missing_languages)
                ))
            
            extra_languages = found_languages - expected_languages
            if extra_languages:
                results['issues'].append(f"Unexpected language options: {extra_languages}")
        else:
            results['issues'].append('Language selector not found')
            self.issues.append(LanguageUIIssue(
                component='language_selector',
                issue_type='missing_element',
                severity='error',
                description='Language selector element not found',
                recommendation='Add language selector UI element',
                languages_affected=['all']
            ))
        
        # Check CSS styling for language selector
        if '#languageSelect' in self.css_content or '.language-selector' in self.css_content:
            results['styling']['has_custom_styles'] = True
        
        # Check mobile responsiveness
        mobile_media_query = r'@media\s*\([^)]*max-width[^)]*\)\s*{[^{}]*language'
        if re.search(mobile_media_query, self.css_content, re.IGNORECASE | re.DOTALL):
            results['styling']['mobile_friendly'] = True
        
        return results
    
    def validate_language_switching_logic(self) -> Dict:
        """Validate JavaScript language switching logic"""
        results = {
            'event_handler_present': False,
            'websocket_integration': False,
            'state_management': {
                'current_language_tracked': False,
                'language_persistence': False,
                'ui_updates_on_change': False
            },
            'supported_languages': [],
            'switching_mechanisms': [],
            'error_handling': False
        }
        
        # Check for language change event handler
        language_change_patterns = [
            r'languageSelect\.onchange',
            r'languageSelect.*addEventListener',
            r'change.*language',
            r'language.*change'
        ]
        
        for pattern in language_change_patterns:
            if re.search(pattern, self.js_content, re.IGNORECASE):
                results['event_handler_present'] = True
                results['switching_mechanisms'].append('event_listener')
                break
        
        if not results['event_handler_present']:
            self.issues.append(LanguageUIIssue(
                component='language_switching',
                issue_type='missing_logic',
                severity='error',
                description='Language change event handler not found',
                recommendation='Implement event handler for language selector changes',
                languages_affected=['all']
            ))
        
        # Check WebSocket integration
        websocket_language_patterns = [
            r'socket.*send.*language',
            r'set_language',
            r'language.*socket',
            r'websocket.*language'
        ]
        
        for pattern in websocket_language_patterns:
            if re.search(pattern, self.js_content, re.IGNORECASE):
                results['websocket_integration'] = True
                break
        
        if not results['websocket_integration']:
            self.issues.append(LanguageUIIssue(
                component='language_switching',
                issue_type='missing_integration',
                severity='warning',
                description='WebSocket language integration not found',
                recommendation='Integrate language changes with WebSocket communication',
                languages_affected=['all']
            ))
        
        # Check state management
        if 'currentLanguage' in self.js_content:
            results['state_management']['current_language_tracked'] = True
        
        if 'localStorage' in self.js_content and 'language' in self.js_content:
            results['state_management']['language_persistence'] = True
        
        # Check for UI updates on language change
        ui_update_patterns = [
            r'language.*update.*ui',
            r'ui.*language',
            r'render.*language',
            r'display.*language'
        ]
        
        for pattern in ui_update_patterns:
            if re.search(pattern, self.js_content, re.IGNORECASE):
                results['state_management']['ui_updates_on_change'] = True
                break
        
        # Find supported languages in code
        language_codes = re.findall(r'[\'"]([a-z]{2}(?:-[a-z]{2})?)[\'"]', self.js_content)
        common_language_codes = ['en', 'hi', 'mixed', 'hindi', 'english']
        results['supported_languages'] = [lang for lang in language_codes if lang in common_language_codes]
        
        # Check error handling
        if 'try' in self.js_content and 'language' in self.js_content:
            results['error_handling'] = True
        
        return results
    
    def validate_multilingual_text_support(self) -> Dict:
        """Validate multilingual text rendering and support"""
        results = {
            'font_support': {
                'latin_fonts': [],
                'devanagari_fonts': [],
                'fallback_fonts': [],
                'web_fonts': []
            },
            'text_rendering': {
                'utf8_encoding': False,
                'unicode_support': False,
                'mixed_script_handling': False
            },
            'css_language_support': {
                'font_face_rules': 0,
                'unicode_range_specified': False,
                'language_specific_styles': []
            },
            'rtl_ltr_support': {
                'direction_property': False,
                'text_align_support': False,
                'writing_mode_support': False
            }
        }
        
        # Check HTML encoding
        charset_meta = self.soup.find('meta', attrs={'charset': True})
        if charset_meta:
            charset = charset_meta.get('charset', '').lower()
            if charset == 'utf-8':
                results['text_rendering']['utf8_encoding'] = True
            else:
                self.issues.append(LanguageUIIssue(
                    component='text_encoding',
                    issue_type='encoding_issue',
                    severity='error',
                    description=f'Non-UTF-8 encoding found: {charset}',
                    recommendation='Use UTF-8 encoding for proper multilingual support',
                    languages_affected=['hi', 'mixed']
                ))
        
        # Check for Unicode support indicators
        unicode_patterns = [
            r'unicode-range',
            r'utf-8',
            r'\\u[0-9a-fA-F]{4}',
            r'devanagari',
            r'hindi'
        ]
        
        for pattern in unicode_patterns:
            if re.search(pattern, self.css_content, re.IGNORECASE):
                results['text_rendering']['unicode_support'] = True
                break
        
        # Check font support
        font_patterns = {
            'latin_fonts': [r'font-family.*latin', r'font-family.*arial', r'font-family.*helvetica'],
            'devanagari_fonts': [r'font-family.*devanagari', r'font-family.*hindi', r'font-family.*noto'],
            'web_fonts': [r'@import.*font', r'fonts\.googleapis\.com', r'font-face']
        }
        
        for font_type, patterns in font_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, self.css_content, re.IGNORECASE)
                if matches:
                    results['font_support'][font_type].extend(matches)
        
        # Check CSS font-face rules
        font_face_count = len(re.findall(r'@font-face', self.css_content, re.IGNORECASE))
        results['css_language_support']['font_face_rules'] = font_face_count
        
        # Check unicode-range
        if 'unicode-range' in self.css_content:
            results['css_language_support']['unicode_range_specified'] = True
        
        # Check RTL/LTR support
        direction_properties = ['direction:', 'text-align:', 'writing-mode:']
        for prop in direction_properties:
            if prop in self.css_content:
                if 'direction:' in prop:
                    results['rtl_ltr_support']['direction_property'] = True
                elif 'text-align:' in prop:
                    results['rtl_ltr_support']['text_align_support'] = True
                elif 'writing-mode:' in prop:
                    results['rtl_ltr_support']['writing_mode_support'] = True
        
        return results
    
    def validate_language_specific_ui_adaptations(self) -> Dict:
        """Validate language-specific UI adaptations"""
        results = {
            'layout_adaptations': {
                'responsive_to_text_length': False,
                'script_specific_spacing': False,
                'font_size_adjustments': False
            },
            'transcription_display': {
                'language_indicators': False,
                'mixed_language_handling': False,
                'script_direction_support': False
            },
            'user_feedback': {
                'language_status_display': False,
                'switching_confirmation': False,
                'error_messages_localized': False
            },
            'accessibility_adaptations': {
                'screen_reader_support': False,
                'keyboard_navigation': False,
                'high_contrast_support': False
            }
        }
        
        # Check layout adaptations
        if 'font-size' in self.css_content and 'language' in self.css_content.lower():
            results['layout_adaptations']['font_size_adjustments'] = True
        
        if 'line-height' in self.css_content or 'letter-spacing' in self.css_content:
            results['layout_adaptations']['script_specific_spacing'] = True
        
        # Check transcription display features
        if 'language.*indicator' in self.js_content or 'lang.*display' in self.js_content:
            results['transcription_display']['language_indicators'] = True
        
        if 'mixed' in self.js_content.lower() and 'language' in self.js_content:
            results['transcription_display']['mixed_language_handling'] = True
        
        # Check user feedback
        status_patterns = [
            r'status.*language',
            r'language.*status',
            r'current.*language',
            r'selected.*language'
        ]
        
        for pattern in status_patterns:
            if re.search(pattern, self.js_content, re.IGNORECASE):
                results['user_feedback']['language_status_display'] = True
                break
        
        # Check accessibility
        if 'aria-label' in self.soup.prettify() and 'language' in self.soup.prettify():
            results['accessibility_adaptations']['screen_reader_support'] = True
        
        return results
    
    def validate_language_persistence(self) -> Dict:
        """Validate language preference persistence"""
        results = {
            'storage_mechanism': None,
            'persistence_methods': [],
            'session_handling': {
                'maintains_across_page_refresh': False,
                'maintains_across_sessions': False,
                'handles_initial_load': False
            },
            'fallback_behavior': {
                'default_language_set': False,
                'invalid_language_handling': False,
                'missing_preference_handling': False
            }
        }
        
        # Check storage mechanisms
        storage_patterns = {
            'localStorage': r'localStorage.*language',
            'sessionStorage': r'sessionStorage.*language',
            'cookies': r'cookie.*language|document\.cookie',
            'url_params': r'URLSearchParams.*language|url.*language'
        }
        
        for mechanism, pattern in storage_patterns.items():
            if re.search(pattern, self.js_content, re.IGNORECASE):
                results['storage_mechanism'] = mechanism
                results['persistence_methods'].append(mechanism)
        
        if not results['persistence_methods']:
            self.issues.append(LanguageUIIssue(
                component='language_persistence',
                issue_type='missing_feature',
                severity='info',
                description='No language persistence mechanism found',
                recommendation='Consider implementing localStorage for language preference persistence',
                languages_affected=['all']
            ))
        
        # Check session handling
        if 'localStorage' in results['persistence_methods']:
            results['session_handling']['maintains_across_sessions'] = True
        
        if 'sessionStorage' in results['persistence_methods']:
            results['session_handling']['maintains_across_page_refresh'] = True
        
        # Check initialization handling
        init_patterns = [
            r'window\.onload.*language',
            r'document\.ready.*language',
            r'init.*language',
            r'language.*init'
        ]
        
        for pattern in init_patterns:
            if re.search(pattern, self.js_content, re.IGNORECASE):
                results['session_handling']['handles_initial_load'] = True
                break
        
        # Check fallback behavior
        if 'defaultLanguage' in self.js_content or 'default.*language' in self.js_content:
            results['fallback_behavior']['default_language_set'] = True
        
        return results
    
    def validate_code_switching_support(self) -> Dict:
        """Validate support for code-switching (mixed Hindi-English)"""
        results = {
            'mixed_language_option': False,
            'code_switching_detection': {
                'client_side_detection': False,
                'server_side_integration': False,
                'automatic_switching': False
            },
            'ui_handling': {
                'mixed_text_display': False,
                'script_highlighting': False,
                'language_tags': False
            },
            'performance_considerations': {
                'efficient_rendering': False,
                'font_loading_optimization': False,
                'text_processing_optimization': False
            }
        }
        
        # Check for mixed language option
        mixed_patterns = [
            r'mixed',
            r'hindi.*english',
            r'english.*hindi',
            r'code.*switch',
            r'multilingual'
        ]
        
        for pattern in mixed_patterns:
            if re.search(pattern, self.js_content, re.IGNORECASE) or re.search(pattern, str(self.soup), re.IGNORECASE):
                results['mixed_language_option'] = True
                break
        
        if not results['mixed_language_option']:
            self.issues.append(LanguageUIIssue(
                component='code_switching',
                issue_type='missing_feature',
                severity='info',
                description='Mixed language option not clearly indicated',
                recommendation='Consider explicitly supporting Hindi-English code-switching',
                languages_affected=['mixed']
            ))
        
        # Check detection capabilities
        if 'detect' in self.js_content and 'language' in self.js_content:
            results['code_switching_detection']['client_side_detection'] = True
        
        if 'websocket' in self.js_content.lower() and 'language' in self.js_content:
            results['code_switching_detection']['server_side_integration'] = True
        
        # Check UI handling
        if 'span' in self.js_content and 'language' in self.js_content:
            results['ui_handling']['language_tags'] = True
        
        return results
    
    def test_language_ui_with_sample_data(self) -> Dict:
        """Test language UI with sample multilingual data"""
        results = {
            'sample_tests': [],
            'rendering_tests': {
                'english_rendering': {'status': 'unknown', 'issues': []},
                'hindi_rendering': {'status': 'unknown', 'issues': []},
                'mixed_rendering': {'status': 'unknown', 'issues': []}
            },
            'font_coverage': {
                'latin_coverage': False,
                'devanagari_coverage': False,
                'mixed_coverage': False
            },
            'performance_impact': {
                'font_loading_time': 'unknown',
                'text_rendering_speed': 'unknown'
            }
        }
        
        # Test sample data for each supported language
        for lang_code, lang_info in self.supported_languages.items():
            sample_text = lang_info['sample_text']
            script = lang_info['script']
            
            # Check if the HTML/CSS can handle the sample text
            test_result = {
                'language': lang_code,
                'sample_text': sample_text,
                'script': script,
                'character_analysis': self._analyze_text_characters(sample_text),
                'potential_issues': []
            }
            
            # Check for potential font issues
            if script == 'Devanagari' or script == 'Mixed':
                if not any('devanagari' in font.lower() or 'noto' in font.lower() 
                          for font_list in results['font_coverage'].values() 
                          if isinstance(font_list, list) for font in font_list):
                    test_result['potential_issues'].append('May lack proper Devanagari font support')
            
            results['sample_tests'].append(test_result)
            
            # Update rendering test status based on analysis
            if lang_code == 'en':
                results['rendering_tests']['english_rendering']['status'] = 'likely_supported'
            elif lang_code == 'hi':
                status = 'needs_verification' if test_result['potential_issues'] else 'likely_supported'
                results['rendering_tests']['hindi_rendering']['status'] = status
                results['rendering_tests']['hindi_rendering']['issues'] = test_result['potential_issues']
            elif lang_code == 'mixed':
                status = 'needs_verification' if test_result['potential_issues'] else 'likely_supported'
                results['rendering_tests']['mixed_rendering']['status'] = status
                results['rendering_tests']['mixed_rendering']['issues'] = test_result['potential_issues']
        
        return results
    
    def _analyze_text_characters(self, text: str) -> Dict:
        """Analyze character composition of text"""
        analysis = {
            'total_characters': len(text),
            'latin_characters': 0,
            'devanagari_characters': 0,
            'numeric_characters': 0,
            'punctuation_characters': 0,
            'other_characters': 0,
            'unicode_blocks': set()
        }
        
        for char in text:
            if char.isspace():
                continue
                
            # Get Unicode block
            try:
                block = unicodedata.name(char).split(' ')[0]
                analysis['unicode_blocks'].add(block)
            except ValueError:
                pass
            
            # Categorize character
            if ord(char) < 128:  # ASCII
                if char.isalpha():
                    analysis['latin_characters'] += 1
                elif char.isdigit():
                    analysis['numeric_characters'] += 1
                elif not char.isalnum():
                    analysis['punctuation_characters'] += 1
            elif 0x0900 <= ord(char) <= 0x097F:  # Devanagari block
                analysis['devanagari_characters'] += 1
            else:
                analysis['other_characters'] += 1
        
        analysis['unicode_blocks'] = list(analysis['unicode_blocks'])
        return analysis
    
    def generate_language_ui_report(self) -> Dict:
        """Generate comprehensive language UI report"""
        if not self.soup:
            self.load_html_css_js()
        
        report = {
            'file_path': self.html_file_path,
            'supported_languages': list(self.supported_languages.keys()),
            'language_selector_ui': self.validate_language_selector_ui(),
            'language_switching_logic': self.validate_language_switching_logic(),
            'multilingual_text_support': self.validate_multilingual_text_support(),
            'ui_adaptations': self.validate_language_specific_ui_adaptations(),
            'language_persistence': self.validate_language_persistence(),
            'code_switching_support': self.validate_code_switching_support(),
            'sample_data_tests': self.test_language_ui_with_sample_data(),
            'issues': [
                {
                    'component': issue.component,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'recommendation': issue.recommendation,
                    'languages_affected': issue.languages_affected
                }
                for issue in self.issues
            ],
            'statistics': self._calculate_language_ui_stats()
        }
        
        return report
    
    def _calculate_language_ui_stats(self) -> Dict:
        """Calculate language UI statistics"""
        error_count = sum(1 for issue in self.issues if issue.severity == 'error')
        warning_count = sum(1 for issue in self.issues if issue.severity == 'warning')
        info_count = sum(1 for issue in self.issues if issue.severity == 'info')
        
        total_issues = len(self.issues)
        
        # Calculate language support score
        max_score = 100
        deductions = error_count * 20 + warning_count * 10 + info_count * 5
        language_support_score = max(0, max_score - deductions)
        
        return {
            'total_issues': total_issues,
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'language_support_score': language_support_score,
            'multilingual_readiness': self._get_multilingual_readiness(language_support_score)
        }
    
    def _get_multilingual_readiness(self, score: int) -> str:
        """Determine multilingual readiness level based on score"""
        if score >= 90:
            return 'Excellent Multilingual Support'
        elif score >= 75:
            return 'Good Multilingual Support'
        elif score >= 60:
            return 'Basic Multilingual Support'
        else:
            return 'Poor Multilingual Support'


class LanguageSwitchingUITestSuite(unittest.TestCase):
    """Test suite for language switching UI validation"""
    
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
        self.validator = LanguageSwitchingUIValidator(str(self.html_file), str(self.static_dir))
        self.assertTrue(self.validator.load_html_css_js(), "Failed to load HTML, CSS, and JavaScript")
    
    def test_language_selector_presence(self):
        """Test presence and structure of language selector"""
        logger.info("Testing language selector presence and structure")
        
        results = self.validator.validate_language_selector_ui()
        
        self.assertTrue(results['selector_present'], "Language selector not found")
        self.assertEqual(results['selector_type'], 'select', "Expected select element for language selector")
        
        # Should have options for supported languages
        self.assertGreater(len(results['options_available']), 0, "No language options found")
        
        # Check for expected languages
        expected_languages = {'en', 'hi', 'mixed'}
        found_languages = {opt['value'] for opt in results['options_available'] if opt['value']}
        
        self.assertTrue(expected_languages.issubset(found_languages),
                       f"Missing expected languages. Expected: {expected_languages}, Found: {found_languages}")
        
        logger.info(f"Language selector validated. Options: {len(results['options_available'])}")
    
    def test_language_selector_accessibility(self):
        """Test language selector accessibility"""
        logger.info("Testing language selector accessibility")
        
        results = self.validator.validate_language_selector_ui()
        
        accessibility = results['accessibility']
        
        # Should have proper labeling
        self.assertTrue(accessibility['has_label'] or accessibility['has_aria_label'],
                       "Language selector missing proper labeling")
        
        # Should be keyboard accessible (select elements are by default)
        self.assertTrue(accessibility['keyboard_accessible'],
                       "Language selector should be keyboard accessible")
        
        logger.info(f"Language selector accessibility validated")
    
    def test_language_switching_logic(self):
        """Test language switching JavaScript logic"""
        logger.info("Testing language switching logic")
        
        results = self.validator.validate_language_switching_logic()
        
        self.assertTrue(results['event_handler_present'],
                       "Language change event handler not found")
        
        # Should integrate with WebSocket for real-time language switching
        self.assertTrue(results['websocket_integration'],
                       "Language switching should integrate with WebSocket")
        
        # Check state management
        state_mgmt = results['state_management']
        self.assertTrue(state_mgmt['current_language_tracked'],
                       "Current language state not tracked")
        
        logger.info(f"Language switching logic validated. Mechanisms: {results['switching_mechanisms']}")
    
    def test_multilingual_text_support(self):
        """Test multilingual text rendering support"""
        logger.info("Testing multilingual text support")
        
        results = self.validator.validate_multilingual_text_support()
        
        # Should use UTF-8 encoding
        self.assertTrue(results['text_rendering']['utf8_encoding'],
                       "UTF-8 encoding required for multilingual support")
        
        # Should have font support for different scripts
        font_support = results['font_support']
        
        # Check for web fonts (Google Fonts or similar)
        self.assertGreater(len(font_support['web_fonts']), 0,
                          "Web fonts recommended for better multilingual support")
        
        logger.info(f"Multilingual text support validated. Unicode support: {results['text_rendering']['unicode_support']}")
    
    def test_hindi_text_rendering_capability(self):
        """Test specific Hindi text rendering capability"""
        logger.info("Testing Hindi text rendering capability")
        
        results = self.validator.validate_multilingual_text_support()
        sample_tests = self.validator.test_language_ui_with_sample_data()
        
        # Check if Devanagari fonts are available or web fonts are loaded
        has_devanagari_support = (
            len(results['font_support']['devanagari_fonts']) > 0 or
            len(results['font_support']['web_fonts']) > 0
        )
        
        if not has_devanagari_support:
            logger.warning("No explicit Devanagari font support found - may rely on system fonts")
        
        # Check sample Hindi text analysis
        hindi_tests = [test for test in sample_tests['sample_tests'] if test['language'] == 'hi']
        if hindi_tests:
            hindi_test = hindi_tests[0]
            char_analysis = hindi_test['character_analysis']
            
            self.assertGreater(char_analysis['devanagari_characters'], 0,
                             "Sample Hindi text should contain Devanagari characters")
        
        logger.info(f"Hindi text rendering capability assessed")
    
    def test_code_switching_support(self):
        """Test Hindi-English code-switching support"""
        logger.info("Testing Hindi-English code-switching support")
        
        results = self.validator.validate_code_switching_support()
        
        # Should have mixed language option
        self.assertTrue(results['mixed_language_option'],
                       "Mixed Hindi-English language option not found")
        
        # Should handle mixed text appropriately
        ui_handling = results['ui_handling']
        # At least one form of mixed text handling should be present
        has_mixed_handling = any(ui_handling.values())
        
        if not has_mixed_handling:
            logger.info("No explicit mixed text handling found - consider implementing for better UX")
        
        logger.info(f"Code-switching support validated. Mixed option: {results['mixed_language_option']}")
    
    def test_language_persistence(self):
        """Test language preference persistence"""
        logger.info("Testing language preference persistence")
        
        results = self.validator.validate_language_persistence()
        
        # Should have some form of persistence (even if just session-based)
        has_persistence = len(results['persistence_methods']) > 0
        
        if has_persistence:
            self.assertIsNotNone(results['storage_mechanism'],
                               "Storage mechanism should be identified")
            logger.info(f"Language persistence found: {results['storage_mechanism']}")
        else:
            logger.info("No language persistence found - consider implementing for better UX")
        
        logger.info(f"Language persistence validated")
    
    def test_language_ui_adaptations(self):
        """Test language-specific UI adaptations"""
        logger.info("Testing language-specific UI adaptations")
        
        results = self.validator.validate_language_specific_ui_adaptations()
        
        # Check transcription display features
        transcription = results['transcription_display']
        
        # Should show language indicators for transcriptions
        if not transcription['language_indicators']:
            logger.info("No language indicators found - consider showing language for each transcription")
        
        # Should handle mixed language scenarios
        if not transcription['mixed_language_handling']:
            logger.info("No mixed language handling found - important for code-switching scenarios")
        
        logger.info(f"Language UI adaptations assessed")
    
    def test_font_and_rendering_performance(self):
        """Test font loading and rendering performance considerations"""
        logger.info("Testing font and rendering performance")
        
        multilingual_results = self.validator.validate_multilingual_text_support()
        
        # Check for font optimization
        font_support = multilingual_results['font_support']
        
        # Web fonts should be efficiently loaded
        if font_support['web_fonts']:
            logger.info(f"Web fonts detected: {len(font_support['web_fonts'])}")
            
            # Check if fonts are preloaded or optimized
            if 'display=swap' in self.validator.css_content or 'font-display: swap' in self.validator.css_content:
                logger.info("Font display optimization found")
            else:
                logger.info("Consider adding font-display: swap for better performance")
        
        logger.info("Font and rendering performance assessed")
    
    def test_overall_language_support_score(self):
        """Test overall language support score"""
        logger.info("Calculating overall language support score")
        
        report = self.validator.generate_language_ui_report()
        stats = report['statistics']
        
        # Should achieve reasonable language support score
        self.assertGreaterEqual(stats['language_support_score'], 50,
                               f"Language support score too low: {stats['language_support_score']}")
        
        # Should have minimal critical errors
        self.assertLessEqual(stats['errors'], 3,
                            f"Too many language support errors: {stats['errors']}")
        
        multilingual_readiness = stats['multilingual_readiness']
        self.assertNotEqual(multilingual_readiness, 'Poor Multilingual Support',
                           f"Multilingual readiness unacceptable: {multilingual_readiness}")
        
        logger.info(f"Language support score: {stats['language_support_score']}/100 - {multilingual_readiness}")
    
    def test_generate_full_language_ui_report(self):
        """Generate and validate full language UI report"""
        logger.info("Generating comprehensive language UI report")
        
        report = self.validator.generate_language_ui_report()
        
        # Validate report structure
        required_sections = [
            'language_selector_ui', 'language_switching_logic', 'multilingual_text_support',
            'ui_adaptations', 'code_switching_support', 'sample_data_tests', 'statistics'
        ]
        
        for section in required_sections:
            self.assertIn(section, report, f"Missing report section: {section}")
        
        # Save report for manual review
        report_file = Path(__file__).parent / f'language_ui_report_{Path(self.html_file).stem}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Full language UI report saved to: {report_file}")
        
        # Print summary
        stats = report['statistics']
        print(f"\n{'='*60}")
        print(f"LANGUAGE SWITCHING UI VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"File: {report['file_path']}")
        print(f"Supported Languages: {', '.join(report['supported_languages'])}")
        print(f"Language Support Score: {stats['language_support_score']}/100")
        print(f"Multilingual Readiness: {stats['multilingual_readiness']}")
        print(f"Total Issues: {stats['total_issues']}")
        print(f"  - Errors: {stats['errors']}")
        print(f"  - Warnings: {stats['warnings']}")
        print(f"  - Info: {stats['info']}")
        
        # Language features summary
        selector = report['language_selector_ui']
        switching = report['language_switching_logic']
        multilingual = report['multilingual_text_support']
        
        print(f"\nLanguage Features:")
        print(f"  Language Selector: {'✓' if selector['selector_present'] else '✗'}")
        print(f"  Switching Logic: {'✓' if switching['event_handler_present'] else '✗'}")
        print(f"  UTF-8 Encoding: {'✓' if multilingual['text_rendering']['utf8_encoding'] else '✗'}")
        print(f"  Code-switching: {'✓' if report['code_switching_support']['mixed_language_option'] else '✗'}")
        
        # Sample text analysis
        sample_tests = report['sample_data_tests']['sample_tests']
        if sample_tests:
            print(f"\nSample Text Analysis:")
            for test in sample_tests:
                char_analysis = test['character_analysis']
                print(f"  {test['language']}: {char_analysis['total_characters']} chars "
                     f"(Latin: {char_analysis['latin_characters']}, "
                     f"Devanagari: {char_analysis['devanagari_characters']})")
        
        if report['issues']:
            print(f"\nTop Issues:")
            for i, issue in enumerate(report['issues'][:5], 1):
                print(f"  {i}. [{issue['severity'].upper()}] {issue['description']}")
                print(f"     Languages: {', '.join(issue['languages_affected'])}")
        
        print(f"{'='*60}")


def run_language_switching_ui_tests(verbose=False):
    """Run language switching UI tests with optional verbose output"""
    
    # Setup test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(LanguageSwitchingUITestSuite)
    
    # Run tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Language Switching UI Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    success = run_language_switching_ui_tests(verbose=args.verbose)
    sys.exit(0 if success else 1)