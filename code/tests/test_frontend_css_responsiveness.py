#!/usr/bin/env python3
"""
Frontend CSS Responsiveness and Cross-Device Testing Framework

This module provides comprehensive testing for CSS responsiveness, mobile optimization,
and cross-device compatibility for the live transcription website.

Features:
- Viewport and media query validation
- Mobile-first responsive design testing
- CSS Grid and Flexbox layout validation
- Touch interaction optimization
- Device-specific CSS property testing
- Performance impact assessment
- Print media support validation

Usage:
    python -m unittest test_frontend_css_responsiveness.CSSResponsivenessTestSuite
    python test_frontend_css_responsiveness.py --verbose
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
import urllib.request
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ResponsivenessIssue:
    """Data class for responsiveness issues"""
    component: str
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    description: str
    recommendation: str
    affected_breakpoints: List[str]

@dataclass
class Breakpoint:
    """Data class for CSS breakpoints"""
    name: str
    min_width: Optional[int]
    max_width: Optional[int]
    media_query: str

class CSSResponsivenessValidator:
    """Comprehensive CSS responsiveness validator"""
    
    def __init__(self, html_file_path: str):
        self.html_file_path = html_file_path
        self.soup = None
        self.css_content = ""
        self.issues: List[ResponsivenessIssue] = []
        
        # Define standard breakpoints
        self.breakpoints = [
            Breakpoint("mobile", None, 480, "max-width: 480px"),
            Breakpoint("tablet", 481, 768, "min-width: 481px and max-width: 768px"),
            Breakpoint("desktop", 769, 1024, "min-width: 769px and max-width: 1024px"),
            Breakpoint("large-desktop", 1025, None, "min-width: 1025px")
        ]
        
        # Mobile-first breakpoints used in the app
        self.app_breakpoints = [
            Breakpoint("small-mobile", None, 480, "max-width: 480px"),
            Breakpoint("mobile", None, 768, "max-width: 768px"),
            Breakpoint("tablet", 769, 1024, "min-width: 769px"),
            Breakpoint("desktop", 1025, None, "min-width: 1025px")
        ]
        
    def load_html_and_css(self) -> bool:
        """Load HTML and extract CSS content"""
        try:
            with open(self.html_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.soup = BeautifulSoup(content, 'html.parser')
            
            # Extract inline CSS
            style_tags = self.soup.find_all('style')
            for style in style_tags:
                if style.string:
                    self.css_content += style.string + "\n"
            
            # Extract external CSS (if any)
            link_tags = self.soup.find_all('link', {'rel': 'stylesheet'})
            for link in link_tags:
                href = link.get('href')
                if href:
                    try:
                        # Handle relative URLs
                        base_dir = Path(self.html_file_path).parent
                        css_file_path = base_dir / href.lstrip('/')
                        
                        if css_file_path.exists():
                            with open(css_file_path, 'r', encoding='utf-8') as css_file:
                                self.css_content += css_file.read() + "\n"
                        else:
                            logger.warning(f"External CSS file not found: {css_file_path}")
                    except Exception as e:
                        logger.warning(f"Could not load external CSS {href}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading HTML/CSS: {e}")
            return False
    
    def validate_viewport_meta(self) -> Dict:
        """Validate viewport meta tag for mobile optimization"""
        results = {
            'has_viewport_meta': False,
            'viewport_content': None,
            'is_mobile_optimized': False,
            'issues': []
        }
        
        viewport_meta = self.soup.find('meta', attrs={'name': 'viewport'})
        
        if viewport_meta:
            results['has_viewport_meta'] = True
            content = viewport_meta.get('content', '')
            results['viewport_content'] = content
            
            # Check for mobile-friendly viewport settings
            if 'width=device-width' in content:
                results['is_mobile_optimized'] = True
            else:
                results['issues'].append('Viewport should include width=device-width')
                self.issues.append(ResponsivenessIssue(
                    component='viewport',
                    issue_type='mobile_optimization',
                    severity='error',
                    description='Viewport meta tag missing width=device-width',
                    recommendation='Add width=device-width to viewport meta tag',
                    affected_breakpoints=['mobile', 'tablet']
                ))
            
            # Check for initial scale
            if 'initial-scale=1' not in content:
                results['issues'].append('Consider adding initial-scale=1 for consistent mobile rendering')
                self.issues.append(ResponsivenessIssue(
                    component='viewport',
                    issue_type='mobile_optimization',
                    severity='warning',
                    description='Viewport meta tag missing initial-scale=1',
                    recommendation='Add initial-scale=1 to viewport meta tag',
                    affected_breakpoints=['mobile']
                ))
            
            # Check for user scalability restrictions
            if 'user-scalable=no' in content or 'maximum-scale=1' in content:
                results['issues'].append('User scalability restrictions may harm accessibility')
                self.issues.append(ResponsivenessIssue(
                    component='viewport',
                    issue_type='accessibility',
                    severity='warning',
                    description='Viewport restricts user scaling',
                    recommendation='Allow users to zoom for accessibility',
                    affected_breakpoints=['mobile', 'tablet']
                ))
        else:
            results['issues'].append('Missing viewport meta tag')
            self.issues.append(ResponsivenessIssue(
                component='viewport',
                issue_type='mobile_optimization',
                severity='error',
                description='Missing viewport meta tag',
                recommendation='Add <meta name="viewport" content="width=device-width, initial-scale=1">',
                affected_breakpoints=['mobile', 'tablet']
            ))
        
        return results
    
    def validate_media_queries(self) -> Dict:
        """Validate CSS media queries and responsive design"""
        results = {
            'media_queries_found': [],
            'breakpoints_covered': [],
            'mobile_first_approach': False,
            'common_breakpoints_missing': [],
            'issues': []
        }
        
        # Extract media queries from CSS
        media_query_pattern = r'@media\s+([^{]+)\s*{([^{}]*(?:{[^{}]*}[^{}]*)*)}'
        media_matches = re.findall(media_query_pattern, self.css_content, re.IGNORECASE | re.DOTALL)
        
        for media_condition, media_content in media_matches:
            media_condition = media_condition.strip()
            results['media_queries_found'].append({
                'condition': media_condition,
                'has_content': bool(media_content.strip()),
                'content_length': len(media_content.strip())
            })
            
            # Check for mobile-first breakpoints
            if 'max-width' in media_condition and ('768px' in media_condition or '480px' in media_condition):
                results['mobile_first_approach'] = True
        
        # Check coverage of standard breakpoints
        css_lower = self.css_content.lower()
        common_breakpoints = {
            'mobile': ['480px', '576px'],
            'tablet': ['768px', '767px'],
            'desktop': ['1024px', '992px'],
            'large': ['1200px', '1440px']
        }
        
        for bp_name, bp_values in common_breakpoints.items():
            found = any(bp_val in css_lower for bp_val in bp_values)
            if found:
                results['breakpoints_covered'].append(bp_name)
            else:
                results['common_breakpoints_missing'].append(bp_name)
        
        # Validate media query usage patterns
        if not results['media_queries_found']:
            results['issues'].append('No media queries found - not responsive')
            self.issues.append(ResponsivenessIssue(
                component='media_queries',
                issue_type='responsive_design',
                severity='error',
                description='No media queries found in CSS',
                recommendation='Add media queries for responsive design',
                affected_breakpoints=['mobile', 'tablet', 'desktop']
            ))
        
        # Check for mobile-first approach
        max_width_queries = sum(1 for mq in results['media_queries_found'] 
                               if 'max-width' in mq['condition'])
        min_width_queries = sum(1 for mq in results['media_queries_found'] 
                               if 'min-width' in mq['condition'])
        
        if max_width_queries > min_width_queries:
            results['mobile_first_approach'] = True
        
        if not results['mobile_first_approach'] and results['media_queries_found']:
            self.issues.append(ResponsivenessIssue(
                component='media_queries',
                issue_type='responsive_design',
                severity='info',
                description='Consider using mobile-first approach with min-width media queries',
                recommendation='Use min-width media queries for better progressive enhancement',
                affected_breakpoints=['mobile']
            ))
        
        return results
    
    def validate_flexible_layouts(self) -> Dict:
        """Validate CSS flexbox and grid usage for responsive layouts"""
        results = {
            'flexbox_usage': {
                'elements': [],
                'properties': [],
                'total_usage': 0
            },
            'grid_usage': {
                'elements': [],
                'properties': [],
                'total_usage': 0
            },
            'responsive_units': {
                'percentage': 0,
                'viewport_units': 0,
                'rem_em': 0,
                'fixed_units': 0
            },
            'layout_issues': []
        }
        
        # Count flexbox usage
        flexbox_properties = [
            'display: flex', 'display: inline-flex', 'flex-direction',
            'justify-content', 'align-items', 'flex-wrap', 'flex-grow',
            'flex-shrink', 'flex-basis', 'align-self', 'order'
        ]
        
        for prop in flexbox_properties:
            count = len(re.findall(re.escape(prop), self.css_content, re.IGNORECASE))
            if count > 0:
                results['flexbox_usage']['properties'].append({
                    'property': prop,
                    'count': count
                })
                results['flexbox_usage']['total_usage'] += count
        
        # Count grid usage
        grid_properties = [
            'display: grid', 'display: inline-grid', 'grid-template-columns',
            'grid-template-rows', 'grid-gap', 'gap', 'grid-column',
            'grid-row', 'grid-area', 'justify-items', 'align-items'
        ]
        
        for prop in grid_properties:
            count = len(re.findall(re.escape(prop), self.css_content, re.IGNORECASE))
            if count > 0:
                results['grid_usage']['properties'].append({
                    'property': prop,
                    'count': count
                })
                results['grid_usage']['total_usage'] += count
        
        # Count responsive units
        unit_patterns = {
            'percentage': r'\d+\.?\d*%',
            'viewport_units': r'\d+\.?\d*(vw|vh|vmin|vmax)',
            'rem_em': r'\d+\.?\d*(rem|em)',
            'fixed_units': r'\d+\.?\d*(px|pt|cm|mm|in)'
        }
        
        for unit_type, pattern in unit_patterns.items():
            matches = re.findall(pattern, self.css_content, re.IGNORECASE)
            results['responsive_units'][unit_type] = len(matches)
        
        # Analyze layout approach
        total_units = sum(results['responsive_units'].values())
        if total_units > 0:
            fixed_percentage = (results['responsive_units']['fixed_units'] / total_units) * 100
            
            if fixed_percentage > 70:
                results['layout_issues'].append('High usage of fixed units may harm responsiveness')
                self.issues.append(ResponsivenessIssue(
                    component='layout',
                    issue_type='responsive_design',
                    severity='warning',
                    description=f'{fixed_percentage:.1f}% of units are fixed (px, pt, etc.)',
                    recommendation='Consider using relative units (%, rem, vw, vh) for better responsiveness',
                    affected_breakpoints=['mobile', 'tablet']
                ))
        
        # Check if using modern layout methods
        has_modern_layout = (
            results['flexbox_usage']['total_usage'] > 0 or 
            results['grid_usage']['total_usage'] > 0
        )
        
        if not has_modern_layout:
            results['layout_issues'].append('No modern layout methods (flexbox/grid) detected')
            self.issues.append(ResponsivenessIssue(
                component='layout',
                issue_type='responsive_design',
                severity='info',
                description='No flexbox or CSS grid usage detected',
                recommendation='Consider using flexbox or CSS grid for more flexible layouts',
                affected_breakpoints=['all']
            ))
        
        return results
    
    def validate_mobile_touch_targets(self) -> Dict:
        """Validate mobile touch target sizes and spacing"""
        results = {
            'touch_friendly_elements': [],
            'potential_issues': [],
            'button_analysis': {
                'total_buttons': 0,
                'with_touch_sizing': 0,
                'undersized_buttons': []
            }
        }
        
        # Extract button styles
        button_selectors = ['.btn', 'button', 'input[type="button"]', 'input[type="submit"]']
        
        for selector in button_selectors:
            # Look for touch-friendly sizing in CSS
            button_pattern = rf'{re.escape(selector)}\s*{{[^}}]*}}'
            button_matches = re.findall(button_pattern, self.css_content, re.IGNORECASE | re.DOTALL)
            
            for match in button_matches:
                has_min_size = (
                    'min-width:' in match or 'min-height:' in match or
                    'padding:' in match or 'height:' in match or 'width:' in match
                )
                
                if has_min_size:
                    results['touch_friendly_elements'].append({
                        'selector': selector,
                        'has_touch_sizing': True
                    })
                    results['button_analysis']['with_touch_sizing'] += 1
                else:
                    results['potential_issues'].append(f'{selector} may lack touch-friendly sizing')
                
                results['button_analysis']['total_buttons'] += 1
        
        # Check for touch-friendly padding and spacing
        touch_properties = ['padding', 'margin', 'gap']
        for prop in touch_properties:
            pattern = rf'{prop}\s*:\s*([^;}}]+)'
            matches = re.findall(pattern, self.css_content, re.IGNORECASE)
            
            for match in matches:
                # Look for reasonable touch spacing (at least 8px or equivalent)
                if any(unit in match.lower() for unit in ['px', 'rem', 'em']):
                    # Extract numeric values
                    values = re.findall(r'\d+', match)
                    if values:
                        max_value = max(int(v) for v in values)
                        if max_value >= 8:  # Minimum touch-friendly spacing
                            results['touch_friendly_elements'].append({
                                'property': prop,
                                'value': match,
                                'touch_friendly': True
                            })
        
        # Generate recommendations
        if results['button_analysis']['total_buttons'] > 0:
            touch_percentage = (results['button_analysis']['with_touch_sizing'] / 
                              results['button_analysis']['total_buttons']) * 100
            
            if touch_percentage < 80:
                self.issues.append(ResponsivenessIssue(
                    component='touch_targets',
                    issue_type='mobile_optimization',
                    severity='warning',
                    description=f'Only {touch_percentage:.1f}% of buttons have touch-friendly sizing',
                    recommendation='Ensure buttons have min-width: 44px and adequate padding for touch',
                    affected_breakpoints=['mobile', 'tablet']
                ))
        
        return results
    
    def validate_mobile_specific_styles(self) -> Dict:
        """Validate mobile-specific CSS properties and optimizations"""
        results = {
            'mobile_optimizations': [],
            'performance_issues': [],
            'mobile_specific_properties': []
        }
        
        # Check for mobile-specific CSS properties
        mobile_properties = {
            '-webkit-tap-highlight-color': 'Controls tap highlight on mobile',
            '-webkit-touch-callout': 'Controls touch callout on iOS',
            '-webkit-user-select': 'Controls text selection',
            'touch-action': 'Controls touch gestures',
            '-webkit-overflow-scrolling': 'Enables momentum scrolling on iOS',
            'will-change': 'Optimizes for animations',
            'transform3d': 'Hardware acceleration'
        }
        
        for prop, description in mobile_properties.items():
            if prop.lower() in self.css_content.lower():
                results['mobile_optimizations'].append({
                    'property': prop,
                    'description': description,
                    'found': True
                })
        
        # Check for performance-impacting properties
        performance_issues = [
            'box-shadow', 'border-radius', 'gradient', 'filter',
            'transform', 'animation', 'transition'
        ]
        
        for prop in performance_issues:
            count = len(re.findall(prop, self.css_content, re.IGNORECASE))
            if count > 0:
                results['performance_issues'].append({
                    'property': prop,
                    'count': count,
                    'impact': 'May affect performance on low-end devices'
                })
        
        # Check for hardware acceleration usage
        transform3d_pattern = r'transform\s*:\s*[^;]*translate3d|translateZ'
        if re.search(transform3d_pattern, self.css_content, re.IGNORECASE):
            results['mobile_optimizations'].append({
                'property': 'hardware_acceleration',
                'description': 'Using 3D transforms for hardware acceleration',
                'found': True
            })
        
        return results
    
    def validate_print_styles(self) -> Dict:
        """Validate print media styles"""
        results = {
            'has_print_styles': False,
            'print_optimizations': [],
            'recommendations': []
        }
        
        # Check for print media queries
        print_media_pattern = r'@media\s+print\s*{([^{}]*(?:{[^{}]*}[^{}]*)*)}'
        print_matches = re.findall(print_media_pattern, self.css_content, re.IGNORECASE | re.DOTALL)
        
        if print_matches:
            results['has_print_styles'] = True
            
            # Analyze print styles
            print_content = '\n'.join(print_matches)
            
            print_optimizations = [
                ('color adjustments', r'color\s*:\s*black|#000'),
                ('background removal', r'background\s*:\s*none|transparent'),
                ('font adjustments', r'font-size\s*:\s*\d+pt'),
                ('page breaks', r'page-break-|break-'),
                ('display adjustments', r'display\s*:\s*none')
            ]
            
            for opt_name, pattern in print_optimizations:
                if re.search(pattern, print_content, re.IGNORECASE):
                    results['print_optimizations'].append(opt_name)
        else:
            results['recommendations'].append('Consider adding print styles for better printability')
            self.issues.append(ResponsivenessIssue(
                component='print_styles',
                issue_type='user_experience',
                severity='info',
                description='No print media styles found',
                recommendation='Add @media print styles for better print experience',
                affected_breakpoints=['print']
            ))
        
        return results
    
    def validate_css_custom_properties(self) -> Dict:
        """Validate CSS custom properties (CSS variables) usage"""
        results = {
            'custom_properties': [],
            'usage_count': 0,
            'responsive_usage': False,
            'color_system': False
        }
        
        # Find CSS custom property definitions
        custom_prop_pattern = r'--[\w-]+\s*:\s*([^;]+)'
        custom_props = re.findall(custom_prop_pattern, self.css_content, re.IGNORECASE)
        
        for prop_value in custom_props:
            results['custom_properties'].append(prop_value.strip())
            results['usage_count'] += 1
        
        # Check for color system using custom properties
        color_vars = [prop for prop in results['custom_properties'] 
                     if any(color in prop.lower() for color in ['#', 'rgb', 'hsl', 'color'])]
        
        if len(color_vars) >= 3:
            results['color_system'] = True
        
        # Check for responsive usage of custom properties
        var_in_media_pattern = r'@media[^{]+{[^{}]*var\('
        if re.search(var_in_media_pattern, self.css_content, re.IGNORECASE | re.DOTALL):
            results['responsive_usage'] = True
        
        return results
    
    def generate_responsiveness_report(self) -> Dict:
        """Generate comprehensive responsiveness report"""
        if not self.soup:
            self.load_html_and_css()
        
        report = {
            'file_path': self.html_file_path,
            'timestamp': str(Path(self.html_file_path).stat().st_mtime),
            'viewport_validation': self.validate_viewport_meta(),
            'media_queries': self.validate_media_queries(),
            'flexible_layouts': self.validate_flexible_layouts(),
            'touch_targets': self.validate_mobile_touch_targets(),
            'mobile_optimizations': self.validate_mobile_specific_styles(),
            'print_styles': self.validate_print_styles(),
            'css_variables': self.validate_css_custom_properties(),
            'issues': [
                {
                    'component': issue.component,
                    'issue_type': issue.issue_type,
                    'severity': issue.severity,
                    'description': issue.description,
                    'recommendation': issue.recommendation,
                    'affected_breakpoints': issue.affected_breakpoints
                }
                for issue in self.issues
            ],
            'statistics': self._calculate_responsiveness_stats()
        }
        
        return report
    
    def _calculate_responsiveness_stats(self) -> Dict:
        """Calculate responsiveness statistics"""
        error_count = sum(1 for issue in self.issues if issue.severity == 'error')
        warning_count = sum(1 for issue in self.issues if issue.severity == 'warning')
        info_count = sum(1 for issue in self.issues if issue.severity == 'info')
        
        total_issues = len(self.issues)
        
        # Calculate responsiveness score
        max_score = 100
        deductions = error_count * 15 + warning_count * 10 + info_count * 5
        responsiveness_score = max(0, max_score - deductions)
        
        return {
            'total_issues': total_issues,
            'errors': error_count,
            'warnings': warning_count,
            'info': info_count,
            'responsiveness_score': responsiveness_score,
            'mobile_readiness': self._get_mobile_readiness(responsiveness_score)
        }
    
    def _get_mobile_readiness(self, score: int) -> str:
        """Determine mobile readiness level based on score"""
        if score >= 90:
            return 'Excellent Mobile Support'
        elif score >= 75:
            return 'Good Mobile Support'
        elif score >= 60:
            return 'Basic Mobile Support'
        else:
            return 'Poor Mobile Support'


class CSSResponsivenessTestSuite(unittest.TestCase):
    """Test suite for CSS responsiveness validation"""
    
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
        self.validator = CSSResponsivenessValidator(str(self.html_file))
        self.assertTrue(self.validator.load_html_and_css(), "Failed to load HTML and CSS")
    
    def test_viewport_meta_validation(self):
        """Test viewport meta tag for mobile optimization"""
        logger.info("Testing viewport meta tag validation")
        
        results = self.validator.validate_viewport_meta()
        
        self.assertTrue(results['has_viewport_meta'], "Missing viewport meta tag")
        self.assertTrue(results['is_mobile_optimized'], "Viewport not optimized for mobile")
        
        if results['viewport_content']:
            self.assertIn('width=device-width', results['viewport_content'], 
                         "Viewport should include width=device-width")
        
        logger.info(f"Viewport validation completed. Mobile optimized: {results['is_mobile_optimized']}")
    
    def test_media_queries_presence(self):
        """Test presence and quality of media queries"""
        logger.info("Testing media queries presence and structure")
        
        results = self.validator.validate_media_queries()
        
        self.assertGreater(len(results['media_queries_found']), 0, "No media queries found")
        self.assertGreater(len(results['breakpoints_covered']), 1, 
                          "Insufficient breakpoint coverage")
        
        # Check for mobile coverage
        mobile_covered = any(bp in results['breakpoints_covered'] 
                           for bp in ['mobile', 'tablet'])
        self.assertTrue(mobile_covered, "Mobile breakpoints not properly covered")
        
        logger.info(f"Found {len(results['media_queries_found'])} media queries covering {results['breakpoints_covered']}")
    
    def test_flexible_layout_usage(self):
        """Test usage of flexible layout methods"""
        logger.info("Testing flexible layout methods (Flexbox/Grid)")
        
        results = self.validator.validate_flexible_layouts()
        
        # Should use modern layout methods
        has_flexbox = results['flexbox_usage']['total_usage'] > 0
        has_grid = results['grid_usage']['total_usage'] > 0
        
        self.assertTrue(has_flexbox or has_grid, 
                       "Should use modern layout methods (Flexbox or Grid)")
        
        # Check for reasonable use of relative units
        total_units = sum(results['responsive_units'].values())
        if total_units > 0:
            fixed_percentage = (results['responsive_units']['fixed_units'] / total_units) * 100
            self.assertLess(fixed_percentage, 80, 
                           f"Too much reliance on fixed units ({fixed_percentage:.1f}%)")
        
        logger.info(f"Layout analysis: Flexbox usage: {results['flexbox_usage']['total_usage']}, "
                   f"Grid usage: {results['grid_usage']['total_usage']}")
    
    def test_mobile_touch_optimization(self):
        """Test mobile touch target optimization"""
        logger.info("Testing mobile touch target optimization")
        
        results = self.validator.validate_mobile_touch_targets()
        
        # Should have touch-friendly elements
        self.assertGreater(len(results['touch_friendly_elements']), 0,
                          "No touch-friendly elements found")
        
        # Button analysis
        if results['button_analysis']['total_buttons'] > 0:
            touch_ratio = (results['button_analysis']['with_touch_sizing'] / 
                          results['button_analysis']['total_buttons'])
            self.assertGreater(touch_ratio, 0.5, 
                              "Less than 50% of buttons have touch-friendly sizing")
        
        logger.info(f"Touch optimization: {len(results['touch_friendly_elements'])} touch-friendly elements found")
    
    def test_mobile_specific_optimizations(self):
        """Test mobile-specific CSS optimizations"""
        logger.info("Testing mobile-specific CSS optimizations")
        
        results = self.validator.validate_mobile_specific_styles()
        
        # Should have some mobile optimizations
        self.assertGreaterEqual(len(results['mobile_optimizations']), 1,
                               "No mobile-specific optimizations found")
        
        # Performance check
        if results['performance_issues']:
            heavy_effects_count = sum(issue['count'] for issue in results['performance_issues'])
            self.assertLess(heavy_effects_count, 50, 
                           "Too many performance-heavy CSS effects for mobile")
        
        logger.info(f"Mobile optimizations: {len(results['mobile_optimizations'])} found")
    
    def test_responsive_breakpoints_coverage(self):
        """Test coverage of essential responsive breakpoints"""
        logger.info("Testing responsive breakpoints coverage")
        
        # Test the specific breakpoints used in the app
        media_results = self.validator.validate_media_queries()
        css_content = self.validator.css_content.lower()
        
        # Check for the app's specific breakpoints
        expected_breakpoints = ['768px', '480px']  # Mobile breakpoints used in the app
        
        found_breakpoints = []
        for bp in expected_breakpoints:
            if bp in css_content:
                found_breakpoints.append(bp)
        
        self.assertGreaterEqual(len(found_breakpoints), 1, 
                               f"Essential mobile breakpoints not found. Expected: {expected_breakpoints}, Found: {found_breakpoints}")
        
        logger.info(f"Breakpoint coverage: {found_breakpoints}")
    
    def test_css_custom_properties_usage(self):
        """Test CSS custom properties for maintainable responsive design"""
        logger.info("Testing CSS custom properties usage")
        
        results = self.validator.validate_css_custom_properties()
        
        # Should use CSS custom properties for better maintenance
        self.assertGreater(results['usage_count'], 0, 
                          "No CSS custom properties found")
        
        # Should have color system
        self.assertTrue(results['color_system'], 
                       "CSS custom properties should be used for color system")
        
        logger.info(f"CSS variables: {results['usage_count']} properties, Color system: {results['color_system']}")
    
    def test_print_styles_consideration(self):
        """Test consideration for print styles"""
        logger.info("Testing print styles consideration")
        
        results = self.validator.validate_print_styles()
        
        # While not required, print styles are good UX
        if not results['has_print_styles']:
            logger.info("No print styles found - consider adding for better user experience")
        else:
            self.assertGreater(len(results['print_optimizations']), 0,
                              "Print styles found but no optimizations detected")
        
        logger.info(f"Print styles: {'Found' if results['has_print_styles'] else 'Not found'}")
    
    def test_overall_responsiveness_score(self):
        """Test overall responsiveness score"""
        logger.info("Calculating overall responsiveness score")
        
        report = self.validator.generate_responsiveness_report()
        stats = report['statistics']
        
        # Should achieve good responsiveness score
        self.assertGreaterEqual(stats['responsiveness_score'], 60,
                               f"Responsiveness score too low: {stats['responsiveness_score']}")
        
        # Should have minimal critical errors
        self.assertLessEqual(stats['errors'], 3,
                            f"Too many responsiveness errors: {stats['errors']}")
        
        mobile_readiness = stats['mobile_readiness']
        self.assertNotEqual(mobile_readiness, 'Poor Mobile Support',
                           f"Mobile readiness level unacceptable: {mobile_readiness}")
        
        logger.info(f"Responsiveness score: {stats['responsiveness_score']}/100 - {mobile_readiness}")
    
    def test_generate_full_responsiveness_report(self):
        """Generate and validate full responsiveness report"""
        logger.info("Generating comprehensive responsiveness report")
        
        report = self.validator.generate_responsiveness_report()
        
        # Validate report structure
        required_sections = [
            'viewport_validation', 'media_queries', 'flexible_layouts',
            'touch_targets', 'mobile_optimizations', 'statistics'
        ]
        
        for section in required_sections:
            self.assertIn(section, report, f"Missing report section: {section}")
        
        # Save report for manual review
        report_file = Path(__file__).parent / f'responsiveness_report_{Path(self.html_file).stem}.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Full responsiveness report saved to: {report_file}")
        
        # Print summary
        stats = report['statistics']
        print(f"\n{'='*60}")
        print(f"CSS RESPONSIVENESS VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"File: {report['file_path']}")
        print(f"Responsiveness Score: {stats['responsiveness_score']}/100")
        print(f"Mobile Readiness: {stats['mobile_readiness']}")
        print(f"Total Issues: {stats['total_issues']}")
        print(f"  - Errors: {stats['errors']}")
        print(f"  - Warnings: {stats['warnings']}")
        print(f"  - Info: {stats['info']}")
        
        # Media query summary
        mq_results = report['media_queries']
        print(f"\nMedia Queries: {len(mq_results['media_queries_found'])}")
        print(f"Breakpoints Covered: {mq_results['breakpoints_covered']}")
        print(f"Mobile-First Approach: {mq_results['mobile_first_approach']}")
        
        # Layout summary
        layout_results = report['flexible_layouts']
        print(f"\nFlexbox Usage: {layout_results['flexbox_usage']['total_usage']}")
        print(f"Grid Usage: {layout_results['grid_usage']['total_usage']}")
        
        if report['issues']:
            print(f"\nTop Issues:")
            for i, issue in enumerate(report['issues'][:5], 1):
                print(f"  {i}. [{issue['severity'].upper()}] {issue['description']}")
                print(f"     Affected: {', '.join(issue['affected_breakpoints'])}")
        
        print(f"{'='*60}")


def run_responsiveness_tests(verbose=False):
    """Run CSS responsiveness tests with optional verbose output"""
    
    # Setup test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(CSSResponsivenessTestSuite)
    
    # Run tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity, buffer=True)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='CSS Responsiveness Test Suite')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    success = run_responsiveness_tests(verbose=args.verbose)
    sys.exit(0 if success else 1)