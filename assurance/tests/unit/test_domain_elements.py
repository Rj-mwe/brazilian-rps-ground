"""
Unit tests for the 8 tactical domain elements of Brazilian RPS Ground Segment.
"""
from datetime import datetime, timezone

import pytest

from rps_ground.core.domain.geodesy.services import GeodeticDistanceCalculator
from rps_ground.core.domain.geodesy.value_objects import BoundingBoxVO, GeodeticCoordinatesVO
from rps_ground.core.domain.stations.aggregates import GroundStationNetworkAggregate
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.stations.factories import GroundStationFactory
from rps_ground.core.domain.stations.policies import RimsCoverageRedundancyPolicy
from rps_ground.core.domain.stations.specifications import (
    ElevationMaskSatisfiedSpecification,
)
from rps_ground.core.domain.stations.value_objects import StationType
from rps_ground.core.domain.telemetry.specifications import SignalIntegrityValidSpecification
from rps_ground.core.domain.telemetry.value_objects import ConstellationSignalLogVO
from rps_ground.core.domain.tracking.aggregates import VehicleTrackingSessionAggregate
from rps_ground.core.domain.tracking.factories import RoadNetworkFactory
from rps_ground.core.domain.tracking.policies import TrajectoryDecimationPolicy
from rps_ground.core.domain.tracking.services import RoadMatchingService
from rps_ground.core.domain.tracking.value_objects import RoadType, VehicleTrackPointVO

# ==============================================================================
# 1. Geodesy Sub-Core Tests
# ==============================================================================

def test_geodetic_coordinates_immutability_and_validation():
    coord = GeodeticCoordinatesVO(latitude_deg=-23.210, longitude_deg=-45.880, altitude_m=660.0)
    assert coord.latitude_deg == -23.210
    assert coord.longitude_deg == -45.880
    assert coord.altitude_m == 660.0
    assert coord.srid == 4326

    # Invariants
    with pytest.raises(ValueError, match="Latitude must be in"):
        GeodeticCoordinatesVO(latitude_deg=95.0, longitude_deg=0.0)

    with pytest.raises(ValueError, match="Longitude must be in"):
        GeodeticCoordinatesVO(latitude_deg=0.0, longitude_deg=-185.0)


def test_bounding_box_and_containment():
    bbox = BoundingBoxVO(min_lat=-25.0, min_lon=-48.0, max_lat=-20.0, max_lon=-44.0)
    sjc = GeodeticCoordinatesVO(-23.210, -45.880, 660.0)
    brasilia = GeodeticCoordinatesVO(-15.794, -47.882, 1172.0)

    assert bbox.contains(sjc) is True
    assert bbox.contains(brasilia) is False

    with pytest.raises(ValueError, match="cannot exceed"):
        BoundingBoxVO(min_lat=-20.0, min_lon=0.0, max_lat=-25.0, max_lon=0.0)


def test_geodetic_distance_calculator_sjc_cpq():
    sjc = GeodeticCoordinatesVO(-23.210, -45.880, 660.0)
    cpq = GeodeticCoordinatesVO(-22.686, -45.007, 565.0)

    dist_m = GeodeticDistanceCalculator.haversine_distance_m(sjc, cpq)
    # Direct distance SJC to Cachoeira Paulista is ~106 km
    assert 100000.0 < dist_m < 115000.0

    bearing = GeodeticDistanceCalculator.initial_bearing_deg(sjc, cpq)
    # SJC to CPQ bearing is northeast (~50-60 degrees)
    assert 45.0 < bearing < 65.0


# ==============================================================================
# 2. Stations Sub-Core Tests (SJC, ALC, NAT, BSB, CPQ)
# ==============================================================================

def test_canonical_stations_factory():
    stations = GroundStationFactory.create_canonical_stations()
    assert len(stations) == 5

    station_codes = [s.code for s in stations]
    assert "SJC" in station_codes
    assert "ALC" in station_codes
    assert "NAT" in station_codes
    assert "BSB" in station_codes
    assert "CPQ" in station_codes

    sjc = next(s for s in stations if s.code == "SJC")
    assert sjc.station_type == StationType.AEROSPACE_RESEARCH
    assert sjc.coverage_polygon is not None
    assert len(sjc.coverage_polygon.vertices) >= 24


def test_station_network_aggregate_and_specifications():
    stations = GroundStationFactory.create_canonical_stations()
    net = GroundStationNetworkAggregate(network_id="BR-RIMS-NET")
    for s in stations:
        net.register_station(s)

    assert net.total_count == 5
    assert net.operational_count == 5

    # Target point in Taubaté/SP (between SJC and CPQ)
    taubate = GeodeticCoordinatesVO(-23.030, -45.560, 580.0)
    covering = net.find_covering_stations(taubate)
    # SJC and CPQ should both cover Taubaté
    covering_codes = [s.code for s in covering]
    assert "SJC" in covering_codes
    assert "CPQ" in covering_codes

    # Redundancy policy
    policy = RimsCoverageRedundancyPolicy(min_redundancy=2)
    assert policy.evaluate_redundancy(stations, taubate) is True


