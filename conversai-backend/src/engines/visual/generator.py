"""
Visual Generator Module — Image Download & Base64 Encoding

Generates AI images via Pollinations.ai (free, URL-based, no API key).
Gemini LLM creates the vivid image prompt; Pollinations renders the image.
The backend downloads the image and returns it as a base64 data URI so the
frontend never makes a direct Pollinations request (avoiding 403s from
retry-parameter cache misses).

Flow:
  Gemini prompt generation → Pollinations.ai URL → Backend download → base64 → Frontend img src
"""

import asyncio
import base64
import time
from typing import List

import httpx

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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _download_image_as_base64(
    url: str,
    session: httpx.AsyncClient,
    *,
    is_retry: bool = False,
) -> str | None:
    """
    Download an image from *url* and return it as a base64 data URI.

    Returns:
        str  - base64 data URI on success
        None - on any failure (non-200, network error, etc.)

    Raises:
        _RateLimitError   - Pollinations returned 429 (first attempt only)
        _TransientError   - timeout / connection error (first attempt only)
    """
    try:
        # Pollinations generates images on-the-fly — complex prompts at 768×432
        # can take 50-70s to render. 90s gives ample headroom.
        response = await session.get(url, timeout=90.0, follow_redirects=True)
        if response.status_code == 200:
            image_bytes = response.content
            encoded = base64.b64encode(image_bytes).decode("utf-8")
            content_type = response.headers.get("content-type", "image/jpeg")
            return f"data:{content_type};base64,{encoded}"
        elif response.status_code == 429 and not is_retry:
            raise _RateLimitError(f"Pollinations 429 on {url[:80]}")
        else:
            logger.warning(f"Pollinations returned {response.status_code} for {url[:80]}")
            return None
    except (_RateLimitError, _TransientError):
        raise  # propagate so caller can retry
    except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
        if not is_retry:
            raise _TransientError(f"Network error on {url[:80]}: {e}")
        logger.warning(f"Failed to download image from {url[:80]}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Failed to download image from {url[:80]}: {e}")
        return None


class _RateLimitError(Exception):
    """Internal signal: Pollinations returned 429 — caller should back off."""
    pass


class _TransientError(Exception):
    """Internal signal: timeout / connection error — caller should back off and retry."""
    pass


def _generate_svg_placeholder(concept: str, headline: str) -> str:
    """
    Generate a simple SVG placeholder image as a base64 data URI.
    Used when the Pollinations download fails.
    """
    # Sanitise to avoid broken SVG XML
    safe_concept = str(concept).upper().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_headline = str(headline).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    svg = f'''<svg width="1280" height="720" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e1b4b;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#312e81;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="1280" height="720" fill="url(#bg)"/>
  <text x="640" y="320" font-family="Arial, sans-serif" font-size="48" font-weight="bold"
        fill="white" text-anchor="middle" opacity="0.9">{safe_concept}</text>
  <text x="640" y="400" font-family="Arial, sans-serif" font-size="28"
        fill="#a5b4fc" text-anchor="middle" opacity="0.8">{safe_headline}</text>
</svg>'''
    svg_bytes = svg.encode("utf-8")
    encoded = base64.b64encode(svg_bytes).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


# ---------------------------------------------------------------------------
# Visual builders
# ---------------------------------------------------------------------------

def _create_visual_from_image_data(image_data: dict, plan: dict, base64_url: str) -> dict:
    """
    Create a visual object from Gemini image prompt data + the already-downloaded base64 URI.

    Args:
        image_data: Dict with imageUrl, imagePrompt, headline, style
        plan: Visual plan with timing info
        base64_url: base64 data URI of the downloaded image (or SVG fallback)

    Returns:
        Visual dict with url set to the base64 data URI
    """
    return {
        "url": base64_url,
        "startTime": plan["startTime"],
        "endTime": plan["endTime"],
        "type": VisualType.ABSTRACT_CONCEPT,
        "imagePrompt": image_data.get("imagePrompt", ""),  # For debugging
        "headline": image_data.get("headline", ""),        # Overlay text
        "style": image_data.get("style", "cinematic"),
        "metadata": {
            "segmentId": plan["segmentId"],
            "concept": plan["metadata"]["concept"],
            "generationMethod": "pollinations_ai_base64",
        },
    }


def _create_fallback_visual(plan: dict, index: int) -> dict:
    """Create an SVG-based fallback visual when generation fails for a segment."""
    concept = plan["metadata"].get("concept", "Key Concept")
    headline = "Key Concept"
    svg_data_uri = _generate_svg_placeholder(concept, headline)
    return {
        "url": svg_data_uri,
        "startTime": plan["startTime"],
        "endTime": plan["endTime"],
        "type": VisualType.ABSTRACT_CONCEPT,
        "headline": headline,
        "metadata": {
            "segmentId": plan["segmentId"],
            "concept": concept,
            "error": "generation_failed",
            "generationMethod": "svg_placeholder",
        },
    }


# ---------------------------------------------------------------------------
# Main async entrypoint
# ---------------------------------------------------------------------------

