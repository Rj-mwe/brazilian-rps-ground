"""
Domain Policies for Tracking Sub-Core.
"""
from typing import List

from rps_ground.core.domain.geodesy.services import GeodeticDistanceCalculator
from rps_ground.core.domain.tracking.value_objects import VehicleTrackPointVO


class TrajectoryDecimationPolicy:
    """
    Decimates high-rate trajectory points to reduce spatial storage footprint
    while preserving trajectory curvature and velocity anomalies.
    """

    def __init__(self, min_distance_m: float = 10.0, min_time_delta_sec: float = 1.0):
        self.min_distance_m = min_distance_m
        self.min_time_delta_sec = min_time_delta_sec

    def filter_points(self, points: List[VehicleTrackPointVO]) -> List[VehicleTrackPointVO]:
        if not points:
            return []

        filtered = [points[0]]
        for pt in points[1:]:
            last = filtered[-1]
            dist = GeodeticDistanceCalculator.haversine_distance_m(last.position, pt.position)
            time_delta = (pt.timestamp - last.timestamp).total_seconds()

            if dist >= self.min_distance_m or time_delta >= self.min_time_delta_sec:
                filtered.append(pt)

        return filtered
