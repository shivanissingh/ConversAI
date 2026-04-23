"""
Explanation Engine - Structurer Module

Responsible for:
- Duration constraints and configuration
- Prompt template assembly
- Story-driven structure definition

Follows the frozen design: docs/EXPLANATION_ENGINE_DESIGN.md
"""

from dataclasses import dataclass
from typing import Optional
from src.shared.types import Duration


@dataclass
class DurationConfig:
    """Configuration for a specific duration mode."""
    duration_description: str
    word_min: int
    word_max: int
    segment_min: int
    segment_max: int
    concept_count: int
    setup_pct: int
    insight_pct: int
    takeaway_pct: int
    words_per_segment: str
    target_duration_min: int  # seconds
    target_duration_max: int  # seconds


# Duration configuration constants following the design spec
DURATION_CONFIGS: dict[str, DurationConfig] = {
    "short": DurationConfig(
        duration_description="30-40 seconds, quick overview",
        word_min=75,
        word_max=100,
        segment_min=2,
        segment_max=4,
        concept_count=2,
        setup_pct=20,
        insight_pct=60,
        takeaway_pct=20,
        words_per_segment="25-35",
        target_duration_min=30,
        target_duration_max=40,
    ),
    "medium": DurationConfig(
        duration_description="60-90 seconds, full explanation with examples",
        word_min=150,
        word_max=225,
        segment_min=4,
        segment_max=7,
        concept_count=3,
        setup_pct=15,
        insight_pct=70,
        takeaway_pct=15,
        words_per_segment="30-45",
        target_duration_min=60,
        target_duration_max=90,
    ),
}


# System prompt - static, used for all requests
SYSTEM_PROMPT = """You are the Explanation Engine for ConversAI, a system that transforms text into engaging narrated explanations.

YOUR ROLE:
- Transform dense text into a story-driven narration
- Focus on core ideas only (2-4 concepts maximum)
- Make content accessible to the specified audience level
- Write for SPEAKING, not reading

STRICT OUTPUT FORMAT:
You MUST return a valid JSON object with this exact structure:
{
  "narration": "The complete narration text as a single string",
  "segments": [
    {
      "id": "segment_1",
      "text": "The narration text for this segment only",
      "startTime": 0,
      "endTime": <calculated_end_time>
    }
  ],
  "metadata": {
    "concepts": ["concept1", "concept2"],
    "difficulty": "beginner" | "intermediate",
    "estimatedDuration": <total_seconds>
  }
}

NARRATION RULES:
1. Follow the structure: SETUP → INSIGHT → TAKEAWAY
2. Use natural, conversational language
3. Include 1-2 concrete analogies or examples
4. Avoid jargon unless essential (then define it)
5. End with a memorable takeaway

SEGMENT RULES:
1. Each segment = one visual scene
2. Break at natural thought boundaries
3. Timing: ~150 words = 60 seconds
4. startTime of segment N = endTime of segment N-1
5. First segment always starts at 0

FORBIDDEN:
- Do NOT include everything from the input
- Do NOT use bullet points in narration
- Do NOT make segments too short (<5 sec) or too long (>20 sec)
- Do NOT include meta-commentary like "In this explanation..."
"""


# User prompt template with placeholders
USER_PROMPT_TEMPLATE = """TRANSFORM THE FOLLOWING TEXT INTO A NARRATED EXPLANATION.

--- INPUT TEXT ---
{text}
--- END INPUT ---

CONSTRAINTS:
- Duration: {duration} ({duration_description})
- Word Budget: {word_min}-{word_max} words total
- Segment Count: {segment_min}-{segment_max} segments
{instruction_block}

OUTPUT REQUIREMENTS:
1. Extract the {concept_count} most important concepts
2. Structure as: Setup ({setup_pct}%) → Insight ({insight_pct}%) → Takeaway ({takeaway_pct}%)
3. Each segment should be {words_per_segment} words on average
4. Calculate timings at 150 words per minute speaking rate

Return ONLY the JSON object. No additional text."""


class Structurer:
    """
    Builds prompts with proper duration constraints for the Explanation Engine.
    """

    @staticmethod
    def get_duration_config(duration: Duration) -> DurationConfig:
        """Get the configuration for a specific duration mode."""
        return DURATION_CONFIGS[duration.value]

    @staticmethod
    def build_instruction_block(instruction: Optional[str]) -> str:
        """Build the instruction block for the prompt."""
        if not instruction:
            return ""
        
        return f"""
ADDITIONAL USER INSTRUCTION:
{instruction}

Apply this instruction to the tone, complexity, and style of the narration.
"""

    @staticmethod
    def build_prompt(text: str, duration: Duration, instruction: Optional[str]) -> tuple[str, str]:
        """
        Build the complete prompt for the LLM.
        
        Args:
            text: The input text to transform
            duration: Duration mode (short/medium)
            instruction: Optional user instruction
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        config = Structurer.get_duration_config(duration)
        instruction_block = Structurer.build_instruction_block(instruction)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            text=text,
            duration=duration.value,
            duration_description=config.duration_description,
            word_min=config.word_min,
            word_max=config.word_max,
            segment_min=config.segment_min,
            segment_max=config.segment_max,
            instruction_block=instruction_block,
            concept_count=config.concept_count,
            setup_pct=config.setup_pct,
            insight_pct=config.insight_pct,
            takeaway_pct=config.takeaway_pct,
            words_per_segment=config.words_per_segment,
        )

        return SYSTEM_PROMPT, user_prompt

    @staticmethod
    def get_constraints(duration: Duration) -> dict:
        """
        Get validation constraints for the output.
        
        Returns dict with min/max values for validation.
        """
        config = Structurer.get_duration_config(duration)
        return {
            "word_min": config.word_min,
            "word_max": int(config.word_max * 1.2),  # 20% tolerance
            "segment_min": config.segment_min,
            "segment_max": config.segment_max,
            "duration_min": config.target_duration_min,
            "duration_max": config.target_duration_max,
        }
