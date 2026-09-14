"""
Native Host Driver for Environment & Runtime Substrate.
Executes commands directly on the host operating system via subprocess.
"""
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from rps_ground.infrastructure.runtime.interfaces import ExecutionResultVO, IEnvironmentDriver


class NativeDriver(IEnvironmentDriver):
    """Executes commands directly on the host operating system."""

    def __init__(self, default_workdir: Optional[Path] = None):
        self._default_workdir = default_workdir or Path.cwd()

    def is_available(self) -> bool:
        return True

    def find_executable(self, cmd: str) -> Optional[str]:
        return shutil.which(cmd)

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
        effective_workdir = Path(workdir).resolve() if workdir else self._default_workdir
        effective_env = dict(os.environ)
        if env:
            effective_env.update(env)

        full_cmd = [cmd] + list(args or [])
        cmd_str = " ".join(full_cmd)

        start_time = time.monotonic()
        try:
            res = subprocess.run(
                full_cmd,
                cwd=str(effective_workdir),
                env=effective_env,
                capture_output=not interactive,
                text=True,
                timeout=timeout_sec
            )
            elapsed = time.monotonic() - start_time
            return ExecutionResultVO(
                exit_code=res.returncode,
                stdout=res.stdout or "" if not interactive else "",
                stderr=res.stderr or "" if not interactive else "",
                elapsed_sec=elapsed,
                command=cmd_str
            )
        except subprocess.TimeoutExpired as e:
            elapsed = time.monotonic() - start_time
            return ExecutionResultVO(
                exit_code=124,
                stdout=e.stdout or "" if isinstance(e.stdout, str) else "",
                stderr=f"Command timed out after {timeout_sec}s",
                elapsed_sec=elapsed,
                command=cmd_str
            )
        except FileNotFoundError:
            elapsed = time.monotonic() - start_time
            return ExecutionResultVO(
                exit_code=127,
                stdout="",
                stderr=f"Executable not found on PATH: {cmd}",
                elapsed_sec=elapsed,
                command=cmd_str
            )
        except Exception as e:
            elapsed = time.monotonic() - start_time
            return ExecutionResultVO(
                exit_code=1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                elapsed_sec=elapsed,
                command=cmd_str
            )
