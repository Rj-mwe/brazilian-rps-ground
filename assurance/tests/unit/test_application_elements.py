"""
Unit tests for Application Layer (Services, DTOs, Mappers, Interfaces, Governance).
"""
from datetime import datetime, timezone

import pytest

from rps_ground.core.application.dtos.ground_dtos import (
    GroundStationDTO,
    SignalReceptionDTO,
    VehicleTrackDTO,
)
from rps_ground.core.application.governance.integrity_censor import GroundDataIntegrityCensor
from rps_ground.core.application.governance.temporal_barrier import GroundTemporalBarrier
from rps_ground.core.application.interfaces.storage_interfaces import (
    IGroundStationStorageInterface,
    ISignalLogStorageInterface,
    ITrajectoryStorageInterface,
)
from rps_ground.core.application.mappers.spatial_mapper import GroundSpatialMapper
from rps_ground.core.application.services.ground_use_cases import (
    IngestStationCoverageUseCase,
    LogConstellationSignalUseCase,
    RecordVehicleTrajectoryUseCase,
)
from rps_ground.core.domain.geodesy.value_objects import BoundingBoxVO, GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.telemetry.value_objects import ConstellationSignalLogVO

# ==============================================================================
# In-Memory Test Doubles for Interfaces
# ==============================================================================

class InMemoryStationStorage(IGroundStationStorageInterface):
    def __init__(self):
        self.stations = {}

    def save_station(self, station: GroundStationEntity) -> None:
        self.stations[station.code] = station

    def get_station_by_code(self, code: str):
        return self.stations.get(code)

    def list_all_stations(self):
        return list(self.stations.values())

    def find_covering_stations(self, coords: GeodeticCoordinatesVO):
        return [
            s for s in self.stations.values()
            if s.is_operational and s.coverage_polygon is not None
        ]


class InMemoryTrajectoryStorage(ITrajectoryStorageInterface):
    def __init__(self):
        self.points = []

    def record_track_points(self, points):
        self.points.extend(points)

    def get_trajectory(self, vehicle_id, start_time, end_time):
        return [p for p in self.points if p.vehicle_id == vehicle_id and start_time <= p.timestamp <= end_time]

    def find_tracks_within_bounds(self, bbox: BoundingBoxVO):
        return [p for p in self.points if bbox.contains(p.position)]


class InMemorySignalStorage(ISignalLogStorageInterface):
    def __init__(self):
        self.logs = []

    def log_signal_receptions(self, records):
        self.logs.extend(records)

    def query_receptions_by_station(self, station_code, limit=100):
        return [r for r in self.logs if r.station_code == station_code][:limit]


# ==============================================================================
# Tests
# ==============================================================================

def test_ground_spatial_mapper_station():
    dto = GroundStationDTO(
        code="SJC",
        name="Estacao SJC ITA",
        station_type="AEROSPACE_RESEARCH",
        latitude=-23.210,
        longitude=-45.880,
        altitude=660.0,
        elevation_mask_deg=5.0,
        coverage_radius_km=1200.0,
        is_operational=True
    )
    entity = GroundSpatialMapper.station_dto_to_entity(dto)
    assert entity.code == "SJC"
    assert entity.location.latitude_deg == -23.210
    assert entity.coverage_polygon is not None

    dto_back = GroundSpatialMapper.station_entity_to_dto(entity)
    assert dto_back.code == dto.code
    assert dto_back.latitude == dto.latitude


def test_ingest_station_coverage_use_case():
    storage = InMemoryStationStorage()
    uc = IngestStationCoverageUseCase(storage=storage)

    # Seed all 5 canonical stations
    seeded = uc.seed_canonical_stations()
    assert len(seeded) == 5
    assert len(storage.stations) == 5
    assert "SJC" in storage.stations
    assert "CPQ" in storage.stations


def test_record_trajectory_use_case():
    storage = InMemoryTrajectoryStorage()
    uc = RecordVehicleTrajectoryUseCase(trajectory_storage=storage)

    dtos = [
        VehicleTrackDTO(
            vehicle_id="CAR-01",
            timestamp=datetime(2026, 9, 14, 10, 0, 0, tzinfo=timezone.utc),
            latitude=-23.210,
            longitude=-45.880,
            altitude=660.0,
            speed_mps=15.0,
            heading_deg=45.0,
            pdop=1.2,
            fix_status="3D_FIX"
        ),
        VehicleTrackDTO(
            vehicle_id="CAR-01",
            timestamp=datetime(2026, 9, 14, 10, 0, 5, tzinfo=timezone.utc),
            latitude=-23.208,
            longitude=-45.878,
            altitude=660.0,
            speed_mps=16.0,
            heading_deg=45.0,
            pdop=1.2,
            fix_status="3D_FIX"
        )
    ]
    session = uc.record_track_batch("SESS-01", dtos)
    assert session.point_count == 2
    assert len(storage.points) == 2


def test_log_constellation_signal_use_case_with_integrity():
    storage = InMemorySignalStorage()
    uc = LogConstellationSignalUseCase(storage=storage)

    dtos = [
        # Valid signal
        SignalReceptionDTO(
            timestamp=datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc),
            station_code="SJC",
            satellite_id=1,
            satellite_type="GEO",
            elevation_deg=70.0,
            azimuth_deg=10.0,
            pseudorange_m=37500000.0,
            c_n0_dbhz=45.0,
            doppler_hz=0.0
        ),
        # Corrupted / invalid signal (out of bounds range)
        SignalReceptionDTO(
            timestamp=datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc),
            station_code="SJC",
            satellite_id=2,
            satellite_type="GEO",
            elevation_deg=70.0,
            azimuth_deg=10.0,
            pseudorange_m=1000.0,  # 1 km range is impossible
            c_n0_dbhz=45.0,
            doppler_hz=0.0
        )
    ]

    logged = uc.log_signals(dtos, enforce_integrity=True)
    assert logged == 1
    assert len(storage.logs) == 1
    assert storage.logs[0].satellite_id == 1


# ==============================================================================
# Governance Sub-Core Tests
# ==============================================================================

def test_temporal_barrier_monotonic_progression():
    t0 = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 9, 14, 12, 0, 1, tzinfo=timezone.utc)
    t_past = datetime(2026, 9, 14, 11, 59, 59, tzinfo=timezone.utc)

    barrier = GroundTemporalBarrier(initial_time=t0)
    assert barrier.current_time == t0

    barrier.advance_time(t1)
    assert barrier.current_time == t1

    with pytest.raises(ValueError, match="Temporal barrier violation"):
        barrier.advance_time(t_past)


def test_data_integrity_censor_quarantine():
    censor = GroundDataIntegrityCensor()

    sig_good = ConstellationSignalLogVO(
        timestamp=datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc),
        station_code="SJC",
        satellite_id=1,
        satellite_type="GEO",
        elevation_deg=60.0,
        azimuth_deg=350.0,
        pseudorange_m=38000000.0,
        c_n0_dbhz=40.0
    )
    sig_bad = ConstellationSignalLogVO(
        timestamp=datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc),
        station_code="SJC",
        satellite_id=2,
        satellite_type="GEO",
        elevation_deg=60.0,
        azimuth_deg=350.0,
        pseudorange_m=38000000.0,
        c_n0_dbhz=10.0  # Very low SNR
    )

    admitted, rejected = censor.censor_signal_batch([sig_good, sig_bad])
    assert len(admitted) == 1
    assert len(rejected) == 1
    assert len(censor.quarantine_records) == 1
