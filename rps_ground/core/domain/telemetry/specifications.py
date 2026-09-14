"""
Domain Specifications for Telemetry Sub-Core.
"""
from rps_ground.core.domain.telemetry.value_objects import ConstellationSignalLogVO


class SignalIntegrityValidSpecification:
    """
    Validates physical plausibility of received pseudorange and Carrier-to-Noise ratio
    for GEO and IGSO satellite signals.
    """

    MIN_GEO_IGSO_RANGE_M: float = 35000000.0  # 35,000 km
    MAX_GEO_IGSO_RANGE_M: float = 45000000.0  # 45,000 km
    MIN_USABLE_CN0_DBHZ: float = 28.0

    @classmethod
    def is_satisfied_by(cls, signal: ConstellationSignalLogVO) -> bool:
        if not signal.los_valid:
            return False
        if signal.c_n0_dbhz < cls.MIN_USABLE_CN0_DBHZ:
            return False
        if not (cls.MIN_GEO_IGSO_RANGE_M <= signal.pseudorange_m <= cls.MAX_GEO_IGSO_RANGE_M):
            return False
        return True
