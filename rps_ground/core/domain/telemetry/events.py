"""
Domain Events for Telemetry Sub-Core.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class LossOfSignalDetectedEvent:
    """Dispatched when Line-of-Sight signal tracking is lost for a satellite."""
    timestamp: datetime
    station_code: str
    satellite_id: int
    reason: str
