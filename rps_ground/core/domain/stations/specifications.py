"""
Domain Specifications for Stations Sub-Core.
Boolean predicate specifications following the Specification pattern.
"""
from rps_ground.core.domain.geodesy.services import GeodeticDistanceCalculator
from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity


class ElevationMaskSatisfiedSpecification:
    """Predicate evaluating if an incoming signal exceeds the station elevation cutoff mask."""

    @classmethod
    def is_satisfied_by(cls, station: GroundStationEntity, observed_elevation_deg: float) -> bool:
        return observed_elevation_deg >= station.elevation_mask_deg


class StationOperationalSpecification:
    """Predicate evaluating if a station is currently operational."""

    @classmethod
    def is_satisfied_by(cls, station: GroundStationEntity) -> bool:
        return station.is_operational


class WithinStationCoverageSpecification:
    """Predicate evaluating if a ground coordinate falls within station coverage radius."""

    @classmethod
    def is_satisfied_by(cls, station: GroundStationEntity, target: GeodeticCoordinatesVO) -> bool:
        dist_m = GeodeticDistanceCalculator.haversine_distance_m(station.location, target)
        return dist_m <= (station.coverage_radius_km * 1000.0)
