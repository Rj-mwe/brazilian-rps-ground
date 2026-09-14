"""
Entities for Stations Domain Sub-Core.
"""
from dataclasses import dataclass
from typing import Optional

from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.stations.value_objects import CoveragePolygonVO, StationType


@dataclass
class GroundStationEntity:
    """
    Mutable entity representing an active or standby regional ground station.
    Identity is defined by its unique code (e.g., SJC, ALC, NAT, BSB, CPQ).
    """
    code: str
    name: str
    station_type: StationType
    location: GeodeticCoordinatesVO
    elevation_mask_deg: float = 5.0
    coverage_radius_km: float = 1200.0
    coverage_polygon: Optional[CoveragePolygonVO] = None
    is_operational: bool = True

    def mark_operational(self) -> None:
        self.is_operational = True

    def mark_degraded(self) -> None:
        self.is_operational = False
