"""
Domain Policies for Stations Sub-Core.
Defines dynamic business and integrity rules.
"""
from typing import List

from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.stations.entities import GroundStationEntity
from rps_ground.core.domain.stations.specifications import WithinStationCoverageSpecification


class RimsCoverageRedundancyPolicy:
    """
    SBAS / DO-229D requirement: ensure minimum $N$ redundant stations
    are covering a target location for valid differential/integrity calculation.
    """

    def __init__(self, min_redundancy: int = 2):
        self.min_redundancy = min_redundancy

    def evaluate_redundancy(
        self,
        stations: List[GroundStationEntity],
        target: GeodeticCoordinatesVO
    ) -> bool:
        operational_covering = [
            s for s in stations
            if s.is_operational and WithinStationCoverageSpecification.is_satisfied_by(s, target)
        ]
        return len(operational_covering) >= self.min_redundancy
