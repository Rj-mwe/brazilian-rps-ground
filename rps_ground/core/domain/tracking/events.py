"""
Domain Events for Tracking Sub-Core.
"""
from dataclasses import dataclass
from datetime import datetime

from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO


@dataclass(frozen=True)
class VehicleEnteredRegionalZoneEvent:
    """Dispatched when a vehicle enters an operational ground zone."""
    vehicle_id: str
    station_code: str
    timestamp: datetime
    location: GeodeticCoordinatesVO


@dataclass(frozen=True)
class SpeedExceededAlertEvent:
    """Dispatched when vehicle exceeds maximum operational corridor speed."""
    vehicle_id: str
    speed_mps: float
    limit_mps: float
    timestamp: datetime
