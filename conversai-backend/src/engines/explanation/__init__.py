"""
Explanation Engine - Public Interface

This module provides the facade for the Explanation Engine.
It orchestrates the analyzer, structurer, and narrator components
to transform input text into narrated explanations.

Usage:
    from src.engines.explanation import process
    
    narration, segments, metadata = await process(text, duration, instruction)
"""

from typing import Tuple, List, Optional
from dataclasses import asdict

from src.shared.types import Segment, Duration
from src.engines.explanation.analyzer import Analyzer, AnalyzerError
from src.engines.explanation.narrator import Narrator, NarratorError, ExplanationOutput
from src.shared.config import settings


class ExplanationEngineError(Exception):
    """Base exception for Explanation Engine errors."""
    pass


class ExplanationEngine:
    """
    Main facade for the Explanation Engine.
    
    Orchestrates the pipeline:
    1. Analyzer validates and analyzes input
    2. Structurer builds prompts (internally used by Narrator)
    3. Narrator generates the explanation via LLM
    """

    def __init__(self):
        """Initialize the Explanation Engine."""
        # Narrator now reads config from settings (supports Gemini and Ollama)
        self.narrator = Narrator()

    async def process(
        self,
        text: str,
        duration: Duration,
        instruction: Optional[str] = None
    ) -> Tuple[str, List[Segment], dict]:
        """
        Process input text and generate a narrated explanation.
        
        Args:
            text: The input text to explain (100-5000 chars)
            duration: Duration mode ("short" or "medium")
            instruction: Optional user instruction for tone/style
            
        Returns:
            Tuple of (narration, segments, metadata)
            - narration: Complete narration text
            - segments: List of Segment objects with timing
            - metadata: Dict with concepts, difficulty, duration
            
        Raises:
            ExplanationEngineError: If processing fails
        """
        # Step 1: Validate input
        is_valid, error_msg = Analyzer.validate_input(text)
        if not is_valid:
            raise ExplanationEngineError(f"Validation failed: {error_msg}")
        
        # Step 2: Analyze for metadata (optional, for logging/debugging)
        analysis = Analyzer.analyze(text)
        
        # Step 3: Generate explanation via narrator
        try:
            output: ExplanationOutput = await self.narrator.generate(
                text=text,
                duration=duration,
                instruction=instruction
            )
        except NarratorError as e:
            raise ExplanationEngineError(f"Narration failed: {e}")
        
        # Step 4: Convert to output format
        segments = [
            Segment(
                text=seg.text,
                startTime=seg.startTime,
                endTime=seg.endTime
            )
            for seg in output.segments
        ]
        
        metadata = {
            "concepts": output.metadata.concepts,
            "difficulty": output.metadata.difficulty,
            "estimatedDuration": output.metadata.estimatedDuration
        }
        
        return output.narration, segments, metadata


# Singleton instance
_engine: Optional[ExplanationEngine] = None


def _get_engine() -> ExplanationEngine:
    """Get or create the engine singleton."""
    global _engine
    if _engine is None:
        _engine = ExplanationEngine()
    return _engine


async def process(
    text: str,
    duration: Duration,
    instruction: Optional[str] = None
) -> Tuple[str, List[Segment], dict]:
    """
    Public interface: Process text and generate explanation.
    
    Args:
        text: Input text to explain
        duration: Duration mode
        instruction: Optional style instruction
        
    Returns:
        Tuple of (narration, segments, metadata)
    """
    engine = _get_engine()
    return await engine.process(text, duration, instruction)
