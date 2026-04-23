"""
Visual Engine - Public Interface

This module provides the facade for the Visual Engine.
It orchestrates the planner and generator components to transform
narration segments into Gemini-powered visual card data.

The visual cards are rendered as beautiful animated slides by the frontend,
replacing the old Stable Diffusion image generation approach.

Usage:
    from src.engines.visual import generate_visuals
    
    result = await generate_visuals(segments, metadata)
"""

from typing import List, Optional
from src.shared.types import Segment
from src.shared.config import settings
from src.shared.logger import logger
from src.engines.visual.planner import plan_visuals
from src.engines.visual.generator import generate_visuals_async


class VisualEngineError(Exception):
    """Base exception for Visual Engine errors."""
    pass


class VisualEngine:
    """
    Main facade for the Visual Engine.
    
    Orchestrates the pipeline:
    1. Planner prepares segment data and timing info
    2. Generator calls Gemini to create structured visual cards
    3. Frontend renders cards as animated slides
    """
    
    def __init__(self):
        """Initialize the Visual Engine."""
        # No HF API key needed anymore — we use Gemini (already validated by narrator)
        pass
    
    async def generate(self, segments: List[Segment], metadata: dict) -> dict:
        """
        Generate visual cards for explanation segments.
        
        Args:
            segments: List of narration segments from Explanation Engine
            metadata: Metadata with concepts and difficulty
            
        Returns:
            {
                "visuals": List[Visual],
                "metadata": {
                    "totalRequested": int,
                    "totalGenerated": int,
                    "failures": List[dict]  # Optional
                }
            }
            
        Raises:
            VisualEngineError: If critical failure prevents any visual generation
        """
        try:
            # Step 1: Plan visuals (prepare timing and segment data)
            logger.info(f"Planning visuals for {len(segments)} segments")
            visual_plans = plan_visuals(segments, metadata)
            logger.info(f"Generated {len(visual_plans)} visual plans")
            
            # Step 2: Generate visual cards via Gemini (single API call)
            logger.info("Starting visual card generation via Gemini API")
            result = await generate_visuals_async(visual_plans, segments, metadata)
            
            logger.info(
                f"Visual generation complete: {result['metadata']['totalGenerated']}/{result['metadata']['totalRequested']} successful"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Visual Engine failed: {e}")
            raise VisualEngineError(f"Visual generation failed: {e}")


# Singleton instance
_engine: Optional[VisualEngine] = None


def _get_engine() -> VisualEngine:
    """Get or create the engine singleton."""
    global _engine
    if _engine is None:
        _engine = VisualEngine()
    return _engine


async def generate_visuals(segments: List[Segment], metadata: dict) -> dict:
    """
    Public interface: Generate visuals for explanation segments.
    
    Args:
        segments: List of narration segments
        metadata: Metadata from Explanation Engine
        
    Returns:
        {
            "visuals": List[Visual],
            "metadata": {
                "totalRequested": int,
                "totalGenerated": int,
                "failures": List[dict]  # Optional
            }
        }
    """
    engine = _get_engine()
    return await engine.generate(segments, metadata)
