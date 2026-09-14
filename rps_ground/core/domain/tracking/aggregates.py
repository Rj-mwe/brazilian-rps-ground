"""
Aggregates for Tracking Sub-Core.
Consistency root managing a vehicle tracking mission session.
"""
from dataclasses import dataclass, field
from typing import List, Optional

from rps_ground.core.domain.tracking.value_objects import VehicleTrackPointVO


@dataclass
class VehicleTrackingSessionAggregate:
    """
    Consistency boundary root for a continuous tracking session of a vehicle.
    Guarantees chronological monotonic order of track points.
    """
    session_id: str
    vehicle_id: str
    points: List[VehicleTrackPointVO] = field(default_factory=list)
    is_active: bool = True

    def record_point(self, point: VehicleTrackPointVO) -> None:
        if not self.is_active:
            raise ValueError(f"Session '{self.session_id}' is closed.")
        if point.vehicle_id != self.vehicle_id:
            raise ValueError(
                f"Mismatched vehicle_id in track point: expected '{self.vehicle_id}', got '{point.vehicle_id}'"
            )

        if self.points:
            last_ts = self.points[-1].timestamp
            if point.timestamp < last_ts:
                raise ValueError(
                    f"Timestamp violation: new point {point.timestamp} is earlier than previous {last_ts}"
                )

        self.points.append(point)

    def close_session(self) -> None:
        self.is_active = False

    @property
    def point_count(self) -> int:
        return len(self.points)

    @property
    def latest_point(self) -> Optional[VehicleTrackPointVO]:
        return self.points[-1] if self.points else None
