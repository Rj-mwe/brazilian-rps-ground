"""
Mappers for Application Layer.
Bidirectional pure translators between Application DTOs and Core Domain Entities/VOs.
"""
from rps_ground.core.application.dtos.ground_dtos import (
    GroundStationDTO,
    RoadSegmentDTO,
    SignalReceptionDTO,
    VehicleTrackDTO,
)
from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.stations.factories import GroundStationFactory
from rps_ground.core.domain.stations.value_objects import StationType
from rps_ground.core.domain.telemetry.value_objects import ConstellationSignalLogVO
from rps_ground.core.domain.tracking.entities import RoadSegmentEntity
from rps_ground.core.domain.tracking.value_objects import RoadType, VehicleTrackPointVO


class GroundSpatialMapper:
    """Translates between Application DTOs and Domain Models."""

    @classmethod
    def station_dto_to_entity(cls, dto: GroundStationDTO) -> GroundStationEntity:
        loc = GeodeticCoordinatesVO(
            latitude_deg=dto.latitude,
            longitude_deg=dto.longitude,
            altitude_m=dto.altitude
        )
        footprint = GroundStationFactory.create_circular_footprint(
            loc,
            radius_km=dto.coverage_radius_km
        )
        return GroundStationEntity(
            code=dto.code,
            name=dto.name,
            station_type=StationType(dto.station_type),
            location=loc,
            elevation_mask_deg=dto.elevation_mask_deg,
            coverage_radius_km=dto.coverage_radius_km,
            coverage_polygon=footprint,
            is_operational=dto.is_operational
        )

    @classmethod
    def station_entity_to_dto(cls, entity: GroundStationEntity) -> GroundStationDTO:
        return GroundStationDTO(
            code=entity.code,
            name=entity.name,
            station_type=entity.station_type.value,
            latitude=entity.location.latitude_deg,
            longitude=entity.location.longitude_deg,
            altitude=entity.location.altitude_m,
            elevation_mask_deg=entity.elevation_mask_deg,
            coverage_radius_km=entity.coverage_radius_km,
            is_operational=entity.is_operational
        )

    @classmethod
    def track_dto_to_vo(cls, dto: VehicleTrackDTO) -> VehicleTrackPointVO:
        return VehicleTrackPointVO(
            vehicle_id=dto.vehicle_id,
            timestamp=dto.timestamp,
            position=GeodeticCoordinatesVO(
                latitude_deg=dto.latitude,
                longitude_deg=dto.longitude,
                altitude_m=dto.altitude
            ),
            speed_mps=dto.speed_mps,
            heading_deg=dto.heading_deg,
            pdop=dto.pdop,
            fix_status=dto.fix_status
        )

    @classmethod
    def track_vo_to_dto(cls, vo: VehicleTrackPointVO) -> VehicleTrackDTO:
        return VehicleTrackDTO(
            vehicle_id=vo.vehicle_id,
            timestamp=vo.timestamp,
            latitude=vo.position.latitude_deg,
            longitude=vo.position.longitude_deg,
            altitude=vo.position.altitude_m,
            speed_mps=vo.speed_mps,
            heading_deg=vo.heading_deg,
            pdop=vo.pdop,
            fix_status=vo.fix_status
        )

    @classmethod
    def road_dto_to_entity(cls, dto: RoadSegmentDTO) -> RoadSegmentEntity:
        waypoints = tuple(
            GeodeticCoordinatesVO(latitude_deg=wp[0], longitude_deg=wp[1], altitude_m=wp[2])
            for wp in dto.waypoints
        )
        return RoadSegmentEntity(
            segment_id=dto.segment_id,
            name=dto.name,
            road_code=dto.road_code,
            road_type=RoadType(dto.road_type),
            waypoints=waypoints,
            length_meters=dto.length_meters
        )

    @classmethod
    def signal_dto_to_vo(cls, dto: SignalReceptionDTO) -> ConstellationSignalLogVO:
        return ConstellationSignalLogVO(
            timestamp=dto.timestamp,
            station_code=dto.station_code,
            satellite_id=dto.satellite_id,
            satellite_type=dto.satellite_type,
            elevation_deg=dto.elevation_deg,
            azimuth_deg=dto.azimuth_deg,
            pseudorange_m=dto.pseudorange_m,
            c_n0_dbhz=dto.c_n0_dbhz,
            doppler_hz=dto.doppler_hz,
            los_valid=dto.los_valid
        )
