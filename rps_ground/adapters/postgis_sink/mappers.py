"""
PostGIS Sink Mappers.
Bidirectional translation between Core Domain Entities/VOs and PostGIS ORM Models / Geometries.
"""
from typing import Any

from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape

from rps_ground.adapters.postgis_sink.schema import (
    GroundStationModel,
    RoadSegmentModel,
    SatelliteSignalLogModel,
    VehicleTrackPointModel,
)
from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.stations.value_objects import CoveragePolygonVO, StationType
from rps_ground.core.domain.telemetry.value_objects import ConstellationSignalLogVO
from rps_ground.core.domain.tracking.entities import RoadSegmentEntity
from rps_ground.core.domain.tracking.value_objects import RoadType, VehicleTrackPointVO


class PostgisGeometryMapper:
    """Handles PostGIS WKT/WKB transformations for GeoAlchemy2."""

    @staticmethod
    def pointz_to_wkt(coord: GeodeticCoordinatesVO) -> WKTElement:
        """Convert 3D geodetic coordinate (lat, lon, alt) to POINT Z (lon lat alt) WKT."""
        wkt = f"POINT Z ({coord.longitude_deg:.8f} {coord.latitude_deg:.8f} {coord.altitude_m:.3f})"
        return WKTElement(wkt, srid=4326)

    @staticmethod
    def polygon_to_wkt(poly: CoveragePolygonVO) -> WKTElement:
        """Convert closed CoveragePolygonVO to 2D POLYGON WKT."""
        pairs = [f"{v.longitude_deg:.8f} {v.latitude_deg:.8f}" for v in poly.vertices]
        wkt = f"POLYGON (({', '.join(pairs)}))"
        return WKTElement(wkt, srid=4326)

    @staticmethod
    def linestring_to_wkt(waypoints: tuple) -> WKTElement:
        """Convert waypoints sequence to 2D LINESTRING WKT."""
        pairs = [f"{wp.longitude_deg:.8f} {wp.latitude_deg:.8f}" for wp in waypoints]
        wkt = f"LINESTRING ({', '.join(pairs)})"
        return WKTElement(wkt, srid=4326)

    @classmethod
    def shape_to_pointz(cls, geom: Any) -> GeodeticCoordinatesVO:
        """Convert GeoAlchemy2 geometry element to GeodeticCoordinatesVO."""
        shape = to_shape(geom)
        coords = shape.coords[0]
        lon, lat = coords[0], coords[1]
        alt = coords[2] if len(coords) > 2 else 0.0
        return GeodeticCoordinatesVO(latitude_deg=lat, longitude_deg=lon, altitude_m=alt)

    @classmethod
    def shape_to_polygon(cls, geom: Any) -> CoveragePolygonVO:
        """Convert GeoAlchemy2 polygon element to CoveragePolygonVO."""
        shape = to_shape(geom)
        exterior_coords = list(shape.exterior.coords)
        vertices = tuple(
            GeodeticCoordinatesVO(latitude_deg=pt[1], longitude_deg=pt[0])
            for pt in exterior_coords
        )
        return CoveragePolygonVO(vertices=vertices)

    @classmethod
    def shape_to_waypoints(cls, geom: Any) -> tuple:
        """Convert GeoAlchemy2 linestring element to waypoints tuple."""
        shape = to_shape(geom)
        return tuple(
            GeodeticCoordinatesVO(latitude_deg=pt[1], longitude_deg=pt[0])
            for pt in shape.coords
        )


