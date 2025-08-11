#!/usr/bin/env python3
"""
Frontend HTML Structure and Accessibility Test Suite

This module provides comprehensive testing for HTML structure validation,
semantic markup, and accessibility compliance for the live transcription website.

Features:
- HTML5 semantic structure validation
- ARIA labels and roles verification
- Form accessibility testing
- Heading hierarchy validation
- Image alt text checking
- Color contrast validation
- Keyboard navigation support
- Screen reader compatibility

Usage:
    python -m unittest test_frontend_html_accessibility.HTMLAccessibilityTestSuite
    python test_frontend_html_accessibility.py --verbose
"""

import unittest
import os
import re
import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AccessibilityIssue:
    """Data class for accessibility issues"""
    element: str
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    recommendation: str
    wcag_guideline: Optional[str] = None

class HTMLAccessibilityValidator:
    """Comprehensive HTML accessibility validator"""
    
    def __init__(self, html_file_path: str):
        self.html_file_path = html_file_path
        self.soup = None
        self.issues: List[AccessibilityIssue] = []
        self.stats = {
            'errors': 0,
            'warnings': 0,
            'info': 0,
            'total_elements': 0,
            'accessible_elements': 0
        }
        
    def load_html(self) -> bool:
        """Load and parse HTML file"""
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.soup = BeautifulSoup(content, 'html.parser')
                return True
        except Exception as e:
            logger.error(f"Error loading HTML file: {e}")
            return False
    
    def validate_html5_structure(self) -> Dict:
        """Validate HTML5 semantic structure"""
        results = {
            'has_doctype': False,
            'has_html_tag': False,
            'has_head': False,
            'has_body': False,
            'has_title': False,
            'has_lang_attribute': False,
            'has_viewport': False,
            'has_charset': False,
            'semantic_elements': [],
            'issues': []
        }
        
        # Check DOCTYPE
        if self.soup.contents and str(self.soup.contents[0]).strip().lower().startswith('<!doctype html'):
            results['has_doctype'] = True
        else:
            self.issues.append(AccessibilityIssue(
                element='document',
                issue_type='html5_structure',
                severity='error',
                description='Missing HTML5 DOCTYPE declaration',
                recommendation='Add <!DOCTYPE html> at the beginning of the document',
                wcag_guideline='4.1.1'
            ))
        
        # Check html tag with lang attribute
        html_tag = self.soup.find('html')
        if html_tag:
            results['has_html_tag'] = True
            if html_tag.get('lang'):
                results['has_lang_attribute'] = True
            else:
                self.issues.append(AccessibilityIssue(
                    element='html',
                    issue_type='language',
                    severity='error',
                    description='Missing lang attribute on html element',
                    recommendation='Add lang="en" or appropriate language code to <html> tag',
                    wcag_guideline='3.1.1'
                ))
        
        # Check head section
        head = self.soup.find('head')
        if head:
            results['has_head'] = True
            
            # Check title
            title = head.find('title')
            if title and title.string:
                results['has_title'] = True
            else:
                self.issues.append(AccessibilityIssue(
                    element='head',
                    issue_type='title',
                    severity='error',
                    description='Missing or empty page title',
                    recommendation='Add descriptive <title> tag in head section',
                    wcag_guideline='2.4.2'
                ))
            
            # Check charset
            charset_meta = head.find('meta', attrs={'charset': True}) or head.find('meta', attrs={'http-equiv': 'Content-Type'})
            if charset_meta:
                results['has_charset'] = True
            else:
                self.issues.append(AccessibilityIssue(
                    element='head',
                    issue_type='charset',
                    severity='warning',
                    description='Missing charset declaration',
                    recommendation='Add <meta charset="UTF-8"> in head section'
                ))
            
            # Check viewport
            viewport_meta = head.find('meta', attrs={'name': 'viewport'})
            if viewport_meta:
                results['has_viewport'] = True
            else:
                self.issues.append(AccessibilityIssue(
                    element='head',
                    issue_type='viewport',
                    severity='warning',
                    description='Missing viewport meta tag',
                    recommendation='Add <meta name="viewport" content="width=device-width, initial-scale=1">'
                ))
        
        # Check body
        body = self.soup.find('body')
        if body:
            results['has_body'] = True
        
        # Check semantic HTML5 elements
        semantic_elements = ['header', 'nav', 'main', 'section', 'article', 'aside', 'footer']
        for element in semantic_elements:
            found_elements = self.soup.find_all(element)
            if found_elements:
                results['semantic_elements'].append({
                    'element': element,
                    'count': len(found_elements)
                })
        
        return results
    
    def validate_heading_hierarchy(self) -> Dict:
        """Validate heading hierarchy (h1-h6)"""
        headings = self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        results = {
            'headings': [],
            'has_h1': False,
            'multiple_h1': False,
            'hierarchy_issues': [],
            'empty_headings': []
        }
        
        heading_levels = []
        h1_count = 0
        
        for heading in headings:
            level = int(heading.name[1])
            text = heading.get_text(strip=True)
            
            results['headings'].append({
                'level': level,
                'text': text,
                'element': str(heading)
            })
            
            heading_levels.append(level)
            
            if level == 1:
                h1_count += 1
            
            # Check for empty headings
            if not text:
                results['empty_headings'].append(heading.name)
                self.issues.append(AccessibilityIssue(
                    element=heading.name,
                    issue_type='heading',
                    severity='error',
                    description=f'Empty {heading.name} element',
                    recommendation=f'Provide descriptive text for {heading.name} element',
                    wcag_guideline='2.4.6'
                ))
        
        results['has_h1'] = h1_count > 0
        results['multiple_h1'] = h1_count > 1
        
        if not results['has_h1']:
            self.issues.append(AccessibilityIssue(
                element='document',
                issue_type='heading',
                severity='error',
                description='Missing h1 element',
                recommendation='Add a main h1 heading to the page',
                wcag_guideline='2.4.6'
            ))
        
        if results['multiple_h1']:
            self.issues.append(AccessibilityIssue(
                element='h1',
                issue_type='heading',
                severity='warning',
                description='Multiple h1 elements found',
                recommendation='Use only one h1 element per page',
                wcag_guideline='2.4.6'
            ))
        
        # Check heading hierarchy
        for i in range(1, len(heading_levels)):
            current = heading_levels[i]
            previous = heading_levels[i-1]
            if current > previous + 1:
                results['hierarchy_issues'].append(f'Skipped from h{previous} to h{current}')
                self.issues.append(AccessibilityIssue(
                    element=f'h{current}',
                    issue_type='heading',
                    severity='warning',
                    description=f'Heading hierarchy skip from h{previous} to h{current}',
                    recommendation='Use sequential heading levels',
                    wcag_guideline='2.4.6'
                ))
        
        return results
    
    def validate_aria_labels(self) -> Dict:
        """Validate ARIA labels and roles"""
        results = {
            'elements_with_aria': [],
            'missing_aria_labels': [],
            'invalid_aria_roles': [],
            'aria_describedby_issues': []
        }
        
        # Find elements with ARIA attributes
        aria_elements = self.soup.find_all(attrs={'aria-label': True}) + \
                      self.soup.find_all(attrs={'aria-labelledby': True}) + \
                      self.soup.find_all(attrs={'role': True}) + \
                      self.soup.find_all(attrs={'aria-describedby': True})
        
        valid_roles = {
            'alert', 'alertdialog', 'application', 'article', 'banner', 'button',
            'cell', 'checkbox', 'columnheader', 'combobox', 'complementary',
            'contentinfo', 'definition', 'dialog', 'directory', 'document',
            'feed', 'figure', 'form', 'grid', 'gridcell', 'group', 'heading',
            'img', 'link', 'list', 'listbox', 'listitem', 'log', 'main',
            'marquee', 'math', 'menu', 'menubar', 'menuitem', 'menuitemcheckbox',
            'menuitemradio', 'navigation', 'none', 'note', 'option', 'presentation',
            'progressbar', 'radio', 'radiogroup', 'region', 'row', 'rowgroup',
            'rowheader', 'scrollbar', 'search', 'searchbox', 'separator',
            'slider', 'spinbutton', 'status', 'switch', 'tab', 'table',
            'tablist', 'tabpanel', 'term', 'textbox', 'timer', 'toolbar',
            'tooltip', 'tree', 'treegrid', 'treeitem'
        }
        
        for element in aria_elements:
            element_info = {
                'tag': element.name,
                'aria_attributes': {}
            }
            
            # Check ARIA role
            role = element.get('role')
            if role:
                element_info['aria_attributes']['role'] = role
                if role not in valid_roles:
                    results['invalid_aria_roles'].append({
                        'element': element.name,
                        'role': role
                    })
                    self.issues.append(AccessibilityIssue(
                        element=element.name,
                        issue_type='aria',
                        severity='error',
                        description=f'Invalid ARIA role: {role}',
                        recommendation=f'Use a valid ARIA role instead of "{role}"',
                        wcag_guideline='4.1.2'
                    ))
            
            # Check ARIA labels
            aria_label = element.get('aria-label')
            aria_labelledby = element.get('aria-labelledby')
            aria_describedby = element.get('aria-describedby')
            
            if aria_label:
                element_info['aria_attributes']['aria-label'] = aria_label
            if aria_labelledby:
                element_info['aria_attributes']['aria-labelledby'] = aria_labelledby
            if aria_describedby:
                element_info['aria_attributes']['aria-describedby'] = aria_describedby
            
            results['elements_with_aria'].append(element_info)
        
        # Check for interactive elements without labels
        interactive_elements = self.soup.find_all(['button', 'input', 'select', 'textarea', 'a'])
        for element in interactive_elements:
            has_label = (
                element.get('aria-label') or 
                element.get('aria-labelledby') or 
                element.get('title') or
                (element.name == 'input' and element.get('placeholder')) or
                element.get_text(strip=True)
            )
            
            if not has_label:
                results['missing_aria_labels'].append(element.name)
                self.issues.append(AccessibilityIssue(
                    element=element.name,
                    issue_type='aria',
                    severity='error',
                    description=f'{element.name} element missing accessible label',
                    recommendation=f'Add aria-label, aria-labelledby, or visible text to {element.name}',
                    wcag_guideline='4.1.2'
                ))
        
        return results
    
    def validate_images(self) -> Dict:
        """Validate image accessibility"""
        images = self.soup.find_all('img')
        results = {
            'total_images': len(images),
            'images_with_alt': 0,
            'images_without_alt': [],
            'decorative_images': [],
            'informative_images': []
        }
        
        for img in images:
            alt = img.get('alt')
            src = img.get('src', 'unknown')
            
            if alt is not None:
                results['images_with_alt'] += 1
                if alt.strip() == '':
                    results['decorative_images'].append(src)
                else:
                    results['informative_images'].append({
                        'src': src,
                        'alt': alt
                    })
            else:
                results['images_without_alt'].append(src)
                self.issues.append(AccessibilityIssue(
                    element='img',
                    issue_type='images',
                    severity='error',
                    description=f'Image missing alt attribute: {src}',
                    recommendation='Add alt attribute with descriptive text or alt="" for decorative images',
                    wcag_guideline='1.1.1'
                ))
        
        return results
    
    def validate_forms(self) -> Dict:
        """Validate form accessibility"""
        forms = self.soup.find_all('form')
        inputs = self.soup.find_all(['input', 'select', 'textarea'])
        
        results = {
            'total_forms': len(forms),
            'total_inputs': len(inputs),
            'inputs_with_labels': 0,
            'inputs_without_labels': [],
            'fieldsets': [],
            'form_errors': []
        }
        
        # Check form inputs for labels
        for input_elem in inputs:
            input_id = input_elem.get('id')
            input_type = input_elem.get('type', 'text')
            input_name = input_elem.get('name', 'unknown')
            
            # Skip hidden inputs
            if input_type == 'hidden':
                continue
            
            has_label = False
            
            # Check for associated label
            if input_id:
                label = self.soup.find('label', attrs={'for': input_id})
                if label:
                    has_label = True
            
            # Check for wrapper label
            parent_label = input_elem.find_parent('label')
            if parent_label:
                has_label = True
            
            # Check for ARIA labels
            if input_elem.get('aria-label') or input_elem.get('aria-labelledby'):
                has_label = True
            
            if has_label:
                results['inputs_with_labels'] += 1
            else:
                results['inputs_without_labels'].append({
                    'type': input_type,
                    'name': input_name,
                    'id': input_id
                })
                self.issues.append(AccessibilityIssue(
                    element=f'input[type="{input_type}"]',
                    issue_type='forms',
                    severity='error',
                    description=f'Form input missing label: {input_name}',
                    recommendation='Associate input with label element or add aria-label',
                    wcag_guideline='1.3.1'
                ))
        
        # Check for fieldsets
        fieldsets = self.soup.find_all('fieldset')
        for fieldset in fieldsets:
            legend = fieldset.find('legend')
            results['fieldsets'].append({
                'has_legend': legend is not None,
                'legend_text': legend.get_text(strip=True) if legend else None
            })
            
            if not legend:
                self.issues.append(AccessibilityIssue(
                    element='fieldset',
                    issue_type='forms',
                    severity='warning',
                    description='Fieldset missing legend element',
                    recommendation='Add <legend> element to describe the fieldset',
                    wcag_guideline='1.3.1'
                ))
        
        return results
    
    def validate_color_contrast(self) -> Dict:
        """Basic color contrast validation (requires CSS analysis)"""
        results = {
            'color_properties_found': [],
            'potential_issues': [],
            'recommendations': []
        }
        
        # Extract inline styles
        elements_with_style = self.soup.find_all(attrs={'style': True})
        
        for element in elements_with_style:
            style = element.get('style')
            
            # Simple regex to find color values
            color_matches = re.findall(r'color\s*:\s*([^;]+)', style, re.IGNORECASE)
            bg_matches = re.findall(r'background(?:-color)?\s*:\s*([^;]+)', style, re.IGNORECASE)
            
            if color_matches or bg_matches:
                results['color_properties_found'].append({
                    'element': element.name,
                    'colors': color_matches,
                    'backgrounds': bg_matches
                })
        
        # Check for CSS variables used for colors
        css_content = ""
        style_tags = self.soup.find_all('style')
        for style in style_tags:
            css_content += style.string or ""
        
        if css_content:
            # Look for CSS color properties
            color_vars = re.findall(r'--[\w-]+\s*:\s*#[0-9a-fA-F]{6}|--[\w-]+\s*:\s*rgb\([^)]+\)', css_content)
            if color_vars:
                results['potential_issues'].append('CSS custom properties found - manual color contrast validation recommended')
        
        # Add general recommendations
        results['recommendations'] = [
            'Ensure text has sufficient contrast ratio (4.5:1 for normal text, 3:1 for large text)',
            'Test color combinations with accessibility tools',
            'Avoid using color alone to convey information',
            'Consider users with color vision deficiencies'
        ]
        
        return results
    
    def validate_keyboard_navigation(self) -> Dict:
        """Validate keyboard navigation support"""
        results = {
            'focusable_elements': [],
            'tabindex_issues': [],
            'skip_links': [],
            'focus_indicators': []
        }
        
        # Find focusable elements
        focusable_selectors = ['a', 'button', 'input', 'select', 'textarea', '[tabindex]']
        focusable_elements = []
        
        for selector in focusable_selectors:
            elements = self.soup.select(selector)
            focusable_elements.extend(elements)
        
        for element in focusable_elements:
            element_info = {
                'tag': element.name,
                'tabindex': element.get('tabindex'),
                'has_href': element.get('href') is not None if element.name == 'a' else None,
                'is_disabled': element.get('disabled') is not None
            }
            
            results['focusable_elements'].append(element_info)
            
            # Check for problematic tabindex values
            tabindex = element.get('tabindex')
            if tabindex:
                try:
                    tabindex_value = int(tabindex)
                    if tabindex_value > 0:
                        results['tabindex_issues'].append({
                            'element': element.name,
                            'tabindex': tabindex_value,
                            'issue': 'Positive tabindex disrupts natural tab order'
                        })
                        self.issues.append(AccessibilityIssue(
                            element=element.name,
                            issue_type='keyboard',
                            severity='warning',
                            description=f'Positive tabindex ({tabindex_value}) found',
                            recommendation='Use tabindex="0" or remove tabindex to preserve natural tab order',
                            wcag_guideline='2.4.3'
                        ))
                except ValueError:
                    results['tabindex_issues'].append({
                        'element': element.name,
                        'tabindex': tabindex,
                        'issue': 'Invalid tabindex value'
                    })
        
        # Check for skip links
        skip_links = self.soup.find_all('a', href=re.compile(r'^#'))
        for link in skip_links:
            link_text = link.get_text(strip=True).lower()
            if any(keyword in link_text for keyword in ['skip', 'jump', 'main', 'content']):
                results['skip_links'].append({
                    'text': link.get_text(strip=True),
                    'href': link.get('href')
                })
        
        if not results['skip_links']:
            self.issues.append(AccessibilityIssue(
                element='document',
                issue_type='keyboard',
                severity='info',
                description='No skip links found',
                recommendation='Consider adding skip links for keyboard users to bypass navigation',
                wcag_guideline='2.4.1'
            ))
        
        return results
    
    def generate_report(self) -> Dict:
        """Generate comprehensive accessibility report"""
        if not self.soup:
            self.load_html()
        
        report = {
            'file_path': self.html_file_path,
            'timestamp': str(Path(self.html_file_path).stat().st_mtime),
            'html_structure': self.validate_html5_structure(),
            'heading_hierarchy': self.validate_heading_hierarchy(),
            'aria_labels': self.validate_aria_labels(),
            'images': self.validate_images(),
            'forms': self.validate_forms(),
            'color_contrast': self.validate_color_contrast(),
            'keyboard_navigation': self.validate_keyboard_navigation(),
            'issues': [
                {
                    'element': issue.element,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'recommendation': issue.recommendation,
                    'wcag_guideline': issue.wcag_guideline
                }
                for issue in self.issues
            ],
            'statistics': self._calculate_stats()
        }
        
        return report
    
    def _calculate_stats(self) -> Dict:
        """Calculate accessibility statistics"""
        error_count = sum(1 for issue in self.issues if issue.severity == 'error')
        warning_count = sum(1 for issue in self.issues if issue.severity == 'warning')
        info_count = sum(1 for issue in self.issues if issue.severity == 'info')
        
        total_issues = len(self.issues)
        
        # Simple scoring (this could be more sophisticated)
        max_score = 100
        deductions = error_count * 10 + warning_count * 5 + info_count * 1
        accessibility_score = max(0, max_score - deductions)
        
        return {
            'total_issues': total_issues,
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'accessibility_score': accessibility_score,
            'compliance_level': self._get_compliance_level(accessibility_score)
        }
    
    def _get_compliance_level(self, score: int) -> str:
        """Determine WCAG compliance level based on score"""
        if score >= 90:
            return 'AAA (Excellent)'
        elif score >= 75:
            return 'AA (Good)'
        elif score >= 60:
            return 'A (Basic)'
        else:
            return 'Non-compliant'


