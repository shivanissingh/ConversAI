"""
Explanation Engine - Analyzer Module

Responsible for:
- Input validation (text length, format)
- Content complexity detection
- Concept pre-scanning

Follows the frozen design: docs/EXPLANATION_ENGINE_DESIGN.md
"""

import re
from dataclasses import dataclass
from typing import Optional
from src.shared.types import Duration


# Input constraints from architecture
MIN_TEXT_LENGTH = 100
MAX_TEXT_LENGTH = 5000


@dataclass
class AnalysisResult:
    """Result of text analysis."""
    is_valid: bool
    error_message: Optional[str]
    char_count: int
    word_count: int
    estimated_complexity: str  # "simple", "moderate", "complex"
    detected_topics: list[str]


class AnalyzerError(Exception):
    """Raised when analysis fails."""
    pass


class Analyzer:
    """
    Analyzes input text for validation and complexity detection.
    """

    @staticmethod
    def validate_input(text: str) -> tuple[bool, Optional[str]]:
        """
        Validate the input text meets requirements.
        
        Args:
            text: The input text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text:
            return False, "Text cannot be empty"
        
        if not isinstance(text, str):
            return False, "Text must be a string"
        
        # Strip whitespace for length check
        stripped = text.strip()
        
        if len(stripped) < MIN_TEXT_LENGTH:
            return False, f"Text too short: {len(stripped)} chars (minimum: {MIN_TEXT_LENGTH})"
        
        if len(stripped) > MAX_TEXT_LENGTH:
            return False, f"Text too long: {len(stripped)} chars (maximum: {MAX_TEXT_LENGTH})"
        
        return True, None

    @staticmethod
    def detect_complexity(text: str) -> str:
        """
        Detect the complexity of the input text.
        
        Uses heuristics based on:
        - Average sentence length
        - Presence of technical terms
        - Vocabulary diversity
        
        Returns: "simple", "moderate", or "complex"
        """
        words = text.split()
        word_count = len(words)
        
        if word_count == 0:
            return "simple"
        
        # Count sentences (rough estimation)
        sentences = len(re.findall(r'[.!?]+', text)) or 1
        avg_sentence_length = word_count / sentences
        
        # Count unique words (vocabulary diversity)
        unique_words = len(set(word.lower() for word in words))
        diversity_ratio = unique_words / word_count
        
        # Detect technical indicators
        technical_patterns = [
            r'\b\d+%\b',  # Percentages
            r'\b[A-Z]{2,}\b',  # Acronyms
            r'\b\w+tion\b',  # Technical suffixes
            r'\b\w+ism\b',
            r'\b\w+ology\b',
        ]
        technical_count = sum(
            len(re.findall(pattern, text)) for pattern in technical_patterns
        )
        
        # Scoring
        complexity_score = 0
        
        # Long sentences increase complexity
        if avg_sentence_length > 25:
            complexity_score += 2
        elif avg_sentence_length > 18:
            complexity_score += 1
        
        # High vocabulary diversity suggests complexity
        if diversity_ratio > 0.7:
            complexity_score += 1
        
        # Technical terms indicate complexity
        if technical_count > 5:
            complexity_score += 2
        elif technical_count > 2:
            complexity_score += 1
        
        # Map score to complexity level
        if complexity_score >= 4:
            return "complex"
        elif complexity_score >= 2:
            return "moderate"
        else:
            return "simple"

    @staticmethod
    def extract_topics(text: str, max_topics: int = 5) -> list[str]:
        """
        Extract potential topics/key nouns from the text.
        
        This is a simple heuristic extraction used as fallback
        when LLM fails to return concepts.
        
        Args:
            text: The input text
            max_topics: Maximum number of topics to return
            
        Returns:
            List of detected topic strings
        """
        # Simple approach: find capitalized words that aren't sentence starters
        words = text.split()
        topics = []
        
        for i, word in enumerate(words):
            # Skip first word of sentences
            if i > 0 and words[i-1].endswith(('.', '!', '?')):
                continue
            
            # Skip if it's the first word
            if i == 0:
                continue
            
            # Check if word starts with capital (proper noun indicator)
            clean_word = re.sub(r'[^\w]', '', word)
            if clean_word and clean_word[0].isupper() and len(clean_word) > 2:
                if clean_word.lower() not in ['the', 'this', 'that', 'these', 'those']:
                    topics.append(clean_word)
        
        # Deduplicate and limit
        seen = set()
        unique_topics = []
        for topic in topics:
            if topic.lower() not in seen:
                seen.add(topic.lower())
                unique_topics.append(topic)
                if len(unique_topics) >= max_topics:
                    break
        
        return unique_topics

    @staticmethod
    def analyze(text: str) -> AnalysisResult:
        """
        Perform complete analysis of the input text.
        
        Args:
            text: The input text to analyze
            
        Returns:
            AnalysisResult with validation and analysis data
        """
        is_valid, error_message = Analyzer.validate_input(text)
        
        if not is_valid:
            return AnalysisResult(
                is_valid=False,
                error_message=error_message,
                char_count=len(text) if text else 0,
                word_count=len(text.split()) if text else 0,
                estimated_complexity="unknown",
                detected_topics=[]
            )
        
        char_count = len(text)
        word_count = len(text.split())
        complexity = Analyzer.detect_complexity(text)
        topics = Analyzer.extract_topics(text)
        
        return AnalysisResult(
            is_valid=True,
            error_message=None,
            char_count=char_count,
            word_count=word_count,
            estimated_complexity=complexity,
            detected_topics=topics
        )

    @staticmethod
    def suggest_duration(text: str) -> Duration:
        """
        Suggest appropriate duration based on text analysis.
        
        Args:
            text: The input text
            
        Returns:
            Suggested Duration enum value
        """
        word_count = len(text.split())
        complexity = Analyzer.detect_complexity(text)
        
        # Complex or long content benefits from medium duration
        if complexity == "complex" or word_count > 300:
            return Duration.MEDIUM
        
        # Simple, shorter content works well with short duration
        if complexity == "simple" and word_count < 200:
            return Duration.SHORT
        
        # Default to medium for balanced coverage
        return Duration.MEDIUM


# Convenience functions for direct use
def validate_text(text: str) -> tuple[bool, Optional[str]]:
    """Validate input text. Returns (is_valid, error_message)."""
    return Analyzer.validate_input(text)


def analyze_text(text: str) -> AnalysisResult:
    """Analyze input text completely."""
    return Analyzer.analyze(text)
