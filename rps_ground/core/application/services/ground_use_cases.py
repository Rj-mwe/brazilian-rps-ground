"""
Application Services (Use Cases).
Orchestrates domain entities, specifications, and storage interfaces to fulfill mission use cases.
"""
from typing import List, Optional, Tuple

from rps_ground.core.application.dtos.ground_dtos import (
    GroundStationDTO,
    SignalReceptionDTO,
    VehicleTrackDTO,
)
from rps_ground.core.application.interfaces.storage_interfaces import (
    IGroundStationStorageInterface,
    IRoadNetworkStorageInterface,
    ISignalLogStorageInterface,
    ITrajectoryStorageInterface,
)
from rps_ground.core.application.mappers.spatial_mapper import GroundSpatialMapper
from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.stations.factories import GroundStationFactory
from rps_ground.core.domain.telemetry.specifications import SignalIntegrityValidSpecification
from rps_ground.core.domain.tracking.aggregates import VehicleTrackingSessionAggregate
from rps_ground.core.domain.tracking.entities import RoadSegmentEntity
from rps_ground.core.domain.tracking.services import RoadMatchingService


class IngestStationCoverageUseCase:
    """Use Case: Ingest and maintain regional ground station network and spatial footprints."""

    def __init__(self, storage: IGroundStationStorageInterface):
        self._storage = storage

    def ingest_station(self, dto: GroundStationDTO) -> GroundStationEntity:
        entity = GroundSpatialMapper.station_dto_to_entity(dto)
        self._storage.save_station(entity)
        return entity

    def seed_canonical_stations(self) -> List[GroundStationEntity]:
        """Seed the 5 canonical Brazilian stations (SJC, ALC, NAT, BSB, CPQ)."""
        stations = GroundStationFactory.create_canonical_stations()
        for s in stations:
            self._storage.save_station(s)
        return stations

    def get_covering_stations(self, lat: float, lon: float, alt: float = 0.0) -> List[GroundStationEntity]:
        target = GeodeticCoordinatesVO(latitude_deg=lat, longitude_deg=lon, altitude_m=alt)
        return self._storage.find_covering_stations(target)


class RecordVehicleTrajectoryUseCase:
    """Use Case: Ingest and persist terrestrial vehicle trajectories and match against road network."""

    def __init__(
        self,
        trajectory_storage: ITrajectoryStorageInterface,
        road_storage: Optional[IRoadNetworkStorageInterface] = None
    ):
        self._trajectory_storage = trajectory_storage
        self._road_storage = road_storage

    def record_track_batch(
        self,
        session_id: str,
        dtos: List[VehicleTrackDTO]
    ) -> VehicleTrackingSessionAggregate:
        if not dtos:
            raise ValueError("No track points provided.")

        vehicle_id = dtos[0].vehicle_id
        session = VehicleTrackingSessionAggregate(session_id=session_id, vehicle_id=vehicle_id)

        points = [GroundSpatialMapper.track_dto_to_vo(d) for d in dtos]
        for p in points:
            session.record_point(p)

        self._trajectory_storage.record_track_points(points)
        return session

    def match_latest_point_to_road(
        self,
        point_dto: VehicleTrackDTO,
        search_radius_m: float = 1000.0
    ) -> Tuple[Optional[RoadSegmentEntity], float]:
        if not self._road_storage:
            return None, float("inf")

        coord = GeodeticCoordinatesVO(
            latitude_deg=point_dto.latitude,
            longitude_deg=point_dto.longitude,
            altitude_m=point_dto.altitude
        )
        nearby_roads = self._road_storage.find_nearby_roads(coord, distance_meters=search_radius_m)
        return RoadMatchingService.find_nearest_road(coord, nearby_roads)


class LogConstellationSignalUseCase:
    """Use Case: Ingest incoming pseudorange and SNR telemetry received from satellites."""

    def __init__(self, storage: ISignalLogStorageInterface):
        self._storage = storage

    def log_signals(
        self,
        dtos: List[SignalReceptionDTO],
        enforce_integrity: bool = True
    ) -> int:
        vos = [GroundSpatialMapper.signal_dto_to_vo(d) for d in dtos]
        if enforce_integrity:
            valid_vos = [v for v in vos if SignalIntegrityValidSpecification.is_satisfied_by(v)]
        else:
            valid_vos = vos

        if valid_vos:
            self._storage.log_signal_receptions(valid_vos)
        return len(valid_vos)
