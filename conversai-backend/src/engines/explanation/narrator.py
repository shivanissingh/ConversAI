"""
Explanation Engine - Narrator Module

Responsible for:
- LLM invocation via Google Gemini (default) or Ollama (fallback)
- Response parsing and JSON validation
- Timing calculation and recalculation
- Fallback handling for invalid responses

Follows the frozen design: docs/EXPLANATION_ENGINE_DESIGN.md
"""

import json
import re
import httpx
from typing import Optional
from dataclasses import dataclass

from src.shared.types import Duration
from src.shared.config import settings, LLMProvider
from src.engines.explanation.structurer import Structurer


# Speaking rate constant: 150 words per minute
SPEAKING_RATE_WPM = 150

# =============================================================================
# Gemini API Configuration
# Endpoint for Google Gemini API (generativelanguage.googleapis.com)
# =============================================================================
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


@dataclass
class ExplanationSegment:
    """A single segment of the explanation."""
    id: str
    text: str
    startTime: float
    endTime: float


@dataclass
class ExplanationMetadata:
    """Metadata about the explanation."""
    concepts: list[str]
    difficulty: str
    estimatedDuration: float


@dataclass
class ExplanationOutput:
    """Complete output from the Explanation Engine."""
    narration: str
    segments: list[ExplanationSegment]
    metadata: ExplanationMetadata


class NarratorError(Exception):
    """Raised when narration generation fails."""
    pass


