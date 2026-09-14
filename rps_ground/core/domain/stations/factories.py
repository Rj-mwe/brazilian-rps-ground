"""
Factories for Stations Sub-Core.
Assembles canonical regional stations and builds footprint geometries.
"""
import math
from typing import List

from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.stations.value_objects import CoveragePolygonVO, StationType


class GroundStationFactory:
    """Factory for creating canonical Brazilian regional stations and footprint rings."""

    EARTH_RADIUS_KM: float = 6371.0

    @classmethod
    def create_circular_footprint(
        cls,
        center: GeodeticCoordinatesVO,
        radius_km: float,
        num_vertices: int = 24
    ) -> CoveragePolygonVO:
        """Approximate circular geographic footprint ring as a closed polygon."""
        vertices: List[GeodeticCoordinatesVO] = []
        center_lat_rad = math.radians(center.latitude_deg)
        center_lon_rad = math.radians(center.longitude_deg)
        angular_dist = radius_km / cls.EARTH_RADIUS_KM

        for i in range(num_vertices):
            bearing_rad = (2.0 * math.pi * i) / num_vertices
            lat_rad = math.asin(
                math.sin(center_lat_rad) * math.cos(angular_dist)
                + math.cos(center_lat_rad) * math.sin(angular_dist) * math.cos(bearing_rad)
            )
            lon_rad = center_lon_rad + math.atan2(
                math.sin(bearing_rad) * math.sin(angular_dist) * math.cos(center_lat_rad),
                math.cos(angular_dist) - math.sin(center_lat_rad) * math.sin(lat_rad)
            )
            vertices.append(
                GeodeticCoordinatesVO(
                    latitude_deg=math.degrees(lat_rad),
                    longitude_deg=math.degrees(lon_rad),
                    altitude_m=center.altitude_m
                )
            )

        # Close the ring
        vertices.append(vertices[0])
        return CoveragePolygonVO(vertices=tuple(vertices))

    @classmethod
    def create_canonical_stations(cls) -> List[GroundStationEntity]:
        """Construct the 5 canonical Brazilian monitoring and operations stations."""
        definitions = [
            (
                "SJC",
                "Estação de Monitoramento e Engenharia SJC (ITA/DCTA)",
                StationType.AEROSPACE_RESEARCH,
                -23.210, -45.880, 660.0, 5.0, 1200.0
            ),
            (
                "ALC",
                "Estação RIMS Equatorial Alcântara (CLA)",
                StationType.RIMS,
                -2.316, -44.368, 35.0, 5.0, 1500.0
            ),
            (
                "NAT",
                "Estação RIMS Leste Natal (CLBI)",
                StationType.RIMS,
                -5.795, -35.209, 42.0, 5.0, 1500.0
            ),
            (
                "BSB",
                "Centro de Controle de Missão Master Brasília (CCM)",
                StationType.MASTER_CONTROL,
                -15.794, -47.882, 1172.0, 5.0, 1800.0
            ),
            (
                "CPQ",
                "Estação RIMS Sudeste Cachoeira Paulista (INPE)",
                StationType.RIMS,
                -22.686, -45.007, 565.0, 5.0, 1200.0
            ),
        ]

        stations: List[GroundStationEntity] = []
        for code, name, stype, lat, lon, alt, mask, radius in definitions:
            location = GeodeticCoordinatesVO(latitude_deg=lat, longitude_deg=lon, altitude_m=alt)
            footprint = cls.create_circular_footprint(location, radius_km=radius)
            stations.append(
                GroundStationEntity(
                    code=code,
                    name=name,
                    station_type=stype,
                    location=location,
                    elevation_mask_deg=mask,
                    coverage_radius_km=radius,
                    coverage_polygon=footprint,
                    is_operational=True
                )
            )

        return stations
