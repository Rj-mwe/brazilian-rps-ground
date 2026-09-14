"""
Domain Events for Stations Sub-Core.
Immutable event notifications dispatched upon state changes.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StationCoverageDegradedEvent:
    """Dispatched when a ground station is taken offline or degraded."""
    station_code: str
    timestamp: datetime
    reason: str


@dataclass(frozen=True)
class StationRestoredEvent:
    """Dispatched when a ground station returns to full operational status."""
    station_code: str
    timestamp: datetime
