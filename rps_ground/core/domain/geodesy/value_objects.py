"""
Value Objects for Geodesy Domain Sub-Core.
Immutable representation of geodetic coordinates and bounding boxes (SIRGAS2000 / WGS84).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GeodeticCoordinatesVO:
    """
    Immutable geodetic coordinate tuple (latitude, longitude, altitude).
    SRID defaults to 4326 (WGS84 / SIRGAS2000 compatible).
    """
    latitude_deg: float
    longitude_deg: float
    altitude_m: float = 0.0
    srid: int = 4326

    def __post_init__(self):
        if not (-90.0 <= self.latitude_deg <= 90.0):
            raise ValueError(f"Latitude must be in [-90, 90] degrees, got {self.latitude_deg}")
        if not (-180.0 <= self.longitude_deg <= 180.0):
            raise ValueError(f"Longitude must be in [-180, 180] degrees, got {self.longitude_deg}")
        if self.srid <= 0:
            raise ValueError(f"SRID must be positive, got {self.srid}")


@dataclass(frozen=True)
class BoundingBoxVO:
    """Immutable 2D geographical bounding box."""
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float

    def __post_init__(self):
        if self.min_lat > self.max_lat:
            raise ValueError(f"min_lat ({self.min_lat}) cannot exceed max_lat ({self.max_lat})")
        if self.min_lon > self.max_lon:
            raise ValueError(f"min_lon ({self.min_lon}) cannot exceed max_lon ({self.max_lon})")

    def contains(self, coord: GeodeticCoordinatesVO) -> bool:
        return (
            self.min_lat <= coord.latitude_deg <= self.max_lat
            and self.min_lon <= coord.longitude_deg <= self.max_lon
        )
