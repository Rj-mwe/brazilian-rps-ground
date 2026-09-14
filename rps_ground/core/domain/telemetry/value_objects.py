"""
Value Objects for Telemetry Domain Sub-Core.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ConstellationSignalLogVO:
    """
    Immutable observation record of a satellite signal received by a ground station.
    """
    timestamp: datetime
    station_code: str
    satellite_id: int
    satellite_type: str                   # 'GEO' or 'IGSO'
    elevation_deg: float
    azimuth_deg: float
    pseudorange_m: float
    c_n0_dbhz: float                      # Carrier-to-Noise density ratio (dB-Hz)
    doppler_hz: float = 0.0
    los_valid: bool = True

    def __post_init__(self):
        if not (-90.0 <= self.elevation_deg <= 90.0):
            raise ValueError(f"Elevation must be in [-90, 90] degrees, got {self.elevation_deg}")
        if not (0.0 <= self.azimuth_deg <= 360.0):
            raise ValueError(f"Azimuth must be in [0, 360] degrees, got {self.azimuth_deg}")
        if self.pseudorange_m < 0.0:
            raise ValueError(f"Pseudorange cannot be negative, got {self.pseudorange_m}")


@dataclass(frozen=True)
class SignalQualityVO:
    """Immutable metrics of signal quality and channel integrity."""
    snr_db: float
    multipath_metric_m: float = 0.0
    cycle_slip_detected: bool = False
