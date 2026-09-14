"""
PostGIS Sink Edge Adapter (Level 3 Fractal Adapter).
Handles spatial persistence of stations, footprints, trajectories, road networks, and telemetry.
"""
from rps_ground.adapters.postgis_sink.mappers import (
    PostgisGeometryMapper,
    PostgisModelMapper,
)
from rps_ground.adapters.postgis_sink.postgis_repository import PostgisSpatialRepository
from rps_ground.adapters.postgis_sink.schema import (
    Base,
    GroundStationModel,
    RoadSegmentModel,
    SatelliteSignalLogModel,
    VehicleTrackPointModel,
)
from rps_ground.adapters.postgis_sink.services import PostgisSinkCoordinatorService

__all__ = [
    "Base",
    "GroundStationModel",
    "RoadSegmentModel",
    "VehicleTrackPointModel",
    "SatelliteSignalLogModel",
    "PostgisGeometryMapper",
    "PostgisModelMapper",
    "PostgisSpatialRepository",
    "PostgisSinkCoordinatorService",
]
