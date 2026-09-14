"""
Internal Application Services for PostGIS Sink Fractal Adapter.
"""
from typing import Optional

from rps_ground.adapters.postgis_sink.dtos import PostgisSinkHealthDTO
from rps_ground.adapters.postgis_sink.interfaces import IPostgisSinkCoordinator
from rps_ground.adapters.postgis_sink.schema import Base
from rps_ground.infrastructure.persistence.database_substrate import DatabaseSubstrate


class PostgisSinkCoordinatorService(IPostgisSinkCoordinator):
    """Coordinates PostGIS sink operations, schema migration, and health inspections."""

    def __init__(self, db_substrate: Optional[DatabaseSubstrate] = None):
        self._db = db_substrate or DatabaseSubstrate.get_instance()

    def verify_readiness(self) -> bool:
        return self._db.health_check()

    def get_postgis_version(self) -> Optional[str]:
        return self._db.postgis_check()

    def setup_tables(self) -> bool:
        """Initialize relational and spatial schema in PostGIS."""
        return self._db.initialize_schema(Base.metadata)

    def get_health_status(self) -> PostgisSinkHealthDTO:
        is_conn = self._db.health_check()
        pg_ver = self._db.postgis_check() if is_conn else None
        return PostgisSinkHealthDTO(
            is_connected=is_conn,
            postgis_version=pg_ver,
            connection_host=self._db.config.host,
            database_name=self._db.config.database
        )
