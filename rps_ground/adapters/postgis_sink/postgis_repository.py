"""
PostGIS Repository Implementation.
Concrete implementation of Application storage interfaces utilizing PostgreSQL + PostGIS.
"""
from datetime import datetime
from typing import List, Optional

from geoalchemy2 import functions as func
from sqlalchemy import select

from rps_ground.adapters.postgis_sink.mappers import PostgisGeometryMapper, PostgisModelMapper
from rps_ground.adapters.postgis_sink.schema import (
    GroundStationModel,
    RoadSegmentModel,
    SatelliteSignalLogModel,
    VehicleTrackPointModel,
)
from rps_ground.core.application.interfaces.storage_interfaces import ISpatialStorageInterface
from rps_ground.core.domain.geodesy.value_objects import BoundingBoxVO, GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.telemetry.value_objects import ConstellationSignalLogVO
from rps_ground.core.domain.tracking.entities import RoadSegmentEntity
from rps_ground.core.domain.tracking.value_objects import VehicleTrackPointVO
from rps_ground.infrastructure.persistence.database_substrate import DatabaseSubstrate


class PostgisSpatialRepository(ISpatialStorageInterface):
    """
    Concrete spatial repository implementing ISpatialStorageInterface.
    Connects to PostgreSQL + PostGIS via DatabaseSubstrate.
    """

    def __init__(self, db_substrate: Optional[DatabaseSubstrate] = None):
        self._db = db_substrate or DatabaseSubstrate.get_instance()

    # --------------------------------------------------------------------------
    # 🛰️ Estações Canônicas e Coberturas Regionais (RIMS)
    # --------------------------------------------------------------------------

    def save_station(self, station: GroundStationEntity) -> None:
        with self._db.session_scope() as session:
            existing = session.execute(
                select(GroundStationModel).where(GroundStationModel.code == station.code)
            ).scalar_one_or_none()

            loc_wkt = PostgisGeometryMapper.pointz_to_wkt(station.location)
            cov_wkt = (
                PostgisGeometryMapper.polygon_to_wkt(station.coverage_polygon)
                if station.coverage_polygon
                else None
            )

            if existing:
                existing.name = station.name
                existing.station_type = station.station_type.value
                existing.elevation_mask_deg = station.elevation_mask_deg
                existing.coverage_radius_km = station.coverage_radius_km
                existing.location = loc_wkt
                existing.coverage_area = cov_wkt
                existing.is_operational = station.is_operational
            else:
                model = GroundStationModel(
                    code=station.code,
                    name=station.name,
                    station_type=station.station_type.value,
                    elevation_mask_deg=station.elevation_mask_deg,
                    coverage_radius_km=station.coverage_radius_km,
                    is_operational=station.is_operational,
                    location=loc_wkt,
                    coverage_area=cov_wkt
                )
                session.add(model)

    def get_station_by_code(self, code: str) -> Optional[GroundStationEntity]:
        with self._db.session_scope() as session:
            model = session.execute(
                select(GroundStationModel).where(GroundStationModel.code == code)
            ).scalar_one_or_none()
            return PostgisModelMapper.model_to_station(model) if model else None

    def list_all_stations(self) -> List[GroundStationEntity]:
        with self._db.session_scope() as session:
            models = session.execute(select(GroundStationModel)).scalars().all()
            return [PostgisModelMapper.model_to_station(m) for m in models]

    def find_covering_stations(self, coords: GeodeticCoordinatesVO) -> List[GroundStationEntity]:
        """Spatial query: find stations whose coverage footprint contains the coordinate (ST_Contains)."""
        point_wkt = f"POINT ({coords.longitude_deg} {coords.latitude_deg})"
        pt_geom = func.ST_SetSRID(func.ST_GeomFromText(point_wkt), 4326)

        with self._db.session_scope() as session:
            stmt = select(GroundStationModel).where(
                GroundStationModel.is_operational.is_(True),
                GroundStationModel.coverage_area.is_not(None),
                func.ST_Contains(GroundStationModel.coverage_area, pt_geom)
            )
            models = session.execute(stmt).scalars().all()
            return [PostgisModelMapper.model_to_station(m) for m in models]

    # --------------------------------------------------------------------------
    # 🚗 Trajetórias de Veículos e Monitoramento Espacial
    # --------------------------------------------------------------------------

    def record_track_points(self, points: List[VehicleTrackPointVO]) -> None:
        if not points:
            return

        with self._db.session_scope() as session:
            models = [PostgisModelMapper.track_point_to_model(p) for p in points]
            session.add_all(models)

    def get_trajectory(
        self,
        vehicle_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[VehicleTrackPointVO]:
        with self._db.session_scope() as session:
            stmt = (
                select(VehicleTrackPointModel)
                .where(
                    VehicleTrackPointModel.vehicle_id == vehicle_id,
                    VehicleTrackPointModel.timestamp >= start_time,
                    VehicleTrackPointModel.timestamp <= end_time
                )
                .order_by(VehicleTrackPointModel.timestamp.asc())
            )
            models = session.execute(stmt).scalars().all()
            return [PostgisModelMapper.model_to_track_point(m) for m in models]

    def find_tracks_within_bounds(self, bbox: BoundingBoxVO) -> List[VehicleTrackPointVO]:
        """Spatial query: find track points within a bounding box (ST_MakeEnvelope)."""
        bbox_geom = func.ST_MakeEnvelope(
            bbox.min_lon, bbox.min_lat,
            bbox.max_lon, bbox.max_lat,
            4326
        )
        with self._db.session_scope() as session:
            stmt = select(VehicleTrackPointModel).where(
                func.ST_Within(VehicleTrackPointModel.location, bbox_geom)
            )
            models = session.execute(stmt).scalars().all()
            return [PostgisModelMapper.model_to_track_point(m) for m in models]

    # --------------------------------------------------------------------------
    # 🛣️ Malhas Viárias Regionais (Rodovias)
    # --------------------------------------------------------------------------

    def save_road_segment(self, segment: RoadSegmentEntity) -> None:
        with self._db.session_scope() as session:
            existing = session.execute(
                select(RoadSegmentModel).where(RoadSegmentModel.segment_id == segment.segment_id)
            ).scalar_one_or_none()

            geom_wkt = PostgisGeometryMapper.linestring_to_wkt(segment.waypoints)

            if existing:
                existing.name = segment.name
                existing.road_code = segment.road_code
                existing.road_type = segment.road_type.value
                existing.length_meters = segment.length_meters
                existing.geom = geom_wkt
            else:
                model = RoadSegmentModel(
                    segment_id=segment.segment_id,
                    name=segment.name,
                    road_code=segment.road_code,
                    road_type=segment.road_type.value,
                    length_meters=segment.length_meters,
                    geom=geom_wkt
                )
                session.add(model)

    def get_road_segment(self, segment_id: str) -> Optional[RoadSegmentEntity]:
        with self._db.session_scope() as session:
            model = session.execute(
                select(RoadSegmentModel).where(RoadSegmentModel.segment_id == segment_id)
            ).scalar_one_or_none()
            return PostgisModelMapper.model_to_road(model) if model else None

    def list_road_segments(self) -> List[RoadSegmentEntity]:
        with self._db.session_scope() as session:
            models = session.execute(select(RoadSegmentModel)).scalars().all()
            return [PostgisModelMapper.model_to_road(m) for m in models]

    def find_nearby_roads(
        self,
        coords: GeodeticCoordinatesVO,
        distance_meters: float
    ) -> List[RoadSegmentEntity]:
        """
        Spatial query: find roads within distance_meters from coordinates.
        Uses ST_DWithin with geography casting for true meter distance on spheroid.
        """
        pt_wkt = f"POINT ({coords.longitude_deg} {coords.latitude_deg})"
        pt_geom = func.ST_SetSRID(func.ST_GeomFromText(pt_wkt), 4326)

        with self._db.session_scope() as session:
            # Cast geometry to geography for ST_DWithin in meters
            stmt = select(RoadSegmentModel).where(
                func.ST_DWithin(
                    func.cast(RoadSegmentModel.geom, func.Geography),
                    func.cast(pt_geom, func.Geography),
                    distance_meters
                )
            )
            models = session.execute(stmt).scalars().all()
            return [PostgisModelMapper.model_to_road(m) for m in models]

    # --------------------------------------------------------------------------
    # 📡 Histórico de Sinais Recebidos da Constelação
    # --------------------------------------------------------------------------

    def log_signal_receptions(self, records: List[ConstellationSignalLogVO]) -> None:
        if not records:
            return

        with self._db.session_scope() as session:
            models = [PostgisModelMapper.signal_to_model(r) for r in records]
            session.add_all(models)

    def query_receptions_by_station(
        self,
        station_code: str,
        limit: int = 100
    ) -> List[ConstellationSignalLogVO]:
        with self._db.session_scope() as session:
            stmt = (
                select(SatelliteSignalLogModel)
                .where(SatelliteSignalLogModel.station_code == station_code)
                .order_by(SatelliteSignalLogModel.timestamp.desc())
                .limit(limit)
            )
            models = session.execute(stmt).scalars().all()
            return [PostgisModelMapper.model_to_signal(m) for m in models]
