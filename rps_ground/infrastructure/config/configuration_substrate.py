"""
Configuration Substrate (Hexágono Dourado Infrastructure Substrate).
Centralized, immutable, and schema-validated configuration platform service for ground segment.
Resolves configuration cascade: Code Defaults -> YAML File -> Environment Variables (RPS_GROUND_*) -> Runtime Overrides.
"""
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


@dataclass(frozen=True)
class DatabaseConfigVO:
    """Immutable Value Object for database connection and storage parameters."""
    host: str = "127.0.0.1"
    port: int = 5432
    database: str = "rps_ground"
    user: str = "rjgamito"
    password: str = ""
    pool_size: int = 10
    max_overflow: int = 20
    timeout_sec: int = 30
    data_dir: str = "~/.local/share/rps_ground/postgres_data"

    @property
    def connection_url(self) -> str:
        """SQLAlchemy connection URL for PostgreSQL."""
        auth = self.user
        if self.password:
            auth = f"{auth}:{self.password}"
        return f"postgresql://{auth}@{self.host}:{self.port}/{self.database}"

    @property
    def resolved_data_dir(self) -> Path:
        return Path(os.path.expanduser(self.data_dir)).resolve()


@dataclass(frozen=True)
class StationConfigVO:
    """Immutable Value Object for ground station configuration."""
    code: str
    name: str
    station_type: str = "RIMS"
    latitude_deg: float = 0.0
    longitude_deg: float = 0.0
    altitude_m: float = 0.0
    elevation_mask_deg: float = 5.0
    coverage_radius_km: float = 1200.0


@dataclass(frozen=True)
class RoadCorridorConfigVO:
    """Immutable Value Object for road corridors."""
    code: str
    name: str
    road_type: str = "HIGHWAY_FEDERAL"