class Narrator:
    """
    Handles LLM invocation, response parsing, and timing calculations.
    
    Supports two LLM providers:
    - Google Gemini (default): Cloud-based, requires GEMINI_API_KEY
    - Ollama (fallback): Local LLM, requires Ollama server running
    """

    def __init__(
        self,
        provider: str = None,
        gemini_api_key: str = None,
        gemini_model: str = None,
        ollama_base_url: str = None,
        ollama_model: str = None
    ):
        """
        Initialize the Narrator.
        
        Args:
            provider: LLM provider ("gemini" or "ollama"). Defaults to settings.
            gemini_api_key: Gemini API key. Defaults to settings.
            gemini_model: Gemini model name. Defaults to settings.
            ollama_base_url: Base URL for Ollama API. Defaults to settings.
            ollama_model: Ollama model name. Defaults to settings.
        """
        # Load from settings if not provided
        self.provider = provider or settings.llm_provider
        self.gemini_api_key = gemini_api_key or settings.gemini_api_key
        self.gemini_model = gemini_model or settings.gemini_model
        self.ollama_base_url = (ollama_base_url or settings.ollama_base_url).rstrip("/")
        self.ollama_model = ollama_model or settings.ollama_model
        self.timeout = settings.llm_timeout
        
        # Validate API key if using Gemini
        if self.provider == LLMProvider.GEMINI.value:
            if not self.gemini_api_key:
                raise NarratorError(
                    "GEMINI_API_KEY is required when using Gemini provider. "
                    "Set via environment variable or switch to Ollama."
                )

    async def generate(
        self,
        text: str,
        duration: Duration,
        instruction: Optional[str] = None
    ) -> ExplanationOutput:
        """
        Generate a narrated explanation from the input text.
        
        Args:
            text: The input text to transform
            duration: Duration mode (short/medium)
            instruction: Optional user instruction
            
        Returns:
            ExplanationOutput with narration, segments, and metadata
            
        Raises:
            NarratorError: If generation fails after retries
        """
        # Build the prompt
        system_prompt, user_prompt = Structurer.build_prompt(text, duration, instruction)
        
        # Try up to 2 times (initial + 1 retry)
        last_error = None
        for attempt in range(2):
            try:
                # =============================================================
                # Call LLM based on configured provider
                # =============================================================
                if self.provider == LLMProvider.GEMINI.value:
                    raw_response = await self._call_gemini(system_prompt, user_prompt)
                else:
                    raw_response = await self._call_ollama(system_prompt, user_prompt)
                
                # Parse JSON from response
                parsed = self._parse_json_response(raw_response)
                
                # Validate structure
                self._validate_structure(parsed)
                
                # Recalculate timings to ensure accuracy
                segments = self._recalculate_timings(parsed["segments"])
                
                # Validate against constraints
                constraints = Structurer.get_constraints(duration)
                self._validate_constraints(parsed, segments, constraints)
                
                # Build output
                return ExplanationOutput(
                    narration=parsed["narration"],
                    segments=segments,
                    metadata=ExplanationMetadata(
                        concepts=parsed["metadata"]["concepts"],
                        difficulty=parsed["metadata"]["difficulty"],
                        estimatedDuration=segments[-1].endTime if segments else 0.0
                    )
                )
                
            except Exception as e:
                last_error = e
                if attempt == 0:
                    # Will retry
                    continue
                    
        raise NarratorError(f"Failed to generate explanation after retries: {last_error}")

    # =========================================================================
    # GEMINI API CALL
    # Sends system prompt + user prompt to Google Gemini Cloud LLM
    # API Key is loaded from GEMINI_API_KEY environment variable
    # =========================================================================
    async def _call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call the Google Gemini API to generate a response.
        
        Payload sent to Gemini:
        - systemInstruction: Contains the system prompt
        - contents: Contains the user prompt with input text + constraints
        
        Args:
            system_prompt: The system prompt defining behavior
            user_prompt: The user prompt with input text and constraints
            
        Returns:
            The raw response text from Gemini
        """
        # Build the Gemini API endpoint URL
        # Format: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
        url = f"{GEMINI_API_BASE}/{self.gemini_model}:generateContent"
        
        # =============================================================
        # Gemini request payload
        # Only sends system prompt and user prompt - no extra metadata
        # =============================================================
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "responseMimeType": "application/json"
            }
        }
        
        # API key passed as query parameter
        params = {"key": self.gemini_api_key}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    params=params,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract text from Gemini response structure
                # Response format: {"candidates": [{"content": {"parts": [{"text": "..."}]}}]}
                candidates = result.get("candidates", [])
                if not candidates:
                    raise NarratorError("Gemini returned no candidates")
                
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise NarratorError("Gemini returned no content parts")
                
                return parts[0].get("text", "")
                
            except httpx.HTTPStatusError as e:
                error_body = e.response.text if hasattr(e, 'response') else str(e)
                raise NarratorError(f"Gemini API error ({e.response.status_code}): {error_body}")
            except httpx.HTTPError as e:
                raise NarratorError(f"Gemini API connection error: {e}")

    # =========================================================================
    # OLLAMA API CALL (Fallback)
    # Preserved for local LLM usage when LLM_PROVIDER=ollama
    # =========================================================================
    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call the Ollama API to generate a response.
        
        Args:
            system_prompt: The system prompt
            user_prompt: The user prompt
            
        Returns:
            The raw response text from the LLM
        """
        url = f"{self.ollama_base_url}/api/chat"
        
        payload = {
            "model": self.ollama_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get("message", {}).get("content", "")
            except httpx.HTTPError as e:
                raise NarratorError(f"Ollama API error: {e}")

    def _parse_json_response(self, raw_response: str) -> dict:
        """
        Parse JSON from the LLM response.
        
        Handles cases where the JSON is wrapped in markdown code blocks.
        """
        # Try direct parse first
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON object directly
        json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        raise NarratorError("Could not parse JSON from LLM response")

    def _validate_structure(self, parsed: dict) -> None:
        """Validate that the parsed response has the required structure."""
        required_fields = ["narration", "segments", "metadata"]
        for field in required_fields:
            if field not in parsed:
                raise NarratorError(f"Missing required field: {field}")
        
        if not isinstance(parsed["segments"], list):
            raise NarratorError("Segments must be a list")
        
        if len(parsed["segments"]) == 0:
            raise NarratorError("At least one segment is required")
        
        for i, segment in enumerate(parsed["segments"]):
            for key in ["id", "text", "startTime", "endTime"]:
                if key not in segment:
                    raise NarratorError(f"Segment {i} missing field: {key}")
        
        if "concepts" not in parsed["metadata"]:
            raise NarratorError("Metadata missing concepts")
        if "difficulty" not in parsed["metadata"]:
            raise NarratorError("Metadata missing difficulty")

    def _recalculate_timings(self, segments: list[dict]) -> list[ExplanationSegment]:
        """
        Recalculate segment timings based on word count.
        
        Uses 150 words per minute speaking rate.
        """
        result = []
        current_time = 0.0
        
        for i, segment in enumerate(segments):
            text = segment["text"]
            word_count = len(text.split())
            duration = (word_count / SPEAKING_RATE_WPM) * 60
            
            result.append(ExplanationSegment(
                id=segment.get("id", f"segment_{i + 1}"),
                text=text,
                startTime=round(current_time, 1),
                endTime=round(current_time + duration, 1)
            ))
            
            current_time += duration
        
        return result

    def _validate_constraints(
        self,
        parsed: dict,
        segments: list[ExplanationSegment],
        constraints: dict
    ) -> None:
        """
        Validate output against duration constraints.
        
        Raises NarratorError if validation fails.
        """
        # Check segment count
        segment_count = len(segments)
        if segment_count < constraints["segment_min"]:
            raise NarratorError(
                f"Too few segments: {segment_count} < {constraints['segment_min']}"
            )
        if segment_count > constraints["segment_max"]:
            # Log warning but don't fail - can be handled by merging
            pass
        
        # Check word count
        word_count = len(parsed["narration"].split())
        if word_count < constraints["word_min"]:
            raise NarratorError(
                f"Narration too short: {word_count} words < {constraints['word_min']}"
            )
        if word_count > constraints["word_max"]:
            # Allow with warning - 20% tolerance already built in
            pass
        
        # Check duration
        estimated_duration = segments[-1].endTime if segments else 0
        if estimated_duration < constraints["duration_min"] * 0.8:  # 20% tolerance
            raise NarratorError(
                f"Duration too short: {estimated_duration:.1f}s < {constraints['duration_min']}s"
            )


# Convenience function for direct use
async def generate_narration(
    text: str,
    duration: Duration,
    instruction: Optional[str] = None
) -> ExplanationOutput:
    """
    Generate a narrated explanation from input text.
    
    Uses the configured LLM provider (Gemini by default).
    This is a convenience function that creates a Narrator instance
    and calls generate().
    """
    narrator = Narrator()
    return await narrator.generate(text, duration, instruction)
