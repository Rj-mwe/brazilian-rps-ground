"""
Context Manager for Environment & Runtime Substrate.
Resolves repository root, environment variables, working directories, and system paths.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional

from rps_ground.infrastructure.runtime.interfaces import RuntimeContextVO


class RuntimeContextManager:
    """Manages host execution contexts, path resolution, and variable injection."""

    def __init__(self, repo_root: Optional[Path] = None):
        if repo_root is not None:
            self._repo_root = Path(repo_root).resolve()
        else:
            self._repo_root = self._detect_repo_root()

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    def _detect_repo_root(self) -> Path:
        """Walk up from current file to find git root or pyproject.toml."""
        current = Path(__file__).resolve().parent
        for parent in [current] + list(current.parents):
            if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
                return parent
        return current

    def build_context(
        self,
        workdir: Optional[Path] = None,
        custom_env: Optional[Dict[str, str]] = None,
        extra_mounts: Optional[List[str]] = None,
        extra_devices: Optional[List[str]] = None
    ) -> RuntimeContextVO:
        """Build an immutable RuntimeContextVO with resolved environment variables."""
        effective_workdir = Path(workdir).resolve() if workdir else self._repo_root

        merged_env = dict(os.environ)
        merged_env["RPS_GROUND_REPO_ROOT"] = str(self._repo_root)
        if custom_env:
            merged_env.update(custom_env)

        display = os.environ.get("DISPLAY")
        mounts_list = [f"{self._repo_root}:{self._repo_root}:rw"]
        if extra_mounts:
            mounts_list.extend(extra_mounts)

        devices_list: List[str] = []
        if extra_devices:
            devices_list.extend(extra_devices)

        shm_path = "/dev/shm" if os.path.exists("/dev/shm") else None

        return RuntimeContextVO(
            workdir=effective_workdir,
            env=merged_env,
            display=display,
            mounts=tuple(mounts_list),
            devices=tuple(devices_list),
            shared_memory_path=shm_path
        )
