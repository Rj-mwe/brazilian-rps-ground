"""
Governance Sub-Core: Temporal Barrier (IEEE 1516 Regulation).
Guarantees monotonic progression of simulation and telemetry time in ground systems.
"""
import threading
from datetime import datetime
from typing import Optional


class GroundTemporalBarrier:
    """
    Thread-safe temporal regulator enforcing IEEE 1516 time progression rules.
    Prevents retrograde time jumps and manages temporal lock-step.
    """

    def __init__(self, initial_time: Optional[datetime] = None):
        self._lock = threading.RLock()
        self._current_time: Optional[datetime] = initial_time

    @property
    def current_time(self) -> Optional[datetime]:
        with self._lock:
            return self._current_time

    def advance_time(self, next_time: datetime) -> None:
        """Advance the master ground clock, ensuring strictly non-retrograde progression."""
        with self._lock:
            if self._current_time is not None and next_time < self._current_time:
                raise ValueError(
                    f"Temporal barrier violation: attempt to reverse time from "
                    f"{self._current_time.isoformat()} to {next_time.isoformat()}"
                )
            self._current_time = next_time

    def validate_timestamp(self, ts: datetime) -> bool:
        """Check if incoming timestamp is not retrograde relative to barrier."""
        with self._lock:
            if self._current_time is None:
                return True
            return ts >= self._current_time
