"""
Entities for Tracking Domain Sub-Core.
"""
from dataclasses import dataclass
from typing import Tuple

from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.tracking.value_objects import RoadType


@dataclass
class RoadSegmentEntity:
    """
    Entity representing a linear segment of the regional road network.
    Identified by unique segment_id.
    """
    segment_id: str
    name: str
    road_code: str
    road_type: RoadType
    waypoints: Tuple[GeodeticCoordinatesVO, ...]
    length_meters: float = 0.0

    def __post_init__(self):
        if len(self.waypoints) < 2:
            raise ValueError(f"Road segment requires at least 2 waypoints, got {len(self.waypoints)}")


@dataclass
class VehicleEntity:
    """
    Entity representing a monitored terrestrial vehicle or fleet unit.
    """
    vehicle_id: str
    name: str
    operational_status: str = "ACTIVE"
