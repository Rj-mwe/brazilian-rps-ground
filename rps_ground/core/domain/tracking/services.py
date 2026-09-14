"""
Domain Services for Tracking Sub-Core.
Pure mathematical routines for trajectory analysis and road matching.
"""
from typing import List, Optional, Tuple

from rps_ground.core.domain.geodesy.services import GeodeticDistanceCalculator
from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.tracking.entities import RoadSegmentEntity


class RoadMatchingService:
    """Calculates cross-track distance between a track point and road polylines."""

    @classmethod
    def distance_to_segment_m(
        cls,
        point: GeodeticCoordinatesVO,
        road: RoadSegmentEntity
    ) -> float:
        """Approximate minimal distance from point to any waypoint in road segment."""
        min_dist = float("inf")
        for wp in road.waypoints:
            d = GeodeticDistanceCalculator.haversine_distance_m(point, wp)
            if d < min_dist:
                min_dist = d
        return min_dist

    @classmethod
    def find_nearest_road(
        cls,
        point: GeodeticCoordinatesVO,
        roads: List[RoadSegmentEntity]
    ) -> Tuple[Optional[RoadSegmentEntity], float]:
        """Find the nearest road segment and distance in meters."""
        if not roads:
            return None, float("inf")

        best_road: Optional[RoadSegmentEntity] = None
        best_dist = float("inf")

        for road in roads:
            d = cls.distance_to_segment_m(point, road)
            if d < best_dist:
                best_dist = d
                best_road = road

        return best_road, best_dist
