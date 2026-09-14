"""
Unit tests for PostGIS schema and geometry mappers.
"""

from rps_ground.adapters.postgis_sink.mappers import PostgisGeometryMapper, PostgisModelMapper
from rps_ground.adapters.postgis_sink.schema import (
    Base,
    GroundStationModel,
    VehicleTrackPointModel,
)
from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.stations.factories import GroundStationFactory
from rps_ground.core.domain.stations.value_objects import StationType


def test_schema_table_names_and_columns():
    table_names = list(Base.metadata.tables.keys())
    assert "ground_stations" in table_names
    assert "road_segments" in table_names
    assert "vehicle_track_points" in table_names
    assert "satellite_signal_logs" in table_names

    station_cols = [c.name for c in GroundStationModel.__table__.columns]
    assert "code" in station_cols
    assert "location" in station_cols
    assert "coverage_area" in station_cols

    track_cols = [c.name for c in VehicleTrackPointModel.__table__.columns]
    assert "vehicle_id" in track_cols
    assert "location" in track_cols
    assert "speed_mps" in track_cols


def test_geometry_mapper_pointz_wkt():
    coord = GeodeticCoordinatesVO(latitude_deg=-23.210, longitude_deg=-45.880, altitude_m=660.0)
    wkt_elem = PostgisGeometryMapper.pointz_to_wkt(coord)
    assert wkt_elem.srid == 4326
    # Longitude first, then latitude, then altitude
    assert "POINT Z (-45.88000000 -23.21000000 660.000)" in str(wkt_elem.data)


def test_geometry_mapper_polygon_wkt():
    sjc = GeodeticCoordinatesVO(-23.210, -45.880, 660.0)
    footprint = GroundStationFactory.create_circular_footprint(sjc, radius_km=100.0, num_vertices=8)
    poly_wkt = PostgisGeometryMapper.polygon_to_wkt(footprint)
    assert poly_wkt.srid == 4326
    assert "POLYGON ((" in str(poly_wkt.data)


def test_model_mapper_station_conversion():
    sjc = GeodeticCoordinatesVO(-23.210, -45.880, 660.0)
    entity = GroundStationEntity(
        code="SJC",
        name="Sao Jose dos Campos",
        station_type=StationType.AEROSPACE_RESEARCH,
        location=sjc,
        elevation_mask_deg=5.0
    )
    model = PostgisModelMapper.station_to_model(entity)
    assert model.code == "SJC"
    assert model.station_type == "AEROSPACE_RESEARCH"
    assert model.location is not None
