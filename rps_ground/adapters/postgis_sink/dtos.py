"""
Internal DTOs for PostGIS Sink Fractal Adapter.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PostgisSinkHealthDTO:
    is_connected: bool
    postgis_version: Optional[str]
    connection_host: str
    database_name: str


@dataclass(frozen=True)
class PostgisBulkStatsDTO:
    inserted_count: int
    elapsed_sec: float
    records_per_sec: float
