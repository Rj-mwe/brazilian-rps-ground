"""
Integration tests for PostGIS Persistence (US124).
Executes against active PostgreSQL + PostGIS native instance.
Gracefully skips if the native database is not yet enabled/running on the host.
"""
from datetime import datetime, timezone

import pytest

from rps_ground.adapters.postgis_sink.postgis_repository import PostgisSpatialRepository
from rps_ground.adapters.postgis_sink.schema import Base
from rps_ground.core.domain.geodesy.value_objects import BoundingBoxVO, GeodeticCoordinatesVO
from rps_ground.core.domain.stations.factories import GroundStationFactory
from rps_ground.core.domain.telemetry.value_objects import ConstellationSignalLogVO
from rps_ground.core.domain.tracking.factories import RoadNetworkFactory
from rps_ground.core.domain.tracking.value_objects import VehicleTrackPointVO
from rps_ground.infrastructure.persistence.database_substrate import DatabaseSubstrate

db_substrate = DatabaseSubstrate.get_instance()
is_db_ready = db_substrate.health_check()


@pytest.mark.skipif(
    not is_db_ready,
    reason="Native PostgreSQL/PostGIS database is not active yet (waiting for BTRFS NoCOW setup)"
)
class TestPostgisPersistenceIntegration:
    """End-to-End integration tests for US124 with active PostGIS backend."""

    @classmethod
    def setup_class(cls):
        """Ensure schema and extensions are initialized before running integration tests."""
        assert db_substrate.initialize_schema(Base.metadata, create_extension=True)
        cls.repo = PostgisSpatialRepository(db_substrate=db_substrate)

    def test_postgis_extension_version(self):
        ver = db_substrate.postgis_check()
        assert ver is not None
        assert "3." in ver

    def test_stations_persistence_and_spatial_containment(self):
        stations = GroundStationFactory.create_canonical_stations()
        for s in stations:
            self.repo.save_station(s)

        # Retrieve SJC
        sjc = self.repo.get_station_by_code("SJC")
        assert sjc is not None
        assert sjc.code == "SJC"
        assert sjc.location.latitude_deg == -23.210

        # Spatial query: Taubaté/SP is inside SJC and CPQ footprints
        taubate = GeodeticCoordinatesVO(latitude_deg=-23.030, longitude_deg=-45.560, altitude_m=580.0)
        covering = self.repo.find_covering_stations(taubate)
        codes = [c.code for c in covering]
        assert "SJC" in codes
        assert "CPQ" in codes

    def test_road_network_persistence_and_dwithin_query(self):
        corridors = RoadNetworkFactory.create_canonical_corridors()
        for c in corridors:
            self.repo.save_road_segment(c)

        dutra = self.repo.get_road_segment("BR116-SJC-CPQ")
        assert dutra is not None
        assert dutra.road_code == "BR-116"

        # Spatial query: ITA point within 2000m from Dutra
        ita_point = GeodeticCoordinatesVO(latitude_deg=-23.212, longitude_deg=-45.878, altitude_m=660.0)
        nearby = self.repo.find_nearby_roads(ita_point, distance_meters=2000.0)
        assert len(nearby) >= 1
        assert any(r.road_code == "BR-116" for r in nearby)

    def test_vehicle_trajectory_persistence_and_bbox_query(self):
        points = [
            VehicleTrackPointVO(
                vehicle_id="BR-VEH-124",
                timestamp=datetime(2026, 9, 14, 14, 0, 0, tzinfo=timezone.utc),
                position=GeodeticCoordinatesVO(-23.210, -45.880, 660.0),
                speed_mps=20.0
            ),
            VehicleTrackPointVO(
                vehicle_id="BR-VEH-124",
                timestamp=datetime(2026, 9, 14, 14, 0, 10, tzinfo=timezone.utc),
                position=GeodeticCoordinatesVO(-23.208, -45.875, 658.0),
                speed_mps=22.0
            )
        ]
        self.repo.record_track_points(points)

        traj = self.repo.get_trajectory(
            vehicle_id="BR-VEH-124",
            start_time=datetime(2026, 9, 14, 13, 0, 0, tzinfo=timezone.utc),
            end_time=datetime(2026, 9, 14, 15, 0, 0, tzinfo=timezone.utc)
        )
        assert len(traj) >= 2

        bbox = BoundingBoxVO(min_lat=-23.5, min_lon=-46.0, max_lat=-23.0, max_lon=-45.5)
        in_box = self.repo.find_tracks_within_bounds(bbox)
        assert len(in_box) >= 2

    def test_satellite_signal_telemetry_persistence(self):
        signals = [
            ConstellationSignalLogVO(
                timestamp=datetime(2026, 9, 14, 15, 0, 0, tzinfo=timezone.utc),
                station_code="SJC",
                satellite_id=1,
                satellite_type="GEO",
                elevation_deg=65.0,
                azimuth_deg=330.0,
                pseudorange_m=37600000.0,
                c_n0_dbhz=44.2,
                doppler_hz=120.0
            )
        ]
        self.repo.log_signal_receptions(signals)

        queried = self.repo.query_receptions_by_station("SJC", limit=10)
        assert len(queried) >= 1
        assert queried[0].satellite_id == 1
