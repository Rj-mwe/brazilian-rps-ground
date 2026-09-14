"""
Value Objects for Stations Domain Sub-Core.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO


class StationType(str, Enum):
    """Classification of regional ground stations."""
    RIMS = "RIMS"                                    # Ranging and Integrity Monitoring Station
    MASTER_CONTROL = "MASTER_CONTROL"                # Master Control Station (MCC / CCM)
    UPLINK = "UPLINK"                                # Ground Uplink Station (GUS)
    AEROSPACE_RESEARCH = "AEROSPACE_RESEARCH"        # Research & Engineering Testbed (e.g., ITA/DCTA)


@dataclass(frozen=True)
class CoveragePolygonVO:
    """
    Immutable closed polygon representing regional coverage footprint on Earth.
    Boundary vertices are a sequence of GeodeticCoordinatesVO.
    """
    vertices: Tuple[GeodeticCoordinatesVO, ...]

    def __post_init__(self):
        if len(self.vertices) < 3:
            raise ValueError(f"Coverage polygon must have at least 3 vertices, got {len(self.vertices)}")
