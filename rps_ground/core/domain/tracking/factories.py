"""
Factories for Tracking Sub-Core.
Assembles canonical road corridors and reference networks.
"""
from typing import List

from rps_ground.core.domain.geodesy.services import GeodeticDistanceCalculator
from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.tracking.entities import RoadSegmentEntity
from rps_ground.core.domain.tracking.value_objects import RoadType


class RoadNetworkFactory:
    """Factory for creating canonical road segments and corridors in the Vale do Paraíba."""

    @classmethod
    def create_canonical_corridors(cls) -> List[RoadSegmentEntity]:
        """
        Creates reference corridors:
        1. BR-116 Presidente Dutra: connecting São José dos Campos (ITA/DCTA) to Cachoeira Paulista (INPE).
        2. SP-099 Rodovia dos Tamoios: connecting São José dos Campos to Caraguatatuba (Litoral Norte).
        """
        # BR-116 Dutra (SJC -> Caçapava -> Taubaté -> Pindamonhangaba -> Guaratinguetá -> Lorena -> Cachoeira Paulista)
        dutra_coords = (
            GeodeticCoordinatesVO(-23.210, -45.880, 660.0),  # SJC (ITA)
            GeodeticCoordinatesVO(-23.100, -45.710, 560.0),  # Caçapava
            GeodeticCoordinatesVO(-23.030, -45.560, 580.0),  # Taubaté
            GeodeticCoordinatesVO(-22.920, -45.460, 540.0),  # Pindamonhangaba
            GeodeticCoordinatesVO(-22.810, -45.190, 530.0),  # Guaratinguetá
            GeodeticCoordinatesVO(-22.730, -45.120, 525.0),  # Lorena
            GeodeticCoordinatesVO(-22.686, -45.007, 565.0),  # Cachoeira Paulista (INPE)
        )

        dutra_length = sum(
            GeodeticDistanceCalculator.haversine_distance_m(dutra_coords[i], dutra_coords[i + 1])
            for i in range(len(dutra_coords) - 1)
        )

        # SP-099 Tamoios (SJC -> Jambeiro -> Paraibuna -> Caraguatatuba)
        tamoios_coords = (
            GeodeticCoordinatesVO(-23.210, -45.880, 660.0),  # SJC
            GeodeticCoordinatesVO(-23.250, -45.820, 620.0),  # Jambeiro
            GeodeticCoordinatesVO(-23.380, -45.660, 600.0),  # Paraibuna
            GeodeticCoordinatesVO(-23.620, -45.410, 10.0),   # Caraguatatuba
        )

        tamoios_length = sum(
            GeodeticDistanceCalculator.haversine_distance_m(tamoios_coords[i], tamoios_coords[i + 1])
            for i in range(len(tamoios_coords) - 1)
        )

        return [
            RoadSegmentEntity(
                segment_id="BR116-SJC-CPQ",
                name="Rodovia Presidente Dutra (SJC -> Cachoeira Paulista)",
                road_code="BR-116",
                road_type=RoadType.HIGHWAY_FEDERAL,
                waypoints=dutra_coords,
                length_meters=dutra_length
            ),
            RoadSegmentEntity(
                segment_id="SP099-SJC-CARAGUA",
                name="Rodovia dos Tamoios (SJC -> Caraguatatuba)",
                road_code="SP-099",
                road_type=RoadType.HIGHWAY_STATE,
                waypoints=tamoios_coords,
                length_meters=tamoios_length
            )
        ]
