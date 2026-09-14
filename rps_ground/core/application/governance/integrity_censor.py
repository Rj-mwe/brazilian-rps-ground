"""
Governance Sub-Core: Data Integrity Censor.
Quarantines malformed telemetry, corrupted pseudorange records, or out-of-order packets.
"""
from typing import Any, List, Tuple

from rps_ground.core.domain.telemetry.specifications import SignalIntegrityValidSpecification
from rps_ground.core.domain.telemetry.value_objects import ConstellationSignalLogVO


class GroundDataIntegrityCensor:
    """
    Sub-Core censor that intercepts external packets, verifies contracts,
    and isolates corrupted or non-compliant records into quarantine.
    """

    def __init__(self):
        self._quarantine: List[Tuple[Any, str]] = []

    def censor_signal_batch(
        self,
        signals: List[ConstellationSignalLogVO]
    ) -> Tuple[List[ConstellationSignalLogVO], List[Tuple[ConstellationSignalLogVO, str]]]:
        admitted: List[ConstellationSignalLogVO] = []
        rejected: List[Tuple[ConstellationSignalLogVO, str]] = []

        for sig in signals:
            if not SignalIntegrityValidSpecification.is_satisfied_by(sig):
                reason = "Failed SignalIntegrityValidSpecification (out-of-bounds range or low C/N0)"
                rejected.append((sig, reason))
                self._quarantine.append((sig, reason))
            else:
                admitted.append(sig)

        return admitted, rejected

    @property
    def quarantine_records(self) -> List[Tuple[Any, str]]:
        return list(self._quarantine)

    def clear_quarantine(self) -> None:
        self._quarantine.clear()
