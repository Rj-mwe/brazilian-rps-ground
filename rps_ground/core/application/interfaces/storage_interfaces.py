"""
Application Layer Interfaces (Contracts / Outbound Ports).
Defines persistence and spatial query contracts required by Application Services.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from rps_ground.core.domain.geodesy.value_objects import BoundingBoxVO, GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.telemetry.value_objects import ConstellationSignalLogVO
from rps_ground.core.domain.tracking.entities import RoadSegmentEntity
from rps_ground.core.domain.tracking.value_objects import VehicleTrackPointVO


class IGroundStationStorageInterface(ABC):
    """Storage contract for regional ground stations and coverage footprints."""

    @abstractmethod
    def save_station(self, station: GroundStationEntity) -> None:
        """Persist or update a ground station with its spatial location and coverage polygon."""
        pass

    @abstractmethod
    def get_station_by_code(self, code: str) -> Optional[GroundStationEntity]:
        """Retrieve station by its unique alphabetic code."""
        pass

    @abstractmethod
    def list_all_stations(self) -> List[GroundStationEntity]:
        """List all registered stations."""
        pass

    @abstractmethod
    def find_covering_stations(self, coords: GeodeticCoordinatesVO) -> List[GroundStationEntity]:
        """Spatial query: find stations whose coverage footprint contains the coordinate."""
        pass


class ITrajectoryStorageInterface(ABC):
    """Storage contract for vehicle trajectories and spatial tracks."""

    @abstractmethod
    def record_track_points(self, points: List[VehicleTrackPointVO]) -> None:
        """Batch record vehicle track points with PostGIS point geometries."""
        pass

    @abstractmethod
    def get_trajectory(
        self,
        vehicle_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[VehicleTrackPointVO]:
        """Query trajectory of a vehicle within a time interval."""
        pass

    @abstractmethod
    def find_tracks_within_bounds(self, bbox: BoundingBoxVO) -> List[VehicleTrackPointVO]:
        """Spatial query: find track points within bounding box."""
        pass


class IRoadNetworkStorageInterface(ABC):
    """Storage contract for regional road networks and highway segments."""

    @abstractmethod
    def save_road_segment(self, segment: RoadSegmentEntity) -> None:
        """Persist a road segment with its LineString geometry."""
        pass

    @abstractmethod
    def get_road_segment(self, segment_id: str) -> Optional[RoadSegmentEntity]:
        """Retrieve road segment by ID."""
        pass

    @abstractmethod
    def list_road_segments(self) -> List[RoadSegmentEntity]:
        """List all registered road segments."""
        pass

    @abstractmethod
    def find_nearby_roads(
        self,
        coords: GeodeticCoordinatesVO,
        distance_meters: float
    ) -> List[RoadSegmentEntity]:
        """Spatial query: find roads within distance_meters from coordinates (ST_DWithin)."""
        pass


class ISignalLogStorageInterface(ABC):
    """Storage contract for satellite signal reception telemetry."""

    @abstractmethod
    def log_signal_receptions(self, records: List[ConstellationSignalLogVO]) -> None:
        """Batch record incoming satellite signals and LOS geometries."""
        pass

    @abstractmethod
    def query_receptions_by_station(
        self,
        station_code: str,
        limit: int = 100
    ) -> List[ConstellationSignalLogVO]:
        """Retrieve recent reception logs for a given station."""
        pass


class ISpatialStorageInterface(
    IGroundStationStorageInterface,
    ITrajectoryStorageInterface,
    IRoadNetworkStorageInterface,
    ISignalLogStorageInterface,
    ABC
):
    """Unified composite interface for spatial storage operations in ground segment."""
    pass
