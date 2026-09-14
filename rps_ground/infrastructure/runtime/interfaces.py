"""
Interfaces and Value Objects for the Environment & Runtime Substrate.
Decouples ground segment adapters and infrastructure from OS runtimes, virtualenvs, and containers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ExecutionResultVO:
    """Immutable result of a command executed by an Environment Driver."""
    exit_code: int
    stdout: str
    stderr: str
    elapsed_sec: float
    command: str

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0


@dataclass(frozen=True)
class RuntimeContextVO:
    """Immutable environment context resolved by the Context Manager."""
    workdir: Path
    env: Dict[str, str] = field(default_factory=dict)
    display: Optional[str] = None
    mounts: Tuple[str, ...] = field(default_factory=tuple)
    devices: Tuple[str, ...] = field(default_factory=tuple)
    shared_memory_path: Optional[str] = None


@dataclass(frozen=True)
class RuntimeManifestVO:
    """Immutable runtime specification declared by an adapter or service."""
    tool_name: str
    version: str = "latest"
    fallback_image: Optional[str] = None
    isolation_preference: Tuple[str, ...] = ("native", "venv", "container")
    mounts: Tuple[str, ...] = field(default_factory=tuple)
    devices: Tuple[str, ...] = field(default_factory=tuple)
    env: Dict[str, str] = field(default_factory=dict)
    default_args: Tuple[str, ...] = field(default_factory=tuple)
    container_name: Optional[str] = None


class IEnvironmentDriver(ABC):
    """Abstract strategy contract for executing commands across isolation regimes."""

    @abstractmethod
    def run(
        self,
        cmd: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        workdir: Optional[Path] = None,
        timeout_sec: Optional[float] = None,
        interactive: bool = False,
        **kwargs: Any
    ) -> ExecutionResultVO:
        """Execute a command within this driver's isolation regime."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Verify whether this driver and its underlying tooling can execute on the host."""
        pass