class PostgisModelMapper:
    """Maps between domain models and SQLAlchemy ORM models."""

    @classmethod
    def station_to_model(cls, entity: GroundStationEntity) -> GroundStationModel:
        loc_wkt = PostgisGeometryMapper.pointz_to_wkt(entity.location)
        cov_wkt = (
            PostgisGeometryMapper.polygon_to_wkt(entity.coverage_polygon)
            if entity.coverage_polygon
            else None
        )
        return GroundStationModel(
            code=entity.code,
            name=entity.name,
            station_type=entity.station_type.value,
            elevation_mask_deg=entity.elevation_mask_deg,
            coverage_radius_km=entity.coverage_radius_km,
            is_operational=entity.is_operational,
            location=loc_wkt,
            coverage_area=cov_wkt
        )

    @classmethod
    def model_to_station(cls, model: GroundStationModel) -> GroundStationEntity:
        location = PostgisGeometryMapper.shape_to_pointz(model.location)
        cov_poly = (
            PostgisGeometryMapper.shape_to_polygon(model.coverage_area)
            if model.coverage_area is not None
            else None
        )
        return GroundStationEntity(
            code=model.code,
            name=model.name,
            station_type=StationType(model.station_type),
            location=location,
            elevation_mask_deg=model.elevation_mask_deg,
            coverage_radius_km=model.coverage_radius_km,
            coverage_polygon=cov_poly,
            is_operational=model.is_operational
        )

    @classmethod
    def track_point_to_model(cls, vo: VehicleTrackPointVO, session_id: str = "DEFAULT") -> VehicleTrackPointModel:
        loc_wkt = PostgisGeometryMapper.pointz_to_wkt(vo.position)
        return VehicleTrackPointModel(
            vehicle_id=vo.vehicle_id,
            session_id=session_id,
            timestamp=vo.timestamp,
            location=loc_wkt,
            speed_mps=vo.speed_mps,
            heading_deg=vo.heading_deg,
            pdop=vo.pdop,
            fix_status=vo.fix_status
        )

    @classmethod
    def model_to_track_point(cls, model: VehicleTrackPointModel) -> VehicleTrackPointVO:
        location = PostgisGeometryMapper.shape_to_pointz(model.location)
        return VehicleTrackPointVO(
            vehicle_id=model.vehicle_id,
            timestamp=model.timestamp,
            position=location,
            speed_mps=model.speed_mps,
            heading_deg=model.heading_deg,
            pdop=model.pdop,
            fix_status=model.fix_status
        )

    @classmethod
    def road_to_model(cls, entity: RoadSegmentEntity) -> RoadSegmentModel:
        geom_wkt = PostgisGeometryMapper.linestring_to_wkt(entity.waypoints)
        return RoadSegmentModel(
            segment_id=entity.segment_id,
            name=entity.name,
            road_code=entity.road_code,
            road_type=entity.road_type.value,
            length_meters=entity.length_meters,
            geom=geom_wkt
        )

    @classmethod
    def model_to_road(cls, model: RoadSegmentModel) -> RoadSegmentEntity:
        waypoints = PostgisGeometryMapper.shape_to_waypoints(model.geom)
        return RoadSegmentEntity(
            segment_id=model.segment_id,
            name=model.name,
            road_code=model.road_code,
            road_type=RoadType(model.road_type),
            waypoints=waypoints,
            length_meters=model.length_meters
        )

    @classmethod
    def signal_to_model(cls, vo: ConstellationSignalLogVO) -> SatelliteSignalLogModel:
        return SatelliteSignalLogModel(
            timestamp=vo.timestamp,
            station_code=vo.station_code,
            satellite_id=vo.satellite_id,
            satellite_type=vo.satellite_type,
            elevation_deg=vo.elevation_deg,
            azimuth_deg=vo.azimuth_deg,
            pseudorange_m=vo.pseudorange_m,
            c_n0_dbhz=vo.c_n0_dbhz,
            doppler_hz=vo.doppler_hz,
            los_geometry=None
        )

    @classmethod
    def model_to_signal(cls, model: SatelliteSignalLogModel) -> ConstellationSignalLogVO:
        return ConstellationSignalLogVO(
            timestamp=model.timestamp,
            station_code=model.station_code,
            satellite_id=model.satellite_id,
            satellite_type=model.satellite_type,
            elevation_deg=model.elevation_deg,
            azimuth_deg=model.azimuth_deg,
            pseudorange_m=model.pseudorange_m,
            c_n0_dbhz=model.c_n0_dbhz,
            doppler_hz=model.doppler_hz,
            los_valid=True
        )
