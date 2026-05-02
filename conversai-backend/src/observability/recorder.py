"""
Observability Recorder Module

This module provides the main recording interface: record_run()

It implements hybrid storage:
- Metadata and truncated previews in SQLite
- Full artifacts (images, audio) on disk
"""

import os
from typing import Dict, Any, List, Optional
from src.shared.logger import logger
from src.observability.database import get_transaction, generate_run_id
from src.observability.models import validate_run_data, ArtifactReference
from src.observability.utils import (
    get_utc_timestamp,
    safe_json_dumps,
    truncate_base64,
    compute_sha256,
    save_artifact_file,
    decode_base64_to_bytes
)


def _process_artifact(
    base64_string: str,
    run_id: str,
    filename: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Process a base64 artifact (image or audio) for hybrid storage.
    
    Args:
        base64_string: Full base64 string (may include data URI prefix)
        run_id: Unique run identifier
        filename: Target filename (e.g., "audio.mp3", "segment_1.png")
        metadata: Optional metadata dict
        
    Returns:
        ArtifactReference dict with preview, hash, and local path
    """
    try:
        write_artifacts = os.getenv("OBSERVABILITY_ARTIFACTS", "true").lower() == "true"
        
        # Fast path if artifacts are disabled (skip heavy base64 decode and file IO)
        if not write_artifacts:
            return {
                "preview_base64": truncate_base64(base64_string, max_chars=400),
                "sha256": None,  # Proper NULL value instead of placeholder string
                "local_path": None,  # Explicitly None to prevent invalid paths
                "size_bytes": int(len(base64_string) * 0.75),  # Approximate size
                "metadata": metadata or {}
            }
            
        # Decode base64 to bytes
        content_bytes = decode_base64_to_bytes(base64_string)
        
        # Save to disk
        local_path = save_artifact_file(run_id, filename, content_bytes)
        
        # Compute hash
        sha256_hash = compute_sha256(base64_string)
        
        # Truncate for preview
        preview = truncate_base64(base64_string, max_chars=400)
        
        return {
            "preview_base64": preview,
            "sha256": sha256_hash,
            "local_path": local_path,
            "size_bytes": len(content_bytes),
            "metadata": metadata or {}
        }
    
    except Exception as e:
        logger.warning(f"Failed to process artifact {filename}: {e}")
        # Return minimal reference on failure
        return {
            "preview_base64": truncate_base64(base64_string, max_chars=200),
            "sha256": "error",
            "local_path": f"error_{filename}",
            "size_bytes": 0,
            "error": str(e)
        }


def _process_visual_artifacts(visual_data: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    """
    Process visual engine data to extract and store image artifacts.
    
    Args:
        visual_data: Visual engine data dict
        run_id: Unique run identifier
        
    Returns:
        Updated visual data with artifact references
    """
    processed_visual = visual_data.copy()
    
    # Process images if present
    if "images" in visual_data and isinstance(visual_data["images"], list):
        processed_images = []
        
        for idx, img in enumerate(visual_data["images"]):
            if isinstance(img, dict) and "base64" in img:
                segment_id = img.get("segmentId", f"segment_{idx}")
                filename = f"{segment_id}.png"
                
                artifact_ref = _process_artifact(
                    base64_string=img["base64"],
                    run_id=run_id,
                    filename=filename,
                    metadata={
                        "segmentId": segment_id,
                        "generation_time_ms": img.get("generation_time_ms")
                    }
                )
                
                processed_images.append({
                    "segmentId": segment_id,
                    **artifact_ref
                })
            else:
                # Keep as-is if no base64
                processed_images.append(img)
        
        processed_visual["images"] = processed_images
    
    return processed_visual


def _process_voice_artifacts(voice_data: Dict[str, Any], run_id: str) -> Dict[str, Any]:
    """
    Process voice engine data to extract and store audio artifact.
    
    Args:
        voice_data: Voice engine data dict
        run_id: Unique run identifier
        
    Returns:
        Updated voice data with artifact reference
    """
    processed_voice = voice_data.copy()
    
    # Process audio if present
    if "audio_base64" in voice_data and voice_data["audio_base64"]:
        artifact_ref = _process_artifact(
            base64_string=voice_data["audio_base64"],
            run_id=run_id,
            filename="audio.mp3",
            metadata={
                "duration_sec": voice_data.get("duration")
            }
        )
        
        # Replace full base64 with artifact reference
        processed_voice["audio"] = artifact_ref
        # Remove the full base64 field
        processed_voice.pop("audio_base64", None)
    
    return processed_voice


def _build_render_manifest(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build render manifest from existing payload data.
    
    CHANGE 2: Render-Aware Observability Storage
    
    This manifest represents the final user experience and allows
    exact future re-rendering WITHOUT triggering new AI processing.
    
    Args:
        payload: Complete payload with explanation, visual, voice data
        
    Returns:
        Render manifest dict with timeline and playback metadata
    """
    try:
        # Extract data from existing payload
        explanation = payload.get("explanation", {})
        visual = payload.get("visual", {})
        voice = payload.get("voice", {})
        
        # Build segment timeline from explanation segments
        segments = explanation.get("segments", [])
        segment_timeline = [
            {
                "segmentId": f"segment_{idx}",
                "start": seg.get("startTime", 0),
                "end": seg.get("endTime", 0)
            }
            for idx, seg in enumerate(segments)
        ]
        
        # Count visual segments (successfully generated)
        visual_images = visual.get("images", [])
        visual_segment_count = len([img for img in visual_images if isinstance(img, dict)])
        
        # Check if audio is present
        audio_present = "audio" in voice and voice["audio"] is not None
        
        # Check if avatar is enabled
        avatar_enabled = len(voice.get("avatar_states", [])) > 0
        
        return {
            "audio_present": audio_present,
            "visual_segment_count": visual_segment_count,
            "avatar_enabled": avatar_enabled,
            "segment_timeline": segment_timeline,
            "playback_rate": 1.0  # Default playback rate
        }
    
    except Exception as e:
        logger.warning(f"Failed to build render manifest: {e}")
        # Return minimal manifest on error
        return {
            "audio_present": False,
            "visual_segment_count": 0,
            "avatar_enabled": False,
            "segment_timeline": [],
            "playback_rate": 1.0
        }


def record_run(run_data: Dict[str, Any]) -> bool:
    """
    Record an explanation run to the observability database.
    
    This is the ONLY public interface for recording observability data.
    
    Args:
        run_data: Dict with keys:
            - status: "success" | "partial" | "failed"
            - total_time_ms: float
            - timings: Optional Dict containing explicit engine timings
            - payload: Dict with user_input, explanation, visual, voice, metrics, failures
            
    Returns:
        True if recording succeeded, False otherwise
        
    CRITICAL: This function NEVER raises exceptions. It logs warnings on failure.
    """
    if os.getenv("OBSERVABILITY_ENABLED", "true").lower() == "false":
        return False

    try:
        # Validate input
        if not validate_run_data(run_data):
            logger.warning("Invalid run data structure, skipping observability recording")
            return False
        
        # Generate run metadata
        run_id = generate_run_id()
        created_at = get_utc_timestamp()
        status = run_data["status"]
        total_time_ms = run_data["total_time_ms"]
        payload = run_data["payload"]
        
        # Process artifacts (hybrid storage)
        processed_payload = payload.copy()
        
        # Process visual artifacts
        if "visual" in processed_payload:
            processed_payload["visual"] = _process_visual_artifacts(
                processed_payload["visual"],
                run_id
            )
        
        # Process voice artifacts
        if "voice" in processed_payload:
            processed_payload["voice"] = _process_voice_artifacts(
                processed_payload["voice"],
                run_id
            )
        
        # CHANGE 2: Render-Aware Observability Storage
        # Add render manifest (derived from existing data, NO new processing)
        processed_payload["render_manifest"] = _build_render_manifest(processed_payload)
        
        # Add final_render field (null by default, can be populated later)
        # This field is for storing a final rendered video IF one exists
        # Observability NEVER triggers rendering - this is populated externally
        processed_payload["final_render"] = payload.get("final_render", None)
        
        # Serialize payload to JSON
        payload_json = safe_json_dumps(processed_payload)
        
        # Extract new structured columns
        user_input_text = payload.get("user_input", {}).get("text")
        narration_text = payload.get("explanation", {}).get("narration")
        segments = payload.get("explanation", {}).get("segments", [])
        segment_count = len(segments) if segments else 0
        visual_count = payload.get("visual", {}).get("timings", {}).get("total_generated", 0)
        
        # Explicit timing extraction (backward compatible defaults to None)
        timings = run_data.get("timings", {})
        explanation_time_ms = timings.get("explanation_time_ms")
        visual_time_ms = timings.get("visual_time_ms")
        voice_time_ms = timings.get("voice_time_ms")
        aggregation_time_ms = timings.get("aggregation_time_ms")
        
        # Timing consistency validation (safely treating None as 0 for calculation only)
        exp_val = explanation_time_ms if explanation_time_ms is not None else 0
        vis_val = visual_time_ms if visual_time_ms is not None else 0
        voice_val = voice_time_ms if voice_time_ms is not None else 0
        agg_val = aggregation_time_ms if aggregation_time_ms is not None else 0
        
        expected_total_time = exp_val + max(vis_val, voice_val) + agg_val
        
        if abs(total_time_ms - expected_total_time) > 5.0:  # Allow 5ms deviation
            logger.warning(
                f"Timing validation deviation: total_time_ms ({total_time_ms:.1f}) deviates from "
                f"expected components sum ({expected_total_time:.1f}). This is logged for tracking."
            )
        
        # Insert into database
        with get_transaction() as conn:
            conn.execute(
                """
                INSERT INTO explanation_runs (
                    run_id, created_at, status, total_time_ms, payload_json,
                    explanation_time_ms, visual_time_ms, voice_time_ms, aggregation_time_ms,
                    user_input_text, narration_text, segment_count, visual_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id, created_at, status, total_time_ms, payload_json,
                    explanation_time_ms, visual_time_ms, voice_time_ms, aggregation_time_ms,
                    user_input_text, narration_text, segment_count, visual_count
                )
            )
        
        logger.info(f"Observability: Recorded run {run_id} (status={status}, time={total_time_ms:.1f}ms)")
        return True
    
    except Exception as e:
        # CRITICAL: Never crash the main request flow
        logger.warning(f"Observability recording failed: {e}", exc_info=True)
        return False


__all__ = ["record_run"]
