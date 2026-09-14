"""
Domain Specifications for Tracking Sub-Core.
"""
from rps_ground.core.domain.tracking.value_objects import VehicleTrackPointVO


class SpeedLimitSpecification:
    """Predicate evaluating if vehicle speed conforms to maximum permissible speed."""

    def __init__(self, max_speed_mps: float = 60.0):
        self.max_speed_mps = max_speed_mps

    def is_satisfied_by(self, point: VehicleTrackPointVO) -> bool:
        return point.speed_mps <= self.max_speed_mps


class ValidFixSpecification:
    """Predicate evaluating whether GNSS navigation fix is valid for differential ops."""

    @classmethod
    def is_satisfied_by(cls, point: VehicleTrackPointVO) -> bool:
        return point.fix_status in ("3D_FIX", "DGPS_FIX", "RTK_FIX", "SBAS_FIX") and point.pdop < 6.0