def test_elevation_mask_specification():
    sjc = GroundStationEntity(
        code="SJC",
        name="SJC",
        station_type=StationType.AEROSPACE_RESEARCH,
        location=GeodeticCoordinatesVO(-23.210, -45.880, 660.0),
        elevation_mask_deg=5.0
    )
    assert ElevationMaskSatisfiedSpecification.is_satisfied_by(sjc, 12.0) is True
    assert ElevationMaskSatisfiedSpecification.is_satisfied_by(sjc, 3.5) is False


# ==============================================================================
# 3. Tracking Sub-Core Tests (Trajectories & Road Network)
# ==============================================================================

def test_road_network_factory_canonical_corridors():
    corridors = RoadNetworkFactory.create_canonical_corridors()
    assert len(corridors) == 2

    dutra = next(c for c in corridors if c.road_code == "BR-116")
    assert dutra.road_type == RoadType.HIGHWAY_FEDERAL
    assert len(dutra.waypoints) >= 6
    assert dutra.length_meters > 100000.0  # > 100 km


def test_tracking_session_aggregate_monotonicity():
    session = VehicleTrackingSessionAggregate(session_id="TRK-001", vehicle_id="FAB-V01")

    p1 = VehicleTrackPointVO(
        vehicle_id="FAB-V01",
        timestamp=datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc),
        position=GeodeticCoordinatesVO(-23.210, -45.880, 660.0),
        speed_mps=20.0
    )
    p2 = VehicleTrackPointVO(
        vehicle_id="FAB-V01",
        timestamp=datetime(2026, 9, 14, 12, 0, 10, tzinfo=timezone.utc),
        position=GeodeticCoordinatesVO(-23.208, -45.875, 658.0),
        speed_mps=22.0
    )
    session.record_point(p1)
    session.record_point(p2)
    assert session.point_count == 2

    # Retrograde timestamp violation
    p_retro = VehicleTrackPointVO(
        vehicle_id="FAB-V01",
        timestamp=datetime(2026, 9, 14, 11, 59, 0, tzinfo=timezone.utc),
        position=GeodeticCoordinatesVO(-23.215, -45.885, 660.0)
    )
    with pytest.raises(ValueError, match="Timestamp violation"):
        session.record_point(p_retro)


def test_trajectory_decimation_policy():
    policy = TrajectoryDecimationPolicy(min_distance_m=50.0, min_time_delta_sec=5.0)

    # Point 1
    p1 = VehicleTrackPointVO(
        vehicle_id="V1",
        timestamp=datetime(2026, 9, 14, 10, 0, 0, tzinfo=timezone.utc),
        position=GeodeticCoordinatesVO(-23.210, -45.880, 660.0)
    )
    # Point 2: only 0.5s later and 2 meters away -> should be filtered out
    p2 = VehicleTrackPointVO(
        vehicle_id="V1",
        timestamp=datetime(2026, 9, 14, 10, 0, 0, 500000, tzinfo=timezone.utc),
        position=GeodeticCoordinatesVO(-23.21001, -45.88001, 660.0)
    )
    # Point 3: 10 seconds later and 200 meters away -> should be kept
    p3 = VehicleTrackPointVO(
        vehicle_id="V1",
        timestamp=datetime(2026, 9, 14, 10, 0, 10, tzinfo=timezone.utc),
        position=GeodeticCoordinatesVO(-23.208, -45.878, 660.0)
    )

    filtered = policy.filter_points([p1, p2, p3])
    assert len(filtered) == 2
    assert filtered[0] == p1
    assert filtered[1] == p3


def test_road_matching_service():
    corridors = RoadNetworkFactory.create_canonical_corridors()
    # Point at ITA campus (very close to SJC Dutra point)
    ita_point = GeodeticCoordinatesVO(-23.212, -45.878, 660.0)
    best_road, dist_m = RoadMatchingService.find_nearest_road(ita_point, corridors)

    assert best_road is not None
    assert dist_m < 1500.0  # Under 1.5 km


# ==============================================================================
# 4. Telemetry Sub-Core Tests (Signals)
# ==============================================================================

def test_signal_integrity_specification():
    # Valid GEO satellite signal (~37,500 km range, 42 dB-Hz)
    valid_sig = ConstellationSignalLogVO(
        timestamp=datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc),
        station_code="SJC",
        satellite_id=1,
        satellite_type="GEO",
        elevation_deg=65.0,
        azimuth_deg=340.0,
        pseudorange_m=37500000.0,
        c_n0_dbhz=42.5,
        doppler_hz=150.0,
        los_valid=True
    )
    assert SignalIntegrityValidSpecification.is_satisfied_by(valid_sig) is True

    # Bad range (e.g. 5,000 km, impossible for GEO/IGSO)
    bad_range = ConstellationSignalLogVO(
        timestamp=datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc),
        station_code="SJC",
        satellite_id=1,
        satellite_type="GEO",
        elevation_deg=65.0,
        azimuth_deg=340.0,
        pseudorange_m=5000000.0,
        c_n0_dbhz=42.5
    )
    assert SignalIntegrityValidSpecification.is_satisfied_by(bad_range) is False

    # Low SNR (e.g. 15 dB-Hz)
    low_snr = ConstellationSignalLogVO(
        timestamp=datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc),
        station_code="SJC",
        satellite_id=1,
        satellite_type="GEO",
        elevation_deg=65.0,
        azimuth_deg=340.0,
        pseudorange_m=37500000.0,
        c_n0_dbhz=15.0
    )
    assert SignalIntegrityValidSpecification.is_satisfied_by(low_snr) is False
