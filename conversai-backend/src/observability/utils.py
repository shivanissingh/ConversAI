"""
Observability Utility Functions

This module provides helper functions for:
- JSON serialization (safe handling of large data)
- Base64 truncation and hashing
- UUID generation
- Timestamp formatting
- File I/O helpers
"""

import json
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from pathlib import Path


def get_utc_timestamp() -> str:
    """
    Get current UTC timestamp in ISO 8601 format.
    
    Returns:
        ISO timestamp string (e.g., "2026-01-28T08:44:23.123456Z")
    """
    return datetime.now(timezone.utc).isoformat()


def truncate_base64(base64_string: str, max_chars: int = 400) -> str:
    """
    Truncate a base64 string for preview purposes.
    
    Args:
        base64_string: Full base64 string (may include data URI prefix)
        max_chars: Maximum characters to keep
        
    Returns:
        Truncated string with "..." suffix if truncated
    """
    if not base64_string:
        return ""
    
    if len(base64_string) <= max_chars:
        return base64_string
    
    return base64_string[:max_chars] + "..."


def compute_sha256(content: str) -> str:
    """
    Compute SHA-256 hash of content.
    
    Args:
        content: String content to hash
        
    Returns:
        Hex digest of SHA-256 hash
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def safe_json_dumps(data: Any) -> str:
    """
    Safely serialize data to JSON.
    
    Never crashes - returns error JSON on failure.
    
    Args:
        data: Any JSON-serializable data
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    except Exception as e:
        # Return error JSON instead of crashing
        return json.dumps({
            "error": "JSON serialization failed",
            "reason": str(e)
        })


def safe_json_loads(json_string: str) -> Dict:
    """
    Safely deserialize JSON string.
    
    Never crashes - returns error dict on failure.
    
    Args:
        json_string: JSON string
        
    Returns:
        Parsed dict or error dict
    """
    try:
        return json.loads(json_string)
    except Exception as e:
        return {
            "error": "JSON deserialization failed",
            "reason": str(e)
        }


def ensure_artifact_directory(run_id: str) -> Path:
    """
    Ensure artifact directory exists for a given run.
    
    Creates: observability_artifacts/run_<run_id>/
    
    Args:
        run_id: Unique run identifier
        
    Returns:
        Path to the run's artifact directory
    """
    # Base artifacts directory (in project root)
    base_dir = Path(__file__).parent.parent.parent / "observability_artifacts"
    run_dir = base_dir / f"run_{run_id}"
    
    # Create directory (no error if exists)
    run_dir.mkdir(parents=True, exist_ok=True)
    
    return run_dir


def save_artifact_file(run_id: str, filename: str, content: bytes) -> str:
    """
    Save an artifact file to disk.
    
    Args:
        run_id: Unique run identifier
        filename: File name (e.g., "audio.mp3", "segment_1.png")
        content: Binary content to write
        
    Returns:
        Relative path to the saved file (for DB storage)
        
    Raises:
        IOError: If file write fails
    """
    run_dir = ensure_artifact_directory(run_id)
    file_path = run_dir / filename
    
    # Write binary content
    file_path.write_bytes(content)
    
    # Return relative path from project root
    return f"observability_artifacts/run_{run_id}/{filename}"


def decode_base64_to_bytes(base64_string: str) -> bytes:
    """
    Decode a base64 string (with or without data URI prefix) to bytes.
    
    Args:
        base64_string: Base64 string, optionally with "data:..." prefix
        
    Returns:
        Decoded bytes
    """
    import base64
    
    # Handle None or empty strings
    if not base64_string:
        return b''
    
    # Remove data URI prefix if present
    if base64_string.startswith("data:"):
        # Format: "data:image/png;base64,iVBORw0KGgo..."
        base64_string = base64_string.split(",", 1)[1]
    
    return base64.b64decode(base64_string)


__all__ = [
    "get_utc_timestamp",
    "truncate_base64",
    "compute_sha256",
    "safe_json_dumps",
    "safe_json_loads",
    "ensure_artifact_directory",
    "save_artifact_file",
    "decode_base64_to_bytes"
]
