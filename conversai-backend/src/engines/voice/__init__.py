"""
Voice & Avatar Engine - Public Facade

Orchestrates Voice Engine (TTS) and Avatar Engine (metadata generation).
Audio generation is REQUIRED. Avatar generation is OPTIONAL.
Avatar failure MUST NOT block audio generation.
"""

import time
from typing import List, Optional, Dict
from src.shared.types import Segment
from src.shared.logger import logger
from .tts import generate_audio_with_retry, VoiceEngineError
from .avatar import generate_avatar_metadata


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


async def synthesize_audio_and_avatar(
    narration: str,
    avatar_enabled: bool,
    segments: Optional[List[Segment]] = None,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Generate audio and optional avatar metadata from narration.
    
    Args:
        narration: Full narration text for TTS
        avatar_enabled: Whether to generate avatar metadata
        segments: Narration segments for avatar timing (optional)
        metadata: Additional context from Explanation Engine (optional)
    
    Returns:
        {
            "audio": str,              # Base64 encoded audio
            "duration": float,         # Actual audio duration
            "format": str,             # Audio format ("mp3")
            "avatar": Optional[dict],  # Avatar metadata if enabled
            "metadata": {
                "generationTime": float,
                "hasAvatar": bool,
                "audioSize": int
            }
        }
    
    Raises:
        ValidationError: If input is invalid
        VoiceEngineError: If audio generation fails
    """
    start_time = time.time()
    
    if not narration:
        raise ValidationError("Narration text is required")
    
    if not narration.strip():
        raise ValidationError("Narration text cannot be empty or whitespace")
    
    logger.info(f"Starting audio generation for {len(narration)} characters")
    
    try:
        audio_data = generate_audio_with_retry(narration)
        logger.info(f"Audio generated successfully: {audio_data['duration']:.2f}s")
    except VoiceEngineError as e:
        logger.error(f"Audio generation failed: {e}")
        raise VoiceEngineError(f"Audio synthesis failed: {e}")
    
    avatar_data = None
    if avatar_enabled:
        logger.info("Avatar enabled, generating metadata")
        try:
            avatar_data = generate_avatar_metadata(
                narration=narration,
                audio_duration=audio_data["duration"],
                segments=segments if segments else []
            )
            if avatar_data:
                logger.info(
                    f"Avatar metadata generated: {avatar_data['metadata']['stateCount']} states"
                )
            else:
                logger.warning("Avatar generation returned None, continuing with audio-only")
        except Exception as e:
            logger.warning(f"Avatar generation failed, continuing with audio-only: {e}")
    else:
        logger.info("Avatar disabled, skipping metadata generation")
    
    generation_time = time.time() - start_time
    
    return {
        "audio": audio_data["audio_base64"],
        "duration": audio_data["duration"],
        "format": audio_data["format"],
        "avatar": avatar_data,
        "metadata": {
            "generationTime": round(generation_time, 2),
            "hasAvatar": avatar_data is not None,
            "audioSize": audio_data["size"]
        }
    }
