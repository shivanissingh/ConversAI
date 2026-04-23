"""
Topic Controller - API Layer for /api/explain/topic

"Topic Mode": the user provides a topic string (e.g. "Explain quantum computing")
instead of pre-existing text.  This controller:

  1. Calls Gemini to expand the topic into a rich 200-400 word source text.
  2. Passes that generated text through the EXACT same aggregate() pipeline
     used by /api/explain — no duplication of logic.
  3. Returns the identical response schema so the frontend can reuse the
     same handler.
"""

import httpx
from fastapi import HTTPException

from src.shared.types import TopicRequest
from src.shared.config import settings
from src.shared.logger import logger
from src.engines.aggregation import aggregate, AggregationError, ValidationError


# ---------------------------------------------------------------------------
# Gemini endpoint (mirrors narrator.py / planner.py pattern)
# ---------------------------------------------------------------------------
_GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

_TOPIC_EXPANSION_SYSTEM = (
    "You are a knowledgeable educator. "
    "When given a topic or question, write a clear, accurate, engaging explanation "
    "in flowing paragraphs. Never use bullet points, headers, or numbered lists. "
    "Write for an educated adult audience."
)


async def _generate_topic_text(topic: str) -> str:
    """
    Use Gemini to expand a short topic string into a 200-400 word source text
    suitable for passing through the ConversAI explanation pipeline.

    Args:
        topic: Raw topic string from the user (e.g. "Explain quantum computing")

    Returns:
        Generated source text (plain prose, 200-400 words)

    Raises:
        ValueError: If Gemini fails or returns an unusably short response
    """
    user_prompt = f"""Write a comprehensive, informative explanation of: {topic}

Requirements:
- 200-400 words
- Factually accurate
- Include key concepts, how it works, and real-world applications
- Write as if explaining to an educated adult
- Do NOT use bullet points or headers, write in flowing paragraphs
- This text will be further transformed into a narrated explanation

Return only the text, no meta-commentary."""

    url = f"{_GEMINI_API_BASE}/{settings.gemini_model}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": _TOPIC_EXPANSION_SYSTEM}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.6,   # Factual accuracy > creativity for source text
            "topP": 0.85,
        },
    }
    params = {"key": settings.gemini_api_key}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                json=payload,
                params=params,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            result = response.json()

        candidates = result.get("candidates", [])
        if not candidates:
            raise ValueError("Gemini returned no candidates for topic expansion")

        parts = candidates[0].get("content", {}).get("parts", [])
        text = parts[0].get("text", "").strip() if parts else ""

        if len(text) < 100:
            raise ValueError(
                f"Gemini topic expansion too short ({len(text)} chars); "
                "may have been blocked or failed"
            )

        logger.info(
            f"Topic expansion: '{topic[:60]}' → {len(text)} chars / "
            f"~{len(text.split())} words"
        )
        return text

    except httpx.HTTPStatusError as e:
        body = e.response.text if hasattr(e, "response") else str(e)
        raise ValueError(f"Gemini API error ({e.response.status_code}): {body}")
    except httpx.HTTPError as e:
        raise ValueError(f"Gemini connection error during topic expansion: {e}")


# ---------------------------------------------------------------------------
# Controller
# ---------------------------------------------------------------------------

class TopicController:
    @staticmethod
    async def process_topic(request: TopicRequest) -> dict:
        """
        Handle POST /api/explain/topic.

        Thin wrapper:
          1. Validate & clean the topic string
          2. Generate source text via Gemini
          3. Run the full aggregate() pipeline (identical to /api/explain)
          4. Return the result unchanged

        Args:
            request: TopicRequest — topic, duration, instruction, avatarEnabled

        Returns:
            Unified multimodal response (same schema as /api/explain)

        Raises:
            HTTPException 400: Validation failure
            HTTPException 500: Generation or pipeline failure
        """
        # --- Input sanitisation -------------------------------------------
        topic = request.topic.strip()
        if len(topic) < 5:
            raise HTTPException(
                status_code=400,
                detail="Topic must be at least 5 characters after trimming whitespace.",
            )
        if len(topic) > 200:
            raise HTTPException(
                status_code=400,
                detail="Topic must be 200 characters or fewer.",
            )

        logger.info(
            f"Topic request: '{topic[:80]}', duration={request.duration.value}, "
            f"avatar={request.avatarEnabled}"
        )

        # --- Step 1: Expand topic → source text ---------------------------
        try:
            source_text = await _generate_topic_text(topic)
        except ValueError as e:
            logger.error(f"Topic expansion failed: {e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Topic expansion failed",
                    "message": str(e),
                    "component": "topic_expansion",
                },
            )

        # --- Step 2: Run the full pipeline --------------------------------
        # Append the original topic as a framing instruction so the
        # explanation engine knows to tailor its narration to it.
        combined_instruction = request.instruction or ""
        topic_hint = f"The user asked about: {topic}. Explain it clearly and engagingly."
        full_instruction = (
            f"{combined_instruction.strip()} {topic_hint}".strip()
        )

        try:
            result = await aggregate(
                text=source_text,
                duration=request.duration.value,
                instruction=full_instruction,
                avatar_enabled=request.avatarEnabled,
            )
        except ValidationError as e:
            logger.warning(f"Topic pipeline validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except AggregationError as e:
            logger.error(f"Topic pipeline aggregation failed: component={e.component}, error={e}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Explanation pipeline failed",
                    "component": e.component,
                    "message": str(e),
                },
            )
        except Exception as e:
            logger.error(f"Topic pipeline unexpected error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

        logger.info(
            f"Topic request complete: {len(result['segments'])} segments, "
            f"{result['audioDuration']:.1f}s audio, "
            f"visuals: {result['metadata']['visualStats']['generated']}/"
            f"{result['metadata']['visualStats']['requested']}"
        )

        # Attach the generated source text so the frontend can surface it
        # (optional, doesn't break existing frontend handler)
        result["topicSourceText"] = source_text

        return result
