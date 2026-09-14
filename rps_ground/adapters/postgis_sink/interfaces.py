"""
Internal Interfaces for PostGIS Sink Fractal Adapter.
"""
from abc import ABC, abstractmethod
from typing import Optional


class IPostgisSinkCoordinator(ABC):
    """Adapter Application interface orchestrating PostGIS sink lifecycle and health."""

    @abstractmethod
    def verify_readiness(self) -> bool:
        pass

    @abstractmethod
    def get_postgis_version(self) -> Optional[str]:
        pass
