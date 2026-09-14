"""
Virtual Environment Driver for Environment & Runtime Substrate.
Executes commands within a specified or detected Python virtual environment.
"""
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from rps_ground.infrastructure.runtime.drivers.native_driver import NativeDriver
from rps_ground.infrastructure.runtime.interfaces import ExecutionResultVO, IEnvironmentDriver


class VirtualEnvDriver(IEnvironmentDriver):
    """Executes commands within a Python virtual environment (.venv)."""

    def __init__(self, repo_root: Optional[Path] = None, venv_path: Optional[Path] = None):
        self._repo_root = repo_root or Path.cwd()
        self._venv_path = venv_path or self._detect_venv()
        self._native_driver = NativeDriver(default_workdir=self._repo_root)

    def _detect_venv(self) -> Optional[Path]:
        # 1. Active VIRTUAL_ENV
        if "VIRTUAL_ENV" in os.environ:
            p = Path(os.environ["VIRTUAL_ENV"])
            if p.exists():
                return p

        # 2. .venv in repo root
        candidate = self._repo_root / ".venv"
        if candidate.exists():
            return candidate

        # 3. Current sys.prefix if running inside venv
        if sys.prefix != getattr(sys, "base_prefix", sys.prefix):
            return Path(sys.prefix)

        return None

    def is_available(self) -> bool:
        return self._venv_path is not None and self._venv_path.exists()

    @property
    def venv_bin_dir(self) -> Optional[Path]:
        if not self._venv_path:
            return None
        bin_dir = self._venv_path / "bin"
        return bin_dir if bin_dir.exists() else None

    def find_executable(self, cmd: str) -> Optional[Path]:
        bin_dir = self.venv_bin_dir
        if not bin_dir:
            return None
        candidate = bin_dir / cmd
        return candidate if candidate.exists() and os.access(candidate, os.X_OK) else None

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
        if not self.is_available() or not self.venv_bin_dir:
            return ExecutionResultVO(
                exit_code=127,
                stdout="",
                stderr="Virtual environment not found or unavailable.",
                elapsed_sec=0.0,
                command=f"{cmd} {' '.join(args or [])}".strip()
            )

        target_cmd = cmd
        executable_in_venv = self.find_executable(cmd)
        if executable_in_venv:
            target_cmd = str(executable_in_venv)

        # Inject VIRTUAL_ENV and PATH
        effective_env = dict(os.environ)
        effective_env["VIRTUAL_ENV"] = str(self._venv_path)
        effective_env["PATH"] = f"{self.venv_bin_dir}:{effective_env.get('PATH', '')}"
        if env:
            effective_env.update(env)

        return self._native_driver.run(
            cmd=target_cmd,
            args=args,
            env=effective_env,
            workdir=workdir or self._repo_root,
            timeout_sec=timeout_sec,
            interactive=interactive,
            **kwargs
        )
