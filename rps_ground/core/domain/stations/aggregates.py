"""
Aggregates for Stations Sub-Core.
Consistency root managing a network of regional ground stations.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.stations.specifications import WithinStationCoverageSpecification


@dataclass
class GroundStationNetworkAggregate:
    """
    Consistency boundary root for the regional station network.
    Maintains invariants on station registration, operational status, and redundancy.
    """
    network_id: str
    stations: Dict[str, GroundStationEntity] = field(default_factory=dict)

    def register_station(self, station: GroundStationEntity) -> None:
        if station.code in self.stations:
            raise ValueError(f"Station '{station.code}' is already registered in network.")
        self.stations[station.code] = station

    def get_station(self, code: str) -> Optional[GroundStationEntity]:
        return self.stations.get(code)

    @property
    def operational_count(self) -> int:
        return sum(1 for s in self.stations.values() if s.is_operational)

    @property
    def total_count(self) -> int:
        return len(self.stations)

    def find_covering_stations(self, target: GeodeticCoordinatesVO) -> List[GroundStationEntity]:
        return [
            s for s in self.stations.values()
            if s.is_operational and WithinStationCoverageSpecification.is_satisfied_by(s, target)
        ]
