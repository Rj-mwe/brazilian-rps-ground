"""
Domain Services for Geodesy Sub-Core.
Pure mathematical and geodetic algorithms on the reference ellipsoid/sphere.
"""
import math

from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO


class GeodeticDistanceCalculator:
    """Calculates ground distances, bearings, and line-of-sight elevation angles."""

    EARTH_RADIUS_M: float = 6371000.0  # Mean spherical Earth radius

    @classmethod
    def haversine_distance_m(cls, p1: GeodeticCoordinatesVO, p2: GeodeticCoordinatesVO) -> float:
        """Calculate great-circle distance between two points on the Earth surface in meters."""
        lat1_rad = math.radians(p1.latitude_deg)
        lat2_rad = math.radians(p2.latitude_deg)
        dlat_rad = math.radians(p2.latitude_deg - p1.latitude_deg)
        dlon_rad = math.radians(p2.longitude_deg - p1.longitude_deg)

        a = (
            math.sin(dlat_rad / 2.0) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon_rad / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return cls.EARTH_RADIUS_M * c

    @classmethod
    def initial_bearing_deg(cls, p1: GeodeticCoordinatesVO, p2: GeodeticCoordinatesVO) -> float:
        """Calculate initial compass bearing from p1 to p2 in degrees [0, 360)."""
        lat1_rad = math.radians(p1.latitude_deg)
        lat2_rad = math.radians(p2.latitude_deg)
        dlon_rad = math.radians(p2.longitude_deg - p1.longitude_deg)

        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (
            math.cos(lat1_rad) * math.sin(lat2_rad)
            - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
        )
        bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
        return bearing

    @classmethod
    def elevation_angle_deg(
        cls,
        station: GeodeticCoordinatesVO,
        target: GeodeticCoordinatesVO
    ) -> float:
        """
        Estimate approximate line-of-sight elevation angle from ground station to target.
        Returns angle in degrees [-90, +90].
        """
        ground_dist = cls.haversine_distance_m(station, target)
        alt_diff = target.altitude_m - station.altitude_m

        if ground_dist == 0.0:
            return 90.0 if alt_diff >= 0.0 else -90.0

        angle_rad = math.atan2(alt_diff, ground_dist)
        return math.degrees(angle_rad)
