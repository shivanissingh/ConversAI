"""
Composer Module - Core Orchestration Logic

This module implements the complete aggregation flow:
1. Call Explanation Engine (FAIL-CRITICAL)
2. Call Visual Engine + Voice & Avatar Engine IN PARALLEL (FAIL-SOFT / FAIL-CRITICAL)
3. Compose unified response
4. Validate timing integrity

Visual and Voice both depend only on Explanation output, so they run
concurrently via asyncio.gather() to minimise total wall-clock time.
"""

import asyncio
import time
from typing import Optional, Dict, List
from src.shared.types import Segment, Duration
from src.shared.logger import logger
from src.engines.aggregation.synchronizer import (
    align_segments_with_visuals,
    validate_timing_integrity,
    validate_visual_alignment,
    collect_failures
)

# Import existing engines
from src.engines.explanation import process as explanation_process
from src.engines.visual import generate_visuals
from src.engines.voice import synthesize_audio_and_avatar

# Import observability
from src.observability import record_run


class AggregationError(Exception):
    """Raised when critical aggregation failure occurs."""
    def __init__(self, message: str, component: str, original_error: Exception = None):
        super().__init__(message)
        self.component = component
        self.original_error = original_error


async def orchestrate_aggregation(
    text: str,
    duration: Duration,
    instruction: Optional[str],
    avatar_enabled: bool
) -> Dict:
    """
    Orchestrate all engines and compose unified output.
    
    This is the CORE orchestration function that follows the exact flow
    defined in AGGREGATION_ENGINE_DESIGN.md.
    
    Args:
        text: Original text to explain
        duration: "short" | "medium"
        instruction: Optional user instruction
        avatar_enabled: Whether to generate avatar metadata
        
    Returns:
        Unified multimodal response (see design doc for schema)
        
    Raises:
        AggregationError: If critical engines (Explanation, Voice) fail
    """
    start_time = time.time()
    
    # Initialize observability data collection
    observability_data = {
        "user_input": {
            "text": text,
            "duration": duration.value,
            "instruction": instruction,
            "avatar_enabled": avatar_enabled
        },
        "explanation": {},
        "visual": {},
        "voice": {},
        "metrics": {},
        "failures": []
    }
    
    logger.info("=" * 60)
    logger.info("AGGREGATION ENGINE STARTED")
    logger.info(f"Text length: {len(text)} chars")
    logger.info(f"Duration: {duration}")
    logger.info(f"Instruction: {instruction or 'None'}")
    logger.info(f"Avatar enabled: {avatar_enabled}")
    logger.info("="* 60)
    
    status = "failed"
    
    try:
    
    # ========================================================================
    # STEP 1: Orchestrate Explanation Engine (CRITICAL)
    # ========================================================================
    t0 = time.time()
    logger.info("STEP 1: Calling Explanation Engine...")
    try:
        explanation_start = time.time()
        narration, segments, explanation_metadata = await explanation_process(
            text=text,
            duration=duration,
            instruction=instruction
        )
        explanation_time = (time.time() - explanation_start) * 1000
        
        logger.info(
            f"✓ Explanation Engine succeeded: "
            f"{len(segments)} segments, "
            f"estimated duration: {explanation_metadata['estimatedDuration']:.1f}s"
        )
        t1 = time.time()
        logger.info(f"⏱  Explanation: {t1 - t0:.1f}s")
        
        # Capture explanation data for observability
        observability_data["explanation"] = {
            "concepts": explanation_metadata.get("concepts", []),
            "narration": narration,
            "segments": [
                {"text": s.text, "startTime": s.startTime, "endTime": s.endTime}
                for s in segments
            ],
            "timings": {
                "total_time_ms": explanation_time,
                "estimated_duration_sec": explanation_metadata.get("estimatedDuration")
            }
        }
        
    except Exception as e:
        logger.error(f"✗ Explanation Engine FAILED: {e}")
        
        # Record failure for observability
        observability_data["failures"].append({
            "component": "explanation",
            "segment_id": None,
            "reason": str(e),
            "critical": True
        })
        
        # Compute available explanation time up to failure
        if 'explanation_start' in locals():
            observability_data["explanation"] = {
                "timings": {"total_time_ms": (time.time() - explanation_start) * 1000}
            }
        
        raise AggregationError(
            f"Critical component 'explanation' failed: {e}",
            component="explanation",
            original_error=e
        )
    
    # ========================================================================
    # STEP 2+3: Visual Engine + Voice & Avatar Engine — run IN PARALLEL
    # Both only need explanation output, so there is no dependency between them.
    # ========================================================================
    logger.info("STEP 2+3: Launching Visual Engine and Voice & Avatar Engine in parallel...")

    visual_task = asyncio.create_task(
        generate_visuals(segments=segments, metadata=explanation_metadata)
    )
    voice_task = asyncio.create_task(
        synthesize_audio_and_avatar(
            narration=narration,
            avatar_enabled=avatar_enabled,
            segments=segments,
            metadata=explanation_metadata
        )
    )

    raw_visual, raw_voice = await asyncio.gather(
        visual_task, voice_task, return_exceptions=True
    )

    t2 = time.time()
    logger.info(
        f"⏱  Visual+Voice parallel: {t2 - t1:.1f}s | "
        f"Total so far: {t2 - t0:.1f}s"
    )

    # --- Visual Engine result (FAIL-SOFT) ---
    visuals = []
    visual_failures = []
    visual_output = None

    if isinstance(raw_visual, Exception):
        logger.warning(f"⚠ Visual Engine failed (non-critical): {raw_visual}")
        visual_failures = [{
            "component": "visual_engine",
            "segmentId": None,
            "reason": str(raw_visual),
            "isCritical": False
        }]
        observability_data["visual"] = {
            "images": [],
            "timings": {"total_time_ms": 0},
            "failures": visual_failures
        }
    else:
        visual_output = raw_visual
        visuals = visual_output.get("visuals", [])
        visual_stats = visual_output.get("metadata", {})
        visual_failures = collect_failures(visual_output)

        logger.info(
            f"✓ Visual Engine completed: "
            f"{visual_stats.get('totalGenerated', 0)}/{visual_stats.get('totalRequested', 0)} "
            f"visuals generated"
        )
        if visual_failures:
            logger.warning(f"Visual Engine had {len(visual_failures)} failures (non-critical)")

        observability_data["visual"] = {
            "images": [
                {
                    "segmentId": v.get("segmentId", f"segment_{idx}"),
                    "base64": v.get("url", ""),
                    "generation_time_ms": v.get("generation_time_ms")
                }
                for idx, v in enumerate(visuals)
            ],
            "timings": {
                "total_time_ms": (t2 - t1) * 1000,
                "total_requested": visual_stats.get("totalRequested", 0),
                "total_generated": visual_stats.get("totalGenerated", 0)
            },
            "failures": visual_failures
        }

    # --- Voice & Avatar Engine result (FAIL-CRITICAL) ---
    if isinstance(raw_voice, Exception):
        logger.error(f"✗ Voice & Avatar Engine FAILED: {raw_voice}")

        observability_data["failures"].append({
            "component": "voice",
            "segment_id": None,
            "reason": str(raw_voice),
            "critical": True
        })

        if 't1' in locals():
            observability_data["voice"] = {
                "timings": {"total_time_ms": (time.time() - t1) * 1000}
            }

        raise AggregationError(
            f"Critical component 'voice' failed: {raw_voice}",
            component="voice",
            original_error=raw_voice
        )

    voice_output = raw_voice
    logger.info(
        f"✓ Voice & Avatar Engine succeeded: "
        f"audio duration: {voice_output['duration']:.1f}s, "
        f"avatar: {voice_output.get('avatar') is not None}"
    )

    avatar_data = voice_output.get("avatar")
    observability_data["voice"] = {
        "audio_base64": voice_output["audio"],
        "duration": voice_output["duration"],
        "avatar_states": avatar_data.get("states", []) if avatar_data else [],
        "avatar_cues": avatar_data.get("cues", []) if avatar_data else [],
        "timings": {
            "total_time_ms": (t2 - t1) * 1000
        }
    }
    
    # ========================================================================
    # STEP 4: Compose Unified Response
    # ========================================================================
    logger.info("STEP 4: Composing unified response...")
    
    # Align segments with visuals (1:1 mapping by segmentId)
    aligned_segments = align_segments_with_visuals(segments, visuals)
    
    logger.info(f"Aligned {len(aligned_segments)} segments with visuals")
    
    # ========================================================================
    # STEP 5: Validate Timing Integrity
    # ========================================================================
    logger.info("STEP 5: Validating timing integrity...")
    
    validate_timing_integrity(aligned_segments, voice_output["duration"])
    validate_visual_alignment(aligned_segments)
    
    logger.info("✓ Timing validation complete")
    
    # ========================================================================
    # STEP 6: Build Final Response
    # ========================================================================
    total_time = time.time() - start_time
    
    # Calculate visual stats
    total_segments = len(segments)
    total_visuals_generated = len(visuals)
    total_visuals_failed = total_segments - total_visuals_generated
    
    # Capture final metrics for observability
    observability_data["metrics"] = {
        "total_time_ms": total_time * 1000,
        "visual_success_ratio": total_visuals_generated / total_segments if total_segments > 0 else 0,
        "audio_vs_segment_duration_delta": voice_output["duration"] - explanation_metadata.get("estimatedDuration", 0)
    }
    
    # Add visual failures to main failures list
    observability_data["failures"].extend(visual_failures)
    
    status = "success" if total_visuals_generated > 0 else "partial"
    
    unified_output = {
        "narration": narration,
        "segments": aligned_segments,
        "audio": voice_output["audio"],
        "audioDuration": voice_output["duration"],
        "avatar": voice_output.get("avatar"),
        "metadata": {
            "totalTime": round(total_time, 2),
            "explanationSuccess": True,  # Always true (else aggregation fails)
            "visualSuccess": total_visuals_generated > 0,
            "voiceSuccess": True,  # Always true (else aggregation fails)
            "avatarSuccess": voice_output.get("avatar") is not None,
            "visualStats": {
                "requested": total_segments,
                "generated": total_visuals_generated,
                "failed": total_visuals_failed
            },
            "failures": visual_failures
        }
    }
    
    logger.info("=" * 60)
    logger.info("AGGREGATION ENGINE COMPLETED")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Segments: {total_segments}")
    logger.info(f"Visuals: {total_visuals_generated}/{total_segments} generated")
    logger.info(f"Audio: {voice_output['duration']:.1f}s")
    logger.info(f"Avatar: {'Yes' if unified_output['metadata']['avatarSuccess'] else 'No'}")
    logger.info("=" * 60)
    
    return unified_output

    except Exception as e:
        # Status remains "failed"
        raise
    
    finally:
        # Ensure only one record is written per request
        total_time_ms_final = (time.time() - start_time) * 1000
        
        # Calculate distinct aggregation time (excluding parallel engine time)
        exp_time = observability_data.get("explanation", {}).get("timings", {}).get("total_time_ms")
        vis_time = observability_data.get("visual", {}).get("timings", {}).get("total_time_ms")
        voice_time = observability_data.get("voice", {}).get("timings", {}).get("total_time_ms")
        
        # Use local variables for arithmetic to avoid overwriting None with 0 in the DB
        exp_calc = exp_time if exp_time is not None else 0
        vis_calc = vis_time if vis_time is not None else 0
        voice_calc = voice_time if voice_time is not None else 0
        
        # Visual and voice run in parallel, so we subtract max
        max_parallel_time = max(vis_calc, voice_calc)
        aggregation_time_ms = max(0.0, total_time_ms_final - exp_calc - max_parallel_time)
        
        try:
            record_run({
                "status": status,
                "total_time_ms": total_time_ms_final,
                "timings": {
                    "explanation_time_ms": exp_time,
                    "visual_time_ms": vis_time,
                    "voice_time_ms": voice_time,
                    "aggregation_time_ms": aggregation_time_ms
                },
                "payload": observability_data
            })
        except Exception as obs_error:
            logger.warning(f"Failed to record final observability data: {obs_error}")
