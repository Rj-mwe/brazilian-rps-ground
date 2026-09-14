"""
Data Transfer Objects (DTOs) for Application Layer.
Immutable boundary contracts shielding the Core domain from edge serialization formats.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Tuple


@dataclass(frozen=True)
class GroundStationDTO:
    code: str
    name: str
    station_type: str
    latitude: float
    longitude: float
    altitude: float
    elevation_mask_deg: float
    coverage_radius_km: float
    is_operational: bool = True


@dataclass(frozen=True)
class VehicleTrackDTO:
    vehicle_id: str
    timestamp: datetime
    latitude: float
    longitude: float
    altitude: float
    speed_mps: float
    heading_deg: float
    pdop: float
    fix_status: str


@dataclass(frozen=True)
class RoadSegmentDTO:
    segment_id: str
    name: str
    road_code: str
    road_type: str
    waypoints: Tuple[Tuple[float, float, float], ...]  # (lat, lon, alt)
    length_meters: float


@dataclass(frozen=True)
class SignalReceptionDTO:
    timestamp: datetime
    station_code: str
    satellite_id: int
    satellite_type: str
    elevation_deg: float
    azimuth_deg: float
    pseudorange_m: float
    c_n0_dbhz: float
    doppler_hz: float = 0.0
    los_valid: bool = True
