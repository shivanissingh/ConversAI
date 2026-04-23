"""
Synchronizer Module - Timing Alignment and Validation

This module provides helper functions for:
- Aligning segments with visuals (1:1 mapping by segmentId)
- Validating timing integrity across components
- Handling visual placeholder logic

All functions are:
- Deterministic (no randomness)
- Side-effect free (no mutations)
- Engine-agnostic (no engine calls)
"""

from typing import List, Dict
from src.shared.types import Segment
from src.shared.logger import logger


def align_segments_with_visuals(
    segments: List[Segment],
    visuals: List[Dict]
) -> List[Dict]:
    """
    Attach visuals to corresponding segments by segmentId.

    Creates a 1:1 mapping where each segment either has an attached visual
    or visual: null if generation failed.

    Args:
        segments: List of narration segments from Explanation Engine
        visuals: List of generated visuals from Visual Engine (dicts)

    Returns:
        List of aligned segments with visual attached:
        [
            {
                "id": "segment_1",
                "text": "...",
                "startTime": 0.0,
                "endTime": 12.8,
                "visual": {dict} or None
            },
            ...
        ]
    """
    # Create lookup map: segmentId -> visual (dict)
    visual_map: Dict[str, Dict] = {}

    for visual in visuals:
        metadata = visual.get("metadata", {})
        segment_id = metadata.get("segmentId")

        if segment_id:
            visual_map[segment_id] = visual

    # Attach visuals to segments
    aligned_segments: List[Dict] = []

    for i, segment in enumerate(segments):
        segment_id = f"segment_{i + 1}"

        aligned_segment = {
            "id": segment_id,
            "text": segment.text,
            "startTime": segment.startTime,
            "endTime": segment.endTime,
            "visual": visual_map.get(segment_id)  # None if visual failed
        }

        aligned_segments.append(aligned_segment)

    return aligned_segments


def validate_timing_integrity(
    aligned_segments: List[Dict],
    audio_duration: float
) -> None:
    """
    Validate timing consistency across segments and audio.

    Checks:
    1. Segment timing continuity (no gaps or overlaps)
    2. First segment starts at 0
    3. Audio duration roughly matches expected duration

    Does NOT raise errors, only logs warnings for mismatches.
    """
    if not aligned_segments:
        logger.warning("No segments to validate timing")
        return

    # Check 1: First segment starts at 0
    first_segment = aligned_segments[0]
    if first_segment["startTime"] != 0:
        logger.warning(
            f"First segment does not start at 0: {first_segment['startTime']}"
        )

    # Check 2: Segment timing continuity
    for i, segment in enumerate(aligned_segments):
        if i > 0:
            prev_segment = aligned_segments[i - 1]
            expected_start = prev_segment["endTime"]
            actual_start = segment["startTime"]

            if abs(actual_start - expected_start) > 0.1:
                logger.warning(
                    f"Segment timing gap detected: "
                    f"segment {i} starts at {actual_start}s, "
                    f"expected {expected_start}s"
                )

    # Check 3: Audio duration matches segment timeline
    last_segment = aligned_segments[-1]
    estimated_duration = last_segment["endTime"]

    tolerance = 0.20
    lower_bound = estimated_duration * (1 - tolerance)
    upper_bound = estimated_duration * (1 + tolerance)

    if not (lower_bound <= audio_duration <= upper_bound):
        logger.warning(
            f"Audio duration mismatch: "
            f"estimated={estimated_duration:.1f}s, "
            f"actual={audio_duration:.1f}s "
            f"(variance: {abs(audio_duration - estimated_duration) / estimated_duration * 100:.1f}%)"
        )
    else:
        logger.info(
            f"Audio duration validated: "
            f"estimated={estimated_duration:.1f}s, "
            f"actual={audio_duration:.1f}s"
        )


def validate_visual_alignment(aligned_segments: List[Dict]) -> None:
    """
    Validate that visuals align correctly with segment timing.

    For segments that have visuals attached, ensures:
    - Visual startTime matches segment startTime
    - Visual endTime matches segment endTime

    Logs warnings for misalignments.
    """
    for segment in aligned_segments:
        visual = segment.get("visual")
        if visual:
            visual_start = visual.get("startTime")
            visual_end = visual.get("endTime")

            if visual_start != segment["startTime"]:
                logger.warning(
                    f"Visual timing mismatch in {segment['id']}: "
                    f"visual starts at {visual_start}s, "
                    f"segment starts at {segment['startTime']}s"
                )

            if visual_end != segment["endTime"]:
                logger.warning(
                    f"Visual timing mismatch in {segment['id']}: "
                    f"visual ends at {visual_end}s, "
                    f"segment ends at {segment['endTime']}s"
                )


def collect_failures(visual_output: Dict) -> List[Dict]:
    """
    Collect failure information from visual engine output.

    Args:
        visual_output: Output from Visual Engine with metadata

    Returns:
        List of failure objects:
        [
            {
                "component": "visual_engine",
                "segmentId": "segment_2" or None,
                "reason": "API timeout",
                "isCritical": False
            },
            ...
        ]
    """
    failures: List[Dict] = []

    metadata = visual_output.get("metadata", {})
    visual_failures = metadata.get("failures", [])

    for failure in visual_failures:
        failures.append({
            "component": "visual_engine",
            "segmentId": failure.get("segmentId"),
            "reason": failure.get("reason", "Unknown error"),
            "isCritical": False
        })

    return failures
