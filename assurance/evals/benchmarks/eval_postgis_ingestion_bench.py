"""
Benchmark & Performance Evaluation: Big Data Spatial Ingestion (US124).
Measures throughput (records/sec) and serialization latency for spatial tracking and signals.
"""
import time
from datetime import datetime, timezone
from typing import List

from rps_ground.adapters.postgis_sink.mappers import PostgisModelMapper
from rps_ground.adapters.postgis_sink.postgis_repository import PostgisSpatialRepository
from rps_ground.core.domain.geodesy.value_objects import GeodeticCoordinatesVO
from rps_ground.core.domain.tracking.value_objects import VehicleTrackPointVO
from rps_ground.infrastructure.persistence.database_substrate import DatabaseSubstrate


def generate_synthetic_track_points(count: int = 1000) -> List[VehicleTrackPointVO]:
    base_time = datetime(2026, 9, 14, 12, 0, 0, tzinfo=timezone.utc)
    points = []
    for i in range(count):
        pt = VehicleTrackPointVO(
            vehicle_id=f"VEH-{i % 10:02d}",
            timestamp=datetime.fromtimestamp(base_time.timestamp() + i, tz=timezone.utc),
            position=GeodeticCoordinatesVO(
                latitude_deg=-23.210 + (i * 0.0001),
                longitude_deg=-45.880 + (i * 0.0001),
                altitude_m=660.0
            ),
            speed_mps=20.0 + (i % 5),
            heading_deg=(i * 10) % 360,
            pdop=1.2,
            fix_status="3D_FIX"
        )
        points.append(pt)
    return points


def eval_in_memory_serialization_throughput(count: int = 5000):
    points = generate_synthetic_track_points(count)

    t0 = time.perf_counter()
    _ = [PostgisModelMapper.track_point_to_model(p) for p in points]
    t1 = time.perf_counter()

    elapsed = t1 - t0
    rate = count / elapsed if elapsed > 0 else 0
    print(f"📊 [EVAL] In-Memory WKT Serialization ({count} records):")
    print(f"   Elapsed: {elapsed * 1000.0:.2f} ms")
    print(f"   Throughput: {rate:,.0f} records/second")
    assert rate > 1000.0, "Serialization throughput must exceed 1,000 records/sec"


def eval_database_ingestion_throughput(count: int = 1000):
    db_sub = DatabaseSubstrate.get_instance()
    if not db_sub.health_check():
        print("⏭️ [EVAL] Skipping live database batch insertion: DB server is inactive.")
        return

    repo = PostgisSpatialRepository(db_substrate=db_sub)
    points = generate_synthetic_track_points(count)

    t0 = time.perf_counter()
    repo.record_track_points(points)
    t1 = time.perf_counter()

    elapsed = t1 - t0
    rate = count / elapsed if elapsed > 0 else 0
    print(f"📊 [EVAL] Live PostGIS Batch Insertion ({count} records):")
    print(f"   Elapsed: {elapsed * 1000.0:.2f} ms")
    print(f"   Throughput: {rate:,.0f} records/second")


if __name__ == "__main__":
    print("🚀 Starting Big Data Spatial Ingestion Benchmarks (US124)...")
    eval_in_memory_serialization_throughput(count=5000)
    eval_database_ingestion_throughput(count=1000)
    print("✅ Ingestion benchmarks completed successfully.")
