"""
Avatar Engine - Lightweight Avatar Metadata Generation

Generates deterministic avatar animation metadata for frontend Lottie rendering.
No AI, no rendering, no lip-sync. Frontend-controlled animation.
"""

from typing import Dict, List, Optional
from src.shared.types import Segment, AvatarState, AnimationCue
from src.shared.logger import logger


def generate_avatar_metadata(
    narration: str,
    audio_duration: float,
    segments: List[Segment]
) -> Optional[Dict]:
    """
    Generate lightweight avatar animation metadata.
    
    Args:
        narration: Full narration text (for context)
        audio_duration: Actual audio duration in seconds
        segments: List of narration segments with timing
    
    Returns:
        {
            "states": List[AvatarState],
            "cues": List[AnimationCue],
            "metadata": {
                "totalDuration": float,
                "stateCount": int
            }
        }
        Returns None if generation fails (graceful degradation)
    """
    try:
        if not segments or len(segments) == 0:
            logger.warning("No segments provided, creating single speaking state")
            states = [
                AvatarState(
                    startTime=0.0,
                    endTime=audio_duration,
                    state="speaking",
                    intensity="medium"
                )
            ]
            cues = []
        else:
            states = []
            cues = []
            
            for segment in segments:
                segment_duration = segment.endTime - segment.startTime
                
                if segment_duration < 10:
                    intensity = "low"
                elif segment_duration < 20:
                    intensity = "medium"
                else:
                    intensity = "high"
                
                state = AvatarState(
                    startTime=segment.startTime,
                    endTime=segment.endTime,
                    state="speaking",
                    intensity=intensity
                )
                states.append(state)
                
                cue = AnimationCue(
                    timestamp=segment.startTime,
                    cueType="segment_start",
                    metadata={
                        "segmentId": getattr(segment, 'id', f'segment_{len(cues) + 1}'),
                        "text": segment.text[:50] if len(segment.text) > 50 else segment.text
                    }
                )
                cues.append(cue)
        
        return {
            "states": [state.model_dump() for state in states],
            "cues": [cue.model_dump() for cue in cues],
            "metadata": {
                "totalDuration": audio_duration,
                "stateCount": len(states)
            }
        }
    
    except Exception as e:
        logger.error(f"Avatar metadata generation failed: {e}")
        return None
