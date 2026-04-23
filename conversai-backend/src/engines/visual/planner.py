"""
Visual Planner Module — Gemini Image Prompt Generator + Pollinations.ai

Architecture:
  1. Gemini LLM generates a vivid, specific image prompt for each segment
  2. We build a Pollinations.ai URL from the prompt (free, no API key)
  3. Frontend renders the image immediately from URL — no download/encode needed

Why Pollinations.ai:
  - Completely free, no API key, no rate limits for reasonable usage
  - URL-based: https://image.pollinations.ai/prompt/{encoded_prompt}
  - Supports width/height parameters, generates 16:9 landscape
  - Images are cached by Pollinations on their CDN

Why Gemini for prompts (not direct image):
  - Gemini understands the educational context and generates SPECIFIC prompts
  - Avoids generic "a blue background with text" type visuals
  - Creates cinematic, educational imagery tailored to the topic
"""

import json
import re
import urllib.parse
import httpx
from typing import List

from src.shared.types import Segment, VisualType
from src.shared.config import settings
from src.shared.logger import logger


# Visual type mapping (kept for backward compat with aggregation)
CARD_TYPE_MAP = {
    "concept": VisualType.ABSTRACT_CONCEPT,
    "process": VisualType.PROCESS_FLOW,
    "comparison": VisualType.COMPARISON,
    "metaphor": VisualType.METAPHOR,
    "structure": VisualType.STRUCTURE_DIAGRAM,
    "summary": VisualType.ICON_COMPOSITION,
}

ACCENT_COLORS = [
    "#6C63FF", "#00C9A7", "#FF6B6B", "#4ECDC4",
    "#FFD93D", "#6BCB77", "#FF8C42",
]

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Pollinations base URL
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt"

IMAGE_PROMPT_SYSTEM = """You are a visual director creating images for an educational explainer video.

For each narration segment, create an image prompt that DIRECTLY illustrates what is being SAID in that specific segment - not the general topic, but the exact sentence or idea.

Rules:
1. The image must show what the narration sentence is DESCRIBING, not just be related to the topic
2. Be highly specific - include concrete visual elements that match the narration
3. Photorealistic cinematic style, 16:9 format, dramatic lighting
4. No text in images
5. Think: "If I was making a documentary, what exact shot would play while this sentence is spoken?"

Return a JSON array. Each object must have:
- segmentId: the segment id
- imagePrompt: 2-3 sentence detailed scene description that specifically illustrates the narration text
- headline: 4-6 word overlay text that captures the segment's main idea
- style: one of "cinematic", "photorealistic", "3d_render", "illustration"

Example: If narration says "Imagine two magic coins that always land on opposite sides no matter how far apart they are"
Good prompt: "Two glowing golden coins floating in deep space, light years apart, one showing heads in warm gold light while simultaneously the other flips to tails in matching warm light, connected by visible quantum energy threads, photorealistic, dramatic space backdrop"
Bad prompt: "Abstract quantum physics concept"

Focus on CONCRETE, SPECIFIC visualization of the exact sentence being narrated."""


