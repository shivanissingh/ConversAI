"""
Voice Engine - Text-to-Speech

Converts narration text to audio using edge-tts (Microsoft Neural TTS).
No API keys required. Natural-sounding neural voice synthesis.

Upgrade from gTTS: edge-tts provides significantly more natural,
human-like voice with proper intonation, emphasis, and pausing.
"""

import os
import asyncio
import time
import base64
import tempfile
from typing import Dict
import edge_tts
from mutagen.mp3 import MP3
from src.shared.logger import logger


class VoiceEngineError(Exception):
    """Raised when voice generation fails."""
    pass


# Retry configuration
RETRY_CONFIG = {
    "max_retries": 2,
    "retry_delay": 1.0,
    "backoff_factor": 2.0
}

# Voice configuration
# Available neural voices (all free, no API key):
#   - en-US-AriaNeural (female, warm, conversational)
#   - en-US-GuyNeural (male, clear, professional)
#   - en-US-JennyNeural (female, friendly)
#   - en-US-ChristopherNeural (male, warm)
#   - en-IN-NeerjaNeural (female, Indian English)
#   - en-IN-PrabhatNeural (male, Indian English)
VOICE_CONFIG = {
    "voice": "en-US-AriaNeural",
    "rate": "+0%",             # Speaking rate adjustment (-50% to +100%)
    "volume": "+0%",           # Volume adjustment
    "pitch": "+0Hz",           # Pitch adjustment
    "output_format": "mp3",
    "temp_dir": "/tmp/conversai_audio"
}


async def _generate_audio_async(narration: str) -> Dict:
    """
    Internal async function to generate audio using edge-tts.
    
    Args:
        narration: Full narration text for TTS generation
    
    Returns:
        Audio data dictionary
    
    Raises:
        VoiceEngineError: If audio generation fails
    """
    if not narration or len(narration.strip()) == 0:
        raise VoiceEngineError("Empty narration text")
    
    # Create temp directory
    os.makedirs(VOICE_CONFIG["temp_dir"], exist_ok=True)
    
    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=f'.{VOICE_CONFIG["output_format"]}',
        dir=VOICE_CONFIG["temp_dir"]
    )
    audio_path = temp_file.name
    temp_file.close()
    
    try:
        # Initialize edge-tts communicator
        communicate = edge_tts.Communicate(
            text=narration,
            voice=VOICE_CONFIG["voice"],
            rate=VOICE_CONFIG["rate"],
            volume=VOICE_CONFIG["volume"],
            pitch=VOICE_CONFIG["pitch"]
        )
        
        # Generate and save audio
        await communicate.save(audio_path)
        
        logger.info(f"Audio generated with edge-tts voice: {VOICE_CONFIG['voice']}")
        
    except Exception as e:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise VoiceEngineError(f"edge-tts audio generation failed: {e}")
    
    # Calculate actual duration
    try:
        audio = MP3(audio_path)
        duration = audio.info.length
    except Exception as e:
        logger.warning(f"Duration calculation failed: {e}, using estimation")
        word_count = len(narration.split())
        duration = (word_count / 150) * 60
    
    # Encode to base64
    try:
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    except Exception as e:
        if os.path.exists(audio_path):
            os.remove(audio_path)
        raise VoiceEngineError(f"Audio encoding failed: {e}")
    
    return {
        "audio_path": audio_path,
        "audio_base64": f"data:audio/mp3;base64,{audio_base64}",
        "duration": duration,
        "format": VOICE_CONFIG["output_format"],
        "size": len(audio_bytes)
    }


def generate_audio(narration: str) -> Dict:
    """
    Generate audio from narration text using edge-tts.
    
    Wraps the async edge-tts call for synchronous usage.
    
    Args:
        narration: Full narration text for TTS generation
    
    Returns:
        {
            "audio_path": str,      # Temp file path
            "audio_base64": str,    # Base64 encoded audio (data URI)
            "duration": float,      # Actual audio duration in seconds
            "format": str,          # "mp3"
            "size": int             # File size in bytes
        }
    
    Raises:
        VoiceEngineError: If audio generation fails
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside an async context (e.g., FastAPI)
            # Create a new thread to run the coroutine
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, _generate_audio_async(narration)
                )
                return future.result(timeout=120)
        else:
            return loop.run_until_complete(_generate_audio_async(narration))
    except RuntimeError:
        # No event loop exists, create one
        return asyncio.run(_generate_audio_async(narration))


def generate_audio_with_retry(narration: str) -> Dict:
    """
    Generate audio with retry logic.
    
    Args:
        narration: Full narration text
    
    Returns:
        Audio data dictionary
    
    Raises:
        VoiceEngineError: If all retry attempts fail
    """
    for attempt in range(RETRY_CONFIG["max_retries"] + 1):
        try:
            return generate_audio(narration)
        except VoiceEngineError as e:
            if attempt == RETRY_CONFIG["max_retries"]:
                raise VoiceEngineError(
                    f"Audio generation failed after {attempt + 1} attempts: {e}"
                )
            
            delay = RETRY_CONFIG["retry_delay"] * (RETRY_CONFIG["backoff_factor"] ** attempt)
            logger.warning(
                f"Audio generation attempt {attempt + 1} failed, "
                f"retrying in {delay}s: {e}"
            )
            time.sleep(delay)
