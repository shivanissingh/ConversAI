"""
Observability Timing Utilities

This module provides timing helpers for measuring engine performance.
"""

import time
from typing import Dict, Optional


class Timer:
    """
    Context manager for measuring execution time.
    
    Usage:
        with Timer() as t:
            # ... code to measure ...
            pass
        
        print(f"Elapsed: {t.elapsed_ms}ms")
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        return False  # Don't suppress exceptions
    
    @property
    def elapsed_ms(self) -> float:
        """Get elapsed time in milliseconds."""
        if self.start_time is None:
            return 0.0
        
        end = self.end_time if self.end_time is not None else time.perf_counter()
        return (end - self.start_time) * 1000.0
    
    @property
    def elapsed_sec(self) -> float:
        """Get elapsed time in seconds."""
        return self.elapsed_ms / 1000.0


class TimingCollector:
    """
    Accumulator for multiple timing measurements.
    
    Usage:
        collector = TimingCollector()
        
        with Timer() as t:
            # ... engine call ...
            pass
        collector.add("explanation_engine", t.elapsed_ms)
        
        timings = collector.get_all()
    """
    
    def __init__(self):
        self._timings: Dict[str, float] = {}
    
    def add(self, name: str, duration_ms: float):
        """
        Add a timing measurement.
        
        Args:
            name: Timing label (e.g., "explanation_engine")
            duration_ms: Duration in milliseconds
        """
        self._timings[name] = duration_ms
    
    def get(self, name: str) -> Optional[float]:
        """Get a specific timing."""
        return self._timings.get(name)
    
    def get_all(self) -> Dict[str, float]:
        """Get all timings as a dict."""
        return self._timings.copy()
    
    def total(self) -> float:
        """Get total of all timings."""
        return sum(self._timings.values())


__all__ = ["Timer", "TimingCollector"]
