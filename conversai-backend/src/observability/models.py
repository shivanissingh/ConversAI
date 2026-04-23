"""
Observability Data Models

This module defines the data structures for observability records.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class RunRecord:
    """
    Main database record for an explanation run.
    
    Maps directly to the explanation_runs table.
    """
    run_id: str
    created_at: str  # ISO 8601 UTC timestamp
    status: str  # "success" | "partial" | "failed"
    total_time_ms: float
    payload_json: str  # JSON string of PayloadData


@dataclass
class ArtifactReference:
    """
    Reference to a stored artifact (image or audio).
    
    Stored in payload_json, NOT as full base64.
    """
    preview_base64: str  # Truncated preview (~400 chars)
    sha256: str  # Hash of full content
    local_path: str  # Relative path to artifact file
    size_bytes: int  # File size
    generation_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PayloadData:
    """
    Complete payload structure stored in payload_json.
    
    This is the main observability data structure.
    """
    # User Input Snapshot
    user_input: Dict[str, Any]  # {text, duration, instruction, avatar_enabled}
    
    # Explanation Engine Data
    explanation: Dict[str, Any]  # {concepts, narration, segments, timings}
    
    # Visual Engine Data
    visual: Dict[str, Any]  # {plans (if available), images (ArtifactReference), timings, failures}
    
    # Voice & Avatar Data
    voice: Dict[str, Any]  # {audio (ArtifactReference), duration, avatar_states, timings}
    
    # Quality & Performance Metrics
    metrics: Dict[str, Any]  # {total_time, visual_success_ratio, audio_vs_segment_delta}
    
    # Failures
    failures: List[Dict[str, Any]]  # [{component, segment_id, reason, critical}]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


def validate_run_data(data: Dict[str, Any]) -> bool:
    """
    Validate that run data has required fields.
    
    Args:
        data: Run data dict
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["status", "total_time_ms", "payload"]
    
    for field in required_fields:
        if field not in data:
            return False
    
    # Validate status
    if data["status"] not in ["success", "partial", "failed"]:
        return False
    
    # Validate payload structure
    payload = data.get("payload", {})
    required_payload_fields = ["user_input", "explanation", "visual", "voice", "metrics", "failures"]
    
    for field in required_payload_fields:
        if field not in payload:
            return False
    
    return True


__all__ = ["RunRecord", "ArtifactReference", "PayloadData", "validate_run_data"]
