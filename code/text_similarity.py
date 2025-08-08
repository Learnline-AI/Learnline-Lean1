"""
Text Similarity Module

Provides text similarity calculations for transcription processing.
Focuses on comparing text endings for transcription accuracy assessment.
"""

from difflib import SequenceMatcher
import re
from typing import Optional, Literal


class TextSimilarity:
    """
    Text similarity calculator with configurable focus and word count for comparison.
    Supports various focus modes for different transcription analysis needs.
    """
    
    def __init__(
        self, 
        focus: Literal['end', 'start', 'full'] = 'end', 
        n_words: int = 5
    ) -> None:
        """
        Initialize TextSimilarity with specified focus and word count.
        
        Args:
            focus: Where to focus the comparison ('end', 'start', or 'full')
            n_words: Number of words to consider when focus is 'end' or 'start'
        """
        self.focus = focus
        self.n_words = n_words
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison by converting to lowercase and cleaning.
        
        Args:
            text: Input text to normalize
            
        Returns:
            Normalized text string
        """
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def _get_focused_text(self, text: str) -> str:
        """
        Extract the focused portion of text based on the configured focus mode.
        
        Args:
            text: Input text to extract from
            
        Returns:
            Focused portion of the text
        """
        normalized_text = self._normalize_text(text)
        
        if self.focus == 'full':
            return normalized_text
        
        words = normalized_text.split()
        
        if self.focus == 'end':
            return ' '.join(words[-self.n_words:]) if words else ""
        elif self.focus == 'start':
            return ' '.join(words[:self.n_words]) if words else ""
        
        return normalized_text
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings based on the configured focus.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity ratio between 0.0 and 1.0 (1.0 = identical)
        """
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        focused_text1 = self._get_focused_text(text1)
        focused_text2 = self._get_focused_text(text2)
        
        if not focused_text1 and not focused_text2:
            return 1.0
        if not focused_text1 or not focused_text2:
            return 0.0
        
        # Use SequenceMatcher for similarity calculation
        matcher = SequenceMatcher(None, focused_text1, focused_text2)
        return matcher.ratio()
    
    def is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """
        Check if two texts are similar above a given threshold.
        
        Args:
            text1: First text string
            text2: Second text string
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            True if similarity is above threshold
        """
        similarity = self.calculate_similarity(text1, text2)
        return similarity >= threshold
    
    def get_word_overlap(self, text1: str, text2: str) -> float:
        """
        Calculate word-level overlap between two texts.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Word overlap ratio between 0.0 and 1.0
        """
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        words1 = set(self._normalize_text(text1).split())
        words2 = set(self._normalize_text(text2).split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0