@dataclass(frozen=True)
class TrackingConfigVO:
    """Immutable Value Object for trajectory tracking parameters."""
    sampling_interval_sec: float = 1.0
    speed_limit_mps: float = 60.0
    reference_corridors: Tuple[RoadCorridorConfigVO, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GroundConfigVO:
    """Root configuration Value Object for the ground segment."""
    database: DatabaseConfigVO
    stations: Tuple[StationConfigVO, ...] = field(default_factory=tuple)
    tracking: TrackingConfigVO = field(default_factory=TrackingConfigVO)
    raw_dict: Dict[str, Any] = field(default_factory=dict)
    source_path: Optional[Path] = None


class ConfigurationSubstrate:
    """
    Platform substrate managing SSOT configuration.
    Provides cascade resolution and thread-safe access.
    """
    _instance: Optional["ConfigurationSubstrate"] = None
    _singleton_lock = threading.Lock()

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        auto_load: bool = True
    ):
        self._lock = threading.RLock()
        self._config_path = Path(config_path).resolve() if config_path else None
        self._overrides = overrides or {}
        self._current_config: Optional[GroundConfigVO] = None

        if auto_load:
            self.load()

    @classmethod
    def get_instance(cls, config_path: Optional[Union[str, Path]] = None) -> "ConfigurationSubstrate":
        """Singleton accessor for global configuration substrate."""
        with cls._singleton_lock:
            if cls._instance is None:
                cls._instance = cls(config_path=config_path)
            elif config_path and cls._instance._config_path != Path(config_path).resolve():
                cls._instance = cls(config_path=config_path)
            return cls._instance

    @staticmethod
    def find_config_file(filename: str = "ground_parameters.yaml") -> Path:
        """Locate central configuration file in project hierarchy."""
        current_dir = Path(__file__).resolve().parent
        for parent in [current_dir] + list(current_dir.parents):
            candidate = parent / "config" / filename
            if candidate.exists():
                return candidate.resolve()
        raise FileNotFoundError(f"Configuration file '{filename}' not found.")

    def _resolve_cascade(self, base_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variables (RPS_GROUND_*) and runtime overrides."""
        resolved = dict(base_data)

        # Database overrides
        db_sec = dict(resolved.get("database", {}))
        if "RPS_GROUND_DB_HOST" in os.environ:
            db_sec["host"] = os.environ["RPS_GROUND_DB_HOST"]
        if "RPS_GROUND_DB_PORT" in os.environ:
            try:
                db_sec["port"] = int(os.environ["RPS_GROUND_DB_PORT"])
            except ValueError:
                pass
        if "RPS_GROUND_DB_NAME" in os.environ:
            db_sec["database"] = os.environ["RPS_GROUND_DB_NAME"]
        if "RPS_GROUND_DB_USER" in os.environ:
            db_sec["user"] = os.environ["RPS_GROUND_DB_USER"]
        if "RPS_GROUND_DB_PASSWORD" in os.environ:
            db_sec["password"] = os.environ["RPS_GROUND_DB_PASSWORD"]
        if "RPS_GROUND_DB_DATA_DIR" in os.environ:
            db_sec["data_dir"] = os.environ["RPS_GROUND_DB_DATA_DIR"]

        resolved["database"] = db_sec

        # Apply programmatic overrides
        if self._overrides:
            resolved.update(self._overrides)

        return resolved

    def load(self) -> GroundConfigVO:
        """Load, validate, and freeze configuration."""
        with self._lock:
            if self._config_path is None:
                self._config_path = self.find_config_file()

            if not self._config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self._config_path}")

            with open(self._config_path, "r", encoding="utf-8") as f:
                raw_yaml = yaml.safe_load(f) or {}

            resolved = self._resolve_cascade(raw_yaml)

            db_data = resolved.get("database", {})
            db_vo = DatabaseConfigVO(
                host=str(db_data.get("host", "127.0.0.1")),
                port=int(db_data.get("port", 5432)),
                database=str(db_data.get("database", "rps_ground")),
                user=str(db_data.get("user", "rjgamito")),
                password=str(db_data.get("password", "")),
                pool_size=int(db_data.get("pool_size", 10)),
                max_overflow=int(db_data.get("max_overflow", 20)),
                timeout_sec=int(db_data.get("timeout_sec", 30)),
                data_dir=str(db_data.get("data_dir", "~/.local/share/rps_ground/postgres_data"))
            )

            stations_list: List[StationConfigVO] = []
            for s in resolved.get("stations", []):
                stations_list.append(
                    StationConfigVO(
                        code=str(s.get("code", "")),
                        name=str(s.get("name", "")),
                        station_type=str(s.get("station_type", "RIMS")),
                        latitude_deg=float(s.get("latitude_deg", 0.0)),
                        longitude_deg=float(s.get("longitude_deg", 0.0)),
                        altitude_m=float(s.get("altitude_m", 0.0)),
                        elevation_mask_deg=float(s.get("elevation_mask_deg", 5.0)),
                        coverage_radius_km=float(s.get("coverage_radius_km", 1200.0))
                    )
                )

            track_data = resolved.get("tracking", {})
            corridors_list: List[RoadCorridorConfigVO] = []
            for c in track_data.get("reference_corridors", []):
                corridors_list.append(
                    RoadCorridorConfigVO(
                        code=str(c.get("code", "")),
                        name=str(c.get("name", "")),
                        road_type=str(c.get("road_type", "HIGHWAY_FEDERAL"))
                    )
                )

            track_vo = TrackingConfigVO(
                sampling_interval_sec=float(track_data.get("sampling_interval_sec", 1.0)),
                speed_limit_mps=float(track_data.get("speed_limit_mps", 60.0)),
                reference_corridors=tuple(corridors_list)
            )

            self._current_config = GroundConfigVO(
                database=db_vo,
                stations=tuple(stations_list),
                tracking=track_vo,
                raw_dict=resolved,
                source_path=self._config_path
            )
            return self._current_config

    def reload(self) -> GroundConfigVO:
        return self.load()

    @property
    def config(self) -> GroundConfigVO:
        with self._lock:
            if self._current_config is None:
                self.load()
            return self._current_config  # type: ignore[return-value]

    @property
    def database(self) -> DatabaseConfigVO:
        return self.config.database

    @property
    def stations(self) -> Tuple[StationConfigVO, ...]:
        return self.config.stations

    @property
    def tracking(self) -> TrackingConfigVO:
        return self.config.tracking

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.raw_dict.get(key, default)
