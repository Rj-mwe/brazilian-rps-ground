"""
PostGIS Relational & Spatial Database Schema (US124).
Declarative ORM models using SQLAlchemy 2.0 and GeoAlchemy2.
SRID 4326 (WGS84 / SIRGAS2000).
"""
from datetime import datetime, timezone

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class GroundStationModel(Base):
    """Spatial table for regional ground monitoring and operations stations."""
    __tablename__ = "ground_stations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    station_type = Column(String(50), nullable=False)
    elevation_mask_deg = Column(Float, nullable=False, default=5.0)
    coverage_radius_km = Column(Float, nullable=False, default=1200.0)
    is_operational = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # 3D Point (lon, lat, alt) in SRID 4326
    location = Column(Geometry(geometry_type="POINTZ", srid=4326, spatial_index=True), nullable=False)

    # 2D Polygon representing regional footprint / coverage boundary
    coverage_area = Column(Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True), nullable=True)


class RoadSegmentModel(Base):
    """Spatial table for regional highways and road networks."""
    __tablename__ = "road_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    segment_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    road_code = Column(String(20), nullable=False, index=True)
    road_type = Column(String(50), nullable=False)
    length_meters = Column(Float, nullable=False, default=0.0)

    # 2D LineString polyline in SRID 4326
    geom = Column(Geometry(geometry_type="LINESTRING", srid=4326, spatial_index=True), nullable=False)


class VehicleTrackPointModel(Base):
    """High-volume spatial time-series table for vehicle tracking points."""
    __tablename__ = "vehicle_track_points"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    vehicle_id = Column(String(50), nullable=False, index=True)
    session_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)

    # 3D Point (lon, lat, alt) in SRID 4326
    location = Column(Geometry(geometry_type="POINTZ", srid=4326, spatial_index=True), nullable=False)

    speed_mps = Column(Float, nullable=False, default=0.0)
    heading_deg = Column(Float, nullable=False, default=0.0)
    pdop = Column(Float, nullable=False, default=1.0)
    fix_status = Column(String(20), nullable=False, default="3D_FIX")

    __table_args__ = (
        Index("ix_track_vehicle_ts", "vehicle_id", "timestamp"),
    )


class SatelliteSignalLogModel(Base):
    """Spatial time-series table for constellation signals received by ground stations."""
    __tablename__ = "satellite_signal_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    station_code = Column(String(10), ForeignKey("ground_stations.code"), nullable=False, index=True)
    satellite_id = Column(Integer, nullable=False, index=True)
    satellite_type = Column(String(10), nullable=False)
    elevation_deg = Column(Float, nullable=False)
    azimuth_deg = Column(Float, nullable=False)
    pseudorange_m = Column(Float, nullable=False)
    c_n0_dbhz = Column(Float, nullable=False)
    doppler_hz = Column(Float, nullable=False, default=0.0)

    # 3D LineString vector from ground station to satellite
    los_geometry = Column(Geometry(geometry_type="LINESTRINGZ", srid=4326, spatial_index=True), nullable=True)

    __table_args__ = (
        Index("ix_signal_station_sat_ts", "station_code", "satellite_id", "timestamp"),
    )