class HTMLAccessibilityTestSuite(unittest.TestCase):
    """Test suite for HTML accessibility validation"""
    
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
        self.validator = HTMLAccessibilityValidator(str(self.html_file))
        self.assertTrue(self.validator.load_html(), "Failed to load HTML file")
    
    def test_html5_structure_validation(self):
        """Test HTML5 semantic structure"""
        logger.info("Testing HTML5 structure validation")
        
        results = self.validator.validate_html5_structure()
        
        # Assert critical structure elements
        self.assertTrue(results['has_doctype'], "HTML5 DOCTYPE declaration missing")
        self.assertTrue(results['has_html_tag'], "HTML tag missing")
        self.assertTrue(results['has_head'], "Head section missing")
        self.assertTrue(results['has_body'], "Body section missing")
        self.assertTrue(results['has_title'], "Page title missing")
        self.assertTrue(results['has_lang_attribute'], "Language attribute missing on html tag")
        self.assertTrue(results['has_viewport'], "Viewport meta tag missing")
        self.assertTrue(results['has_charset'], "Charset declaration missing")
        
        # Check for semantic elements
        semantic_found = [elem['element'] for elem in results['semantic_elements']]
        self.assertIn('header', semantic_found, "Header element not found")
        
        logger.info(f"HTML5 structure validation completed. Found semantic elements: {semantic_found}")
    
    def test_heading_hierarchy(self):
        """Test heading hierarchy compliance"""
        logger.info("Testing heading hierarchy")
        
        results = self.validator.validate_heading_hierarchy()
        
        self.assertTrue(results['has_h1'], "Page missing h1 element")
        self.assertFalse(results['multiple_h1'], "Multiple h1 elements found")
        self.assertEqual(len(results['empty_headings']), 0, "Empty headings found")
        self.assertEqual(len(results['hierarchy_issues']), 0, 
                        f"Heading hierarchy issues: {results['hierarchy_issues']}")
        
        logger.info(f"Found {len(results['headings'])} headings with proper hierarchy")
    
    def test_aria_labels_validation(self):
        """Test ARIA labels and roles"""
        logger.info("Testing ARIA labels and roles")
        
        results = self.validator.validate_aria_labels()
        
        # Should have no invalid ARIA roles
        self.assertEqual(len(results['invalid_aria_roles']), 0,
                        f"Invalid ARIA roles found: {results['invalid_aria_roles']}")
        
        # Interactive elements should have proper labels
        self.assertEqual(len(results['missing_aria_labels']), 0,
                        f"Elements missing ARIA labels: {results['missing_aria_labels']}")
        
        logger.info(f"ARIA validation completed. Found {len(results['elements_with_aria'])} elements with ARIA attributes")
    
    def test_image_accessibility(self):
        """Test image accessibility"""
        logger.info("Testing image accessibility")
        
        results = self.validator.validate_images()
        
        if results['total_images'] > 0:
            # All images should have alt attributes
            self.assertEqual(len(results['images_without_alt']), 0,
                            f"Images without alt attributes: {results['images_without_alt']}")
            
            # Calculate percentage of images with alt text
            alt_percentage = (results['images_with_alt'] / results['total_images']) * 100
            self.assertEqual(alt_percentage, 100.0, "Not all images have alt attributes")
        
        logger.info(f"Image accessibility validated. {results['images_with_alt']}/{results['total_images']} images have alt text")
    
    def test_form_accessibility(self):
        """Test form accessibility"""
        logger.info("Testing form accessibility")
        
        results = self.validator.validate_forms()
        
        if results['total_inputs'] > 0:
            # All form inputs should have labels
            self.assertEqual(len(results['inputs_without_labels']), 0,
                            f"Form inputs without labels: {results['inputs_without_labels']}")
            
            # Calculate label percentage
            label_percentage = (results['inputs_with_labels'] / results['total_inputs']) * 100
            self.assertGreaterEqual(label_percentage, 90.0, 
                                   "Less than 90% of inputs have proper labels")
        
        logger.info(f"Form accessibility validated. {results['inputs_with_labels']}/{results['total_inputs']} inputs have labels")
    
    def test_keyboard_navigation(self):
        """Test keyboard navigation support"""
        logger.info("Testing keyboard navigation")
        
        results = self.validator.validate_keyboard_navigation()
        
        # Should not have problematic tabindex values
        positive_tabindex_issues = [issue for issue in results['tabindex_issues'] 
                                   if 'Positive tabindex' in issue.get('issue', '')]
        self.assertEqual(len(positive_tabindex_issues), 0,
                        f"Problematic positive tabindex values found: {positive_tabindex_issues}")
        
        # Check that focusable elements exist
        focusable_count = len(results['focusable_elements'])
        self.assertGreater(focusable_count, 0, "No focusable elements found")
        
        logger.info(f"Keyboard navigation validated. {focusable_count} focusable elements found")
    
    def test_color_contrast_analysis(self):
        """Test color contrast considerations"""
        logger.info("Testing color contrast analysis")
        
        results = self.validator.validate_color_contrast()
        
        # This test mainly validates that color analysis is working
        # Manual testing would be needed for actual contrast ratios
        self.assertIsInstance(results['recommendations'], list)
        self.assertGreater(len(results['recommendations']), 0)
        
        if results['color_properties_found']:
            logger.info(f"Found {len(results['color_properties_found'])} elements with color properties")
        
        logger.info("Color contrast analysis completed (manual verification recommended)")
    
    def test_accessibility_compliance_score(self):
        """Test overall accessibility compliance score"""
        logger.info("Calculating accessibility compliance score")
        
        report = self.validator.generate_report()
        stats = report['statistics']
        
        # Should have minimal critical errors
        self.assertLessEqual(stats['errors'], 2, 
                           f"Too many accessibility errors: {stats['errors']}")
        
        # Should achieve reasonable accessibility score
        self.assertGreaterEqual(stats['accessibility_score'], 70,
                               f"Accessibility score too low: {stats['accessibility_score']}")
        
        # Should be at least WCAG AA compliant
        compliance = stats['compliance_level']
        self.assertIn('AA', compliance, f"WCAG compliance level insufficient: {compliance}")
        
        logger.info(f"Accessibility score: {stats['accessibility_score']}/100 - {compliance}")
    
    def test_generate_full_accessibility_report(self):
        """Generate and validate full accessibility report"""
        logger.info("Generating comprehensive accessibility report")
        
        report = self.validator.generate_report()
        
        # Validate report structure
        required_sections = [
            'html_structure', 'heading_hierarchy', 'aria_labels',
            'images', 'forms', 'keyboard_navigation', 'issues', 'statistics'
        ]
        
        for section in required_sections:
            self.assertIn(section, report, f"Missing report section: {section}")
        
        # Save report for manual review
        report_file = Path(__file__).parent / f'accessibility_report_{Path(self.html_file).stem}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Full accessibility report saved to: {report_file}")
        
        # Print summary
        stats = report['statistics']
        print(f"\n{'='*60}")
        print(f"ACCESSIBILITY VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"File: {report['file_path']}")
        print(f"Accessibility Score: {stats['accessibility_score']}/100")
        print(f"Compliance Level: {stats['compliance_level']}")
        print(f"Total Issues: {stats['total_issues']}")
        print(f"  - Errors: {stats['errors']}")
        print(f"  - Warnings: {stats['warnings']}")
        print(f"  - Info: {stats['info']}")
        
        if report['issues']:
            print(f"\nTop Issues:")
            for i, issue in enumerate(report['issues'][:5], 1):
                print(f"  {i}. [{issue['severity'].upper()}] {issue['description']}")
                print(f"     Recommendation: {issue['recommendation']}")
        
        print(f"{'='*60}")


def run_html_accessibility_tests(verbose=False):
    """Run HTML accessibility tests with optional verbose output"""
    
    # Setup test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(HTMLAccessibilityTestSuite)
    
    # Run tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='HTML Accessibility Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    success = run_html_accessibility_tests(verbose=args.verbose)
    sys.exit(0 if success else 1)