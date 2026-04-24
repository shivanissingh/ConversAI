"""
Aggregation Engine - Public Facade

This module provides the SINGLE public interface for the Aggregation Engine.

The Aggregation Engine orchestrates existing engines (Explanation, Visual, Voice)
and combines their outputs into a unified multimodal response.

Usage:
    from src.engines.aggregation import aggregate
    
    result = await aggregate(
        text="...",
        duration="short",
        instruction=None,
        avatar_enabled=True
    )
"""

from typing import Optional, Dict
from src.shared.types import Duration
from src.shared.logger import logger
from src.engines.aggregation.composer import (
    orchestrate_aggregation,
    AggregationError
)


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


async def aggregate(
    text: str,
    duration: str,
    instruction: Optional[str] = None,
    avatar_enabled: bool = True
) -> Dict:
    """
    Orchestrate all engines and compose unified multimodal response.
    
    This is the ONLY public interface of the Aggregation Engine.
    
    Flow:
        1. Validate input
        2. Delegate orchestration to composer
        3. Return unified response
    
    Args:
        text: Original text to explain (10-5000 chars)
        duration: "short" | "medium"
        instruction: Optional user instruction (e.g., "explain like I'm 5")
        avatar_enabled: Whether to generate avatar metadata
    
    Returns:
        {
            "narration": str,
            "segments": List[AlignedSegment],
            "audio": str,  # Base64 encoded
            "audioDuration": float,
            "avatar": Optional[AvatarData],
            "metadata": {
                "totalTime": float,
                "explanationSuccess": bool,
                "visualSuccess": bool,
                "voiceSuccess": bool,
                "avatarSuccess": bool,
                "visualStats": {
                    "requested": int,
                    "generated": int,
                    "failed": int
                },
                "failures": List[Dict]
            }
        }
    
    Raises:
        ValidationError: If input validation fails
        AggregationError: If critical engines (Explanation, Voice) fail
    """
    # ========================================================================
    # Input Validation
    # ========================================================================
    
    # Validate text
    if not text:
        raise ValidationError("Text is required")
    
    if not isinstance(text, str):
        raise ValidationError("Text must be a string")
    
    text = text.strip()
    if not text:
        raise ValidationError("Text cannot be empty or whitespace")
    
    if len(text) < 10:
        raise ValidationError(f"Text too short: {len(text)} chars (minimum: 10)")
    
    if len(text) > 5000:
        raise ValidationError(f"Text too long: {len(text)} chars (maximum: 5000)")
    
    # Validate duration
    if not duration:
        raise ValidationError("Duration is required")
    
    if duration not in ["short", "medium"]:
        raise ValidationError(
            f"Invalid duration: '{duration}'. Must be 'short' or 'medium'"
        )
    
    # Convert string to Duration enum
    duration_enum = Duration.SHORT if duration == "short" else Duration.MEDIUM
    
    # Validate instruction (optional)
    if instruction is not None:
        if not isinstance(instruction, str):
            raise ValidationError("Instruction must be a string")
        
        if len(instruction) > 2000:
            raise ValidationError(
                f"Instruction too long: {len(instruction)} chars (maximum: 2000)"
            )
    
    # Validate avatar_enabled
    if not isinstance(avatar_enabled, bool):
        raise ValidationError("avatar_enabled must be a boolean")
    
    logger.info(f"Aggregation request validated: {len(text)} chars, {duration}, avatar={avatar_enabled}")
    
    # ========================================================================
    # Delegate to Orchestrator
    # ========================================================================
    
    try:
        result = await orchestrate_aggregation(
            text=text,
            duration=duration_enum,
            instruction=instruction,
            avatar_enabled=avatar_enabled
        )
        return result
    
    except AggregationError:
        # Re-raise aggregation errors as-is
        raise
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected aggregation error: {e}")
        raise AggregationError(
            f"Unexpected aggregation failure: {e}",
            component="aggregation",
            original_error=e
        )


# Export public interface
__all__ = ["aggregate", "AggregationError", "ValidationError"]
