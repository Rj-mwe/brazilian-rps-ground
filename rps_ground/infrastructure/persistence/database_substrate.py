"""
Database Substrate (Hexágono Dourado Infrastructure Substrate).
Manages PostgreSQL + PostGIS connections, connection pooling, transactions,
and lifecycle operations for the native database backend.
"""
import logging
import shutil
import threading
from contextlib import contextmanager
from typing import Any, Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from rps_ground.infrastructure.config.configuration_substrate import (
    ConfigurationSubstrate,
    DatabaseConfigVO,
)

logger = logging.getLogger(__name__)


class DatabaseSubstrate:
    """
    Platform substrate managing spatial persistence connections and schema.
    Thread-safe engine and session provider.
    """
    _instance: Optional["DatabaseSubstrate"] = None
    _lock = threading.Lock()

    def __init__(self, config: Optional[DatabaseConfigVO] = None):
        self._config = config or ConfigurationSubstrate.get_instance().database
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._engine_lock = threading.RLock()

    @classmethod
    def get_instance(cls, config: Optional[DatabaseConfigVO] = None) -> "DatabaseSubstrate":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(config=config)
            return cls._instance

    @property
    def config(self) -> DatabaseConfigVO:
        return self._config

    @property
    def engine(self) -> Engine:
        """Lazy-initialize and return the SQLAlchemy engine."""
        with self._engine_lock:
            if self._engine is None:
                self._engine = create_engine(
                    self._config.connection_url,
                    poolclass=QueuePool,
                    pool_size=self._config.pool_size,
                    max_overflow=self._config.max_overflow,
                    pool_timeout=self._config.timeout_sec,
                    pool_pre_ping=True
                )
                self._session_factory = sessionmaker(
                    bind=self._engine,
                    autocommit=False,
                    autoflush=False,
                    expire_on_commit=False
                )
            return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        _ = self.engine
        return self._session_factory  # type: ignore[return-value]

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations."""
        session: Session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def health_check(self) -> bool:
        """
        Verify database reachability and liveness with a short timeout.
        Returns False gracefully if server is inactive, unconfigured, or unreachable.
        """
        try:
            # Create a short-lived test engine to avoid long pool blocks if inactive
            test_engine = create_engine(
                self._config.connection_url,
                connect_args={"connect_timeout": 2}
            )
            with test_engine.connect() as conn:
                res = conn.execute(text("SELECT 1"))
                return res.scalar() == 1
        except Exception as e:
            logger.debug("DatabaseSubstrate health_check failed (expected if inactive): %s", e)
            return False

    def postgis_check(self) -> Optional[str]:
        """Check PostGIS extension version if database is reachable."""
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT PostGIS_Version();"))
                val = res.scalar()
                return str(val) if val else None
        except Exception:
            return None

    def initialize_schema(self, base_metadata: Any, create_extension: bool = True) -> bool:
        """
        Create tables and spatial indexes.
        Requires database server to be active.
        """
        if not self.health_check():
            logger.warning("Cannot initialize schema: PostgreSQL server is not reachable.")
            return False

        with self.engine.begin() as conn:
            if create_extension:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis_topology;"))
            base_metadata.create_all(conn)

        return True

    def is_cluster_initialized(self) -> bool:
        """Check if native PG cluster directory contains PG_VERSION."""
        data_dir = self._config.resolved_data_dir
        version_file = data_dir / "PG_VERSION"
        return version_file.exists()

    def is_server_binary_available(self) -> bool:
        """Check if native postgres/initdb/pg_ctl binaries are installed on host."""
        return (
            shutil.which("postgres") is not None
            and shutil.which("initdb") is not None
            and shutil.which("pg_ctl") is not None
        )
