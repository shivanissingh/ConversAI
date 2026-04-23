"""
Visual Generator Module — Image URL Generation

Generates AI images via Pollinations.ai (free, URL-based, no API key).
Gemini LLM creates the vivid image prompt; Pollinations renders the image.

Flow:
  Gemini prompt generation → Pollinations.ai URL → Frontend img src
"""

import time
from typing import List

from src.shared.logger import logger
from src.shared.types import VisualType
from src.engines.visual.planner import (
    generate_image_prompts_via_gemini,
    _generate_fallback_prompts,
    CARD_TYPE_MAP,
    ACCENT_COLORS,
)


class GeneratorError(Exception):
    """Exception raised when visual generation fails."""
    pass


def _create_visual_from_image_data(image_data: dict, plan: dict) -> dict:
    """
    Create a visual object from Gemini image prompt data + Pollinations URL.

    Args:
        image_data: Dict with imageUrl, imagePrompt, headline, style
        plan: Visual plan with timing info

    Returns:
        Visual dict with url pointing to Pollinations.ai image
    """
    return {
        "url": image_data.get("imageUrl"),          # Real image URL
        "startTime": plan["startTime"],
        "endTime": plan["endTime"],
        "type": VisualType.ABSTRACT_CONCEPT,
        "imagePrompt": image_data.get("imagePrompt", ""),  # For debugging
        "headline": image_data.get("headline", ""),         # Overlay text
        "style": image_data.get("style", "cinematic"),
        "metadata": {
            "segmentId": plan["segmentId"],
            "concept": plan["metadata"]["concept"],
            "generationMethod": "pollinations_ai",
        }
    }


def _create_fallback_visual(plan: dict, index: int) -> dict:
    """Create a fallback visual when generation fails for a segment."""
    import urllib.parse
    prompt = (
        f"Abstract educational concept visualization, glowing nodes, "
        f"dark background, cinematic style, high quality"
    )
    encoded = urllib.parse.quote(f"{prompt}, no text")
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1280&height=720&nologo=true&seed={index * 37}"
    )
    return {
        "url": url,
        "startTime": plan["startTime"],
        "endTime": plan["endTime"],
        "type": VisualType.ABSTRACT_CONCEPT,
        "headline": "Key Concept",
        "metadata": {
            "segmentId": plan["segmentId"],
            "concept": plan["metadata"]["concept"],
            "error": "generation_failed",
            "generationMethod": "pollinations_fallback",
        }
    }


async def generate_visuals_async(visual_plans: List[dict], segments, metadata: dict) -> dict:
    """
    Generate Pollinations.ai image URLs for all segments.

    Steps:
      1. Ask Gemini to generate vivid image prompts for each segment
      2. Build Pollinations.ai URLs from those prompts
      3. Return visual objects with URL ready for frontend img src

    Args:
        visual_plans: List of visual plans from planner
        segments: Original segments for Gemini prompt
        metadata: Metadata from explanation engine

    Returns:
        {"visuals": [...], "metadata": {...}}
    """
    start_time = time.time()
    visuals = []
    failures = []

    try:
        logger.info(f"Generating image prompts for {len(segments)} segments via Gemini")
        image_data_list = await generate_image_prompts_via_gemini(segments, metadata)

        generation_time = time.time() - start_time
        logger.info(f"Image prompts generated in {generation_time:.2f}s — building Pollinations URLs")

        for i, plan in enumerate(visual_plans):
            if i < len(image_data_list):
                visual = _create_visual_from_image_data(image_data_list[i], plan)
                visual["metadata"]["promptTime"] = round(generation_time, 2)
                visuals.append(visual)
                logger.info(f"  Segment {i+1}: {visual['url'][:80]}...")
            else:
                visuals.append(_create_fallback_visual(plan, i))
                failures.append({
                    "segmentId": plan["segmentId"],
                    "reason": "No image data generated for this segment"
                })

    except Exception as e:
        logger.error(f"Visual generation failed: {e}")
        for i, plan in enumerate(visual_plans):
            visuals.append(_create_fallback_visual(plan, i))
            failures.append({
                "segmentId": plan["segmentId"],
                "reason": f"Generation failed: {str(e)}"
            })

    successful = [v for v in visuals if not v.get("metadata", {}).get("error")]
    response = {
        "visuals": visuals,
        "metadata": {
            "totalRequested": len(visual_plans),
            "totalGenerated": len(successful),
            "generationMethod": "pollinations_ai",
        }
    }
    if failures:
        response["metadata"]["failures"] = failures

    logger.info(f"Visual generation complete: {len(successful)}/{len(visual_plans)} successful")
    return response


def generate_visuals(visual_plans: List[dict]) -> dict:
    """Synchronous stub — real generation uses generate_visuals_async()."""
    return {
        "visuals": [],
        "metadata": {
            "totalRequested": len(visual_plans),
            "totalGenerated": 0,
        }
    }
