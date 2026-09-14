"""
Value Objects for Tracking Domain Sub-Core.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO


class RoadType(str, Enum):
    HIGHWAY_FEDERAL = "HIGHWAY_FEDERAL"
    HIGHWAY_STATE = "HIGHWAY_STATE"
    ARTERIAL = "ARTERIAL"
    LOCAL = "LOCAL"


@dataclass(frozen=True)
class VehicleTrackPointVO:
    """
    Immutable georeferenced tracking point captured by vehicle GNSS receiver.
    """
    vehicle_id: str
    timestamp: datetime
    position: GeodeticCoordinatesVO
    speed_mps: float = 0.0
    heading_deg: float = 0.0
    pdop: float = 1.0
    fix_status: str = "3D_FIX"

    def __post_init__(self):
        if self.speed_mps < 0.0:
            raise ValueError(f"Speed cannot be negative, got {self.speed_mps}")
        if not (0.0 <= self.heading_deg <= 360.0):
            raise ValueError(f"Heading must be in [0, 360] degrees, got {self.heading_deg}")
        if self.pdop < 0.0:
            raise ValueError(f"PDOP cannot be negative, got {self.pdop}")
