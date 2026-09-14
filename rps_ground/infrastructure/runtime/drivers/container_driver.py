"""
Container Driver for Environment & Runtime Substrate.
Executes commands inside OCI containers via Podman or Docker CLI.
"""
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rps_ground.infrastructure.runtime.drivers.native_driver import NativeDriver
from rps_ground.infrastructure.runtime.interfaces import ExecutionResultVO, IEnvironmentDriver


class ContainerDriver(IEnvironmentDriver):
    """Executes commands inside an OCI container via Podman or Docker."""

    def __init__(self, engine_cmd: Optional[str] = None):
        self._engine = engine_cmd or self._detect_engine()
        self._native_driver = NativeDriver()

    def _detect_engine(self) -> Optional[str]:
        if shutil.which("podman"):
            return "podman"
        if shutil.which("docker"):
            return "docker"
        return None

    def is_available(self) -> bool:
        return self._engine is not None

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
        if not self.is_available():
            return ExecutionResultVO(
                exit_code=127,
                stdout="",
                stderr="Container runtime (podman/docker) not found on host.",
                elapsed_sec=0.0,
                command=f"{cmd} {' '.join(args or [])}".strip()
            )

        image = kwargs.get("image", "docker.io/library/ubuntu:24.04")
        container_name = kwargs.get("container_name")
        mounts: Tuple[str, ...] = kwargs.get("mounts", ())
        devices: Tuple[str, ...] = kwargs.get("devices", ())

        cli_args = ["run", "--rm"]
        if interactive:
            cli_args.append("-it")

        if container_name:
            cli_args.extend(["--name", container_name])

        for m in mounts:
            cli_args.extend(["-v", m])

        for d in devices:
            cli_args.extend(["--device", d])

        if env:
            for k, v in env.items():
                cli_args.extend(["-e", f"{k}={v}"])

        if workdir:
            cli_args.extend(["-w", str(workdir)])

        cli_args.append(image)
        cli_args.append(cmd)
        if args:
            cli_args.extend(args)

        return self._native_driver.run(
            cmd=self._engine,  # type: ignore[arg-type]
            args=cli_args,
            workdir=workdir,
            timeout_sec=timeout_sec,
            interactive=interactive
        )