async def generate_visuals_async(visual_plans: List[dict], segments, metadata: dict) -> dict:
    """
    Generate base64-encoded images for all segments.

    Steps:
      1. Ask Gemini to generate vivid image prompts for each segment
      2. Build Pollinations.ai URLs from those prompts
      3. Download all images sequentially with rate-limit backoff
      4. Convert each image to a base64 data URI (SVG fallback on error)
      5. Return visual objects with base64 url ready for frontend img src

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

        prompt_time = time.time() - start_time
        logger.info(f"Image prompts generated in {prompt_time:.2f}s — downloading images from Pollinations")

        # Collect the Pollinations URLs we need to download
        # image_data_list items have an 'imageUrl' key built by the planner
        download_items = []
        for i, plan in enumerate(visual_plans):
            if i < len(image_data_list):
                download_items.append({
                    "index": i,
                    "plan": plan,
                    "image_data": image_data_list[i],
                    "url": image_data_list[i].get("imageUrl", ""),
                })
            else:
                download_items.append({
                    "index": i,
                    "plan": plan,
                    "image_data": None,
                    "url": None,
                })

        # ------------------------------------------------------------------
        # Sequential download with inter-request gap + retry on 429/timeout
        #
        # Pollinations free tier:
        #   - Generates images on-the-fly (complex prompts can take 50-70s)
        #   - Rate-limits concurrent / rapid-fire bursts to 429
        #
        # Strategy: download ONE image at a time with a 10s cooldown gap.
        # Per-request timeout is 90s to let Pollinations finish rendering.
        # On 429 or timeout, wait 10s and retry once.
        # ------------------------------------------------------------------
        INTER_REQUEST_DELAY   = 10.0  # seconds between sequential requests
        RETRY_DELAY_429       = 10.0  # seconds to wait before retry on 429 rate limit
        RETRY_DELAY_TRANSIENT = 10.0  # seconds to wait before retry on timeout/connection error

        logger.info(f"Downloading {len(download_items)} images sequentially ({INTER_REQUEST_DELAY}s gap, 90s timeout per image)…")
        base64_results: list[str | Exception | None] = []

        async with httpx.AsyncClient(timeout=120.0) as client:
            for idx, item in enumerate(download_items):
                if idx > 0:
                    logger.info(f"  Waiting {INTER_REQUEST_DELAY}s before next image request...")
                    await asyncio.sleep(INTER_REQUEST_DELAY)

                url = item["url"]
                if not url:
                    base64_results.append(None)
                    continue

                logger.info(f"Downloading image {idx+1}/{len(download_items)} for {item['plan']['segmentId']}")

                try:
                    result = await _download_image_as_base64(url, client)
                    base64_results.append(result)
                except _RateLimitError as first_err:
                    logger.warning(
                        f"  Segment {idx+1}: 429 rate limit, waiting {RETRY_DELAY_429}s before retry..."
                    )
                    await asyncio.sleep(RETRY_DELAY_429)
                    try:
                        result = await _download_image_as_base64(url, client, is_retry=True)
                        base64_results.append(result)
                    except Exception as retry_err:
                        logger.warning(f"  Segment {idx+1}: retry also failed: {retry_err}")
                        base64_results.append(None)
                except _TransientError as first_err:
                    logger.warning(
                        f"  Segment {idx+1}: timeout/connection error, retrying after {RETRY_DELAY_TRANSIENT}s..."
                    )
                    await asyncio.sleep(RETRY_DELAY_TRANSIENT)
                    try:
                        result = await _download_image_as_base64(url, client, is_retry=True)
                        base64_results.append(result)
                    except Exception as retry_err:
                        logger.warning(f"  Segment {idx+1}: retry also failed: {retry_err}")
                        base64_results.append(None)
                except Exception as exc:
                    base64_results.append(exc)

        download_time = time.time() - start_time - prompt_time
        successful_downloads = sum(1 for r in base64_results if isinstance(r, str) and r is not None)
        logger.info(
            f"Image downloads completed: {successful_downloads}/{len(download_items)} succeeded "
            f"in {download_time:.2f}s"
        )

        # Assemble visuals — fall back to SVG placeholder on any failure
        for item, result in zip(download_items, base64_results):
            i = item["index"]
            plan = item["plan"]

            if isinstance(result, Exception) or result is None:
                # Download failed → use SVG placeholder
                concept = plan["metadata"].get("concept", "Key Concept")
                headline = item["image_data"].get("headline", "Key Concept") if item["image_data"] else "Key Concept"
                svg_uri = _generate_svg_placeholder(concept, headline)

                if item["image_data"]:
                    visual = _create_visual_from_image_data(item["image_data"], plan, svg_uri)
                    visual["metadata"]["generationMethod"] = "svg_placeholder_fallback"
                else:
                    visual = _create_fallback_visual(plan, i)

                failures.append({
                    "segmentId": plan["segmentId"],
                    "reason": str(result) if isinstance(result, Exception) else "Download returned None",
                })
                logger.warning(f"  Segment {i+1}: download failed, using SVG placeholder")
            else:
                visual = _create_visual_from_image_data(item["image_data"], plan, result)
                visual["metadata"]["promptTime"] = round(prompt_time, 2)
                logger.info(f"  Segment {i+1}: downloaded OK ({len(result)} chars base64)")

            visuals.append(visual)

    except Exception as e:
        logger.error(f"Visual generation failed: {e}")
        for i, plan in enumerate(visual_plans):
            visuals.append(_create_fallback_visual(plan, i))
            failures.append({
                "segmentId": plan["segmentId"],
                "reason": f"Generation failed: {str(e)}",
            })

    successful = [v for v in visuals if not v.get("metadata", {}).get("error")]
    response = {
        "visuals": visuals,
        "metadata": {
            "totalRequested": len(visual_plans),
            "totalGenerated": len(successful),
            "generationMethod": "pollinations_ai_base64",
        },
    }
    if failures:
        response["metadata"]["failures"] = failures

    total_time = time.time() - start_time
    logger.info(
        f"Visual generation complete: {len(successful)}/{len(visual_plans)} successful "
        f"in {total_time:.2f}s (images embedded as base64)"
    )
    return response


def generate_visuals(visual_plans: List[dict]) -> dict:
    """Synchronous stub — real generation uses generate_visuals_async()."""
    return {
        "visuals": [],
        "metadata": {
            "totalRequested": len(visual_plans),
            "totalGenerated": 0,
        },
    }
