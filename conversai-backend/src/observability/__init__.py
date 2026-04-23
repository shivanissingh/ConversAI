"""
Observability Module - Public Interface

This module provides observability and telemetry for ConversAI.

Usage:
    from src.observability import record_run
    
    record_run({
        "status": "success",
        "total_time_ms": 1234.5,
        "payload": {...}
    })
"""

from src.observability.recorder import record_run
from src.observability.timers import Timer, TimingCollector
from src.observability.database import initialize_database

__all__ = ["record_run", "Timer", "TimingCollector", "initialize_database"]