async def generate_image_prompts_via_gemini(
    segments: List[Segment],
    metadata: dict
) -> List[dict]:
    """
    Use Gemini LLM to generate vivid image prompts for each segment.
    Then builds Pollinations.ai URLs for immediate rendering.

    Returns list of dicts with imageUrl, imagePrompt, headline per segment.
    """
    concepts = metadata.get("concepts", [])
    difficulty = metadata.get("difficulty", "beginner")

    # Build a structured list so Gemini receives the FULL narration text for each segment
    segment_objects = []
    for i, seg in enumerate(segments):
        # Derive per-segment duration safely
        duration = round(
            (getattr(seg, "endTime", 0) or 0) - (getattr(seg, "startTime", 0) or 0),
            1
        )
        segment_objects.append({
            "segmentId": f"segment_{i + 1}",
            "narrationText": seg.text,
            "concept": concepts[i] if i < len(concepts) else (concepts[0] if concepts else "educational content"),
            "segmentDuration": duration,
        })

    import json as _json
    segments_json = _json.dumps(segment_objects, ensure_ascii=False, indent=2)

    user_prompt = f"""Generate image prompts for each narration segment below.

OVERALL TOPIC: {', '.join(concepts) if concepts else 'General educational content'}
DIFFICULTY: {difficulty}
NUMBER OF SEGMENTS: {len(segments)}

SEGMENTS (each contains the EXACT narration text to visualize):
{segments_json}

For each segment, base the imagePrompt SPECIFICALLY on the narrationText field — visualize what is literally being said.
Return a JSON array with exactly {len(segments)} objects.
Return ONLY the JSON array. No additional text."""

    url = f"{GEMINI_API_BASE}/{settings.gemini_model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": IMAGE_PROMPT_SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "topP": 0.85,
            "responseMimeType": "application/json"
        }
    }
    params = {"key": settings.gemini_api_key}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url, json=payload, params=params,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()

            candidates = result.get("candidates", [])
            if not candidates:
                raise Exception("Gemini returned no candidates")

            parts = candidates[0].get("content", {}).get("parts", [])
            raw_text = parts[0].get("text", "") if parts else ""

            image_data = _parse_image_prompts(raw_text)
            logger.info(f"Gemini generated {len(image_data)} image prompts")

            # Build Pollinations URLs
            for item in image_data:
                prompt = item.get("imagePrompt", "educational concept visualization")
                style = item.get("style", "cinematic")
                full_prompt = f"{prompt}, {style} style, 16:9 aspect ratio, high quality, ultra detailed, no text"
                encoded = urllib.parse.quote(full_prompt)
                item["imageUrl"] = (
                    f"{POLLINATIONS_BASE}/{encoded}"
                    f"?width=768&height=432&seed={abs(hash(prompt)) % 9999}"
                )

            return image_data

    except Exception as e:
        logger.error(f"Gemini image prompt generation failed: {e}")
        return _generate_fallback_prompts(segments)


def _parse_image_prompts(raw_text: str) -> List[dict]:
    """Parse JSON array from Gemini response."""
    try:
        result = json.loads(raw_text)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "prompts" in result:
            return result["prompts"]
        return [result]
    except json.JSONDecodeError:
        pass

    json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    json_match = re.search(r"\[.*\]", raw_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    raise Exception("Could not parse image prompts from Gemini response")


def _generate_fallback_prompts(segments: List[Segment]) -> List[dict]:
    """Fallback: use generic educational visuals when Gemini fails."""
    fallbacks = [
        ("Abstract glowing network of interconnected nodes floating in dark blue space, "
         "representing information flow and connectivity", "3d_render"),
        ("Close-up of a human brain with glowing synapses firing, concept of learning "
         "and neural processing, cinematic depth", "cinematic"),
        ("Futuristic data visualization with flowing light streams in purple and teal, "
         "representing digital transformation", "cinematic"),
        ("Clean minimal workspace with holographic displays showing flowing data, "
         "soft studio lighting, ultra modern", "3d_render"),
        ("Abstract geometric shapes forming a complex pattern, representing structured "
         "thinking and organization", "illustration"),
    ]

    results = []
    for i, seg in enumerate(segments):
        prompt, style = fallbacks[i % len(fallbacks)]
        encoded = urllib.parse.quote(f"{prompt}, {style} style, high quality, no text")
        results.append({
            "segmentId": f"segment_{i+1}",
            "imagePrompt": prompt,
            "style": style,
            "headline": f"Concept {i+1}",
            "imageUrl": (
                f"{POLLINATIONS_BASE}/{encoded}"
                f"?width=768&height=432&seed={i * 42}"
            )
        })
    return results


# Keep old function name for backward compatibility (now just delegates)
async def generate_visual_cards_via_gemini(segments, metadata):
    """Backward-compat alias — now generates image prompts."""
    return await generate_image_prompts_via_gemini(segments, metadata)


def _generate_fallback_cards(segments, metadata):
    """Backward-compat alias."""
    return _generate_fallback_prompts(segments)


def plan_visuals(segments: List[Segment], metadata: dict) -> List[dict]:
    """
    Create visual plans with timing info for all segments.
    Actual image prompt generation happens in generate_visuals_async().
    """
    visual_plans = []
    for i, segment in enumerate(segments):
        visual_plans.append({
            "segmentId": f"segment_{i + 1}",
            "segment": segment,
            "startTime": segment.startTime,
            "endTime": segment.endTime,
            "metadata": {
                "concept": metadata.get("concepts", [""])[0] if metadata.get("concepts") else "",
                "complexity": "simple" if metadata.get("difficulty") == "beginner" else "moderate"
            }
        })
    return visual_plans
