"""
Environment & Runtime Substrate (Hexágono Dourado Infrastructure Substrate).
Unified execution facade decoupling ground segment adapters and domain services
from OS runtimes, virtual environments, and OCI containers.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from rps_ground.infrastructure.runtime.context_manager import RuntimeContextManager
from rps_ground.infrastructure.runtime.drivers.container_driver import ContainerDriver
from rps_ground.infrastructure.runtime.drivers.native_driver import NativeDriver
from rps_ground.infrastructure.runtime.drivers.venv_driver import VirtualEnvDriver
from rps_ground.infrastructure.runtime.interfaces import (
    ExecutionResultVO,
    RuntimeManifestVO,
)
from rps_ground.infrastructure.runtime.manifest_parser import RuntimeManifestParser


class EnvironmentSubstrate:
    """Unified Facade for environment execution across host, venv, and container regimes."""

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        context_manager: Optional[RuntimeContextManager] = None,
        native_driver: Optional[NativeDriver] = None,
        venv_driver: Optional[VirtualEnvDriver] = None,
        container_driver: Optional[ContainerDriver] = None
    ):
        self._context_manager = context_manager or RuntimeContextManager(repo_root=repo_root)
        self._native_driver = native_driver or NativeDriver(default_workdir=self._context_manager.repo_root)
        self._venv_driver = venv_driver or VirtualEnvDriver(repo_root=self._context_manager.repo_root)
        self._container_driver = container_driver or ContainerDriver()

    @property
    def context_manager(self) -> RuntimeContextManager:
        return self._context_manager

    @property
    def native_driver(self) -> NativeDriver:
        return self._native_driver

    @property
    def venv_driver(self) -> VirtualEnvDriver:
        return self._venv_driver

    @property
    def container_driver(self) -> ContainerDriver:
        return self._container_driver

    def resolve_manifest(
        self,
        manifest: Optional[Union[RuntimeManifestVO, Path, str, Dict[str, Any]]]
    ) -> Optional[RuntimeManifestVO]:
        """Resolve manifest reference into a validated RuntimeManifestVO."""
        if manifest is None:
            return None
        if isinstance(manifest, RuntimeManifestVO):
            return manifest
        if isinstance(manifest, (Path, str)):
            p = Path(manifest)
            if p.exists() and p.is_file():
                return RuntimeManifestParser.parse_file(p)
            return RuntimeManifestParser.parse_yaml(str(manifest))
        if isinstance(manifest, dict):
            return RuntimeManifestParser.parse_dict(manifest)
        raise TypeError(f"Unsupported manifest type: {type(manifest)}")

    def run(
        self,
        cmd: str,
        args: Optional[List[str]] = None,
        manifest: Optional[Union[RuntimeManifestVO, Path, str, Dict[str, Any]]] = None,
        regime: str = "auto",
        workdir: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        timeout_sec: Optional[float] = None,
        interactive: bool = False,
        **kwargs: Any
    ) -> ExecutionResultVO:
        """Execute a command adhering to declarative preferences and system availability."""
        parsed_manifest = self.resolve_manifest(manifest)

        effective_args = list(args or [])
        if not effective_args and parsed_manifest and parsed_manifest.default_args:
            effective_args = list(parsed_manifest.default_args)

        effective_env: Dict[str, str] = {}
        if parsed_manifest and parsed_manifest.env:
            effective_env.update(parsed_manifest.env)
        if env:
            effective_env.update(env)

        effective_workdir = workdir or self._context_manager.repo_root

        if regime == "native":
            return self._native_driver.run(
                cmd=cmd,
                args=effective_args,
                env=effective_env,
                workdir=effective_workdir,
                timeout_sec=timeout_sec,
                interactive=interactive,
                **kwargs
            )

        if regime == "venv":
            return self._venv_driver.run(
                cmd=cmd,
                args=effective_args,
                env=effective_env,
                workdir=effective_workdir,
                timeout_sec=timeout_sec,
                interactive=interactive,
                **kwargs
            )

        if regime == "container":
            return self._dispatch_container(
                cmd=cmd,
                args=effective_args,
                manifest=parsed_manifest,
                env=effective_env,
                workdir=effective_workdir,
                timeout_sec=timeout_sec,
                interactive=interactive,
                **kwargs
            )

        if regime == "auto":
            preferences: Tuple[str, ...] = ("native", "venv", "container")
            if parsed_manifest and parsed_manifest.isolation_preference:
                preferences = parsed_manifest.isolation_preference

            for pref in preferences:
                if pref == "native" and self._native_driver.find_executable(cmd):
                    return self._native_driver.run(
                        cmd=cmd,
                        args=effective_args,
                        env=effective_env,
                        workdir=effective_workdir,
                        timeout_sec=timeout_sec,
                        interactive=interactive,
                        **kwargs
                    )
                if pref == "venv" and self._venv_driver.is_available():
                    if self._venv_driver.find_executable(cmd):
                        return self._venv_driver.run(
                            cmd=cmd,
                            args=effective_args,
                            env=effective_env,
                            workdir=effective_workdir,
                            timeout_sec=timeout_sec,
                            interactive=interactive,
                            **kwargs
                        )
                if pref == "container" and self._container_driver.is_available():
                    return self._dispatch_container(
                        cmd=cmd,
                        args=effective_args,
                        manifest=parsed_manifest,
                        env=effective_env,
                        workdir=effective_workdir,
                        timeout_sec=timeout_sec,
                        interactive=interactive,
                        **kwargs
                    )

            # Fallback to native if binary is found anywhere
            if self._native_driver.find_executable(cmd):
                return self._native_driver.run(
                    cmd=cmd,
                    args=effective_args,
                    env=effective_env,
                    workdir=effective_workdir,
                    timeout_sec=timeout_sec,
                    interactive=interactive,
                    **kwargs
                )

            return ExecutionResultVO(
                exit_code=127,
                stdout="",
                stderr=f"Command '{cmd}' cannot be executed across regimes {preferences}.",
                elapsed_sec=0.0,
                command=f"{cmd} {' '.join(effective_args)}".strip()
            )

        raise ValueError(f"Unknown execution regime: '{regime}'. Expected 'auto', 'native', 'venv', or 'container'.")

    def _dispatch_container(
        self,
        cmd: str,
        args: List[str],
        manifest: Optional[RuntimeManifestVO],
        env: Dict[str, str],
        workdir: Path,
        timeout_sec: Optional[float],
        interactive: bool,
        **kwargs: Any
    ) -> ExecutionResultVO:
        context = self._context_manager.build_context(
            workdir=workdir,
            custom_env=env,
            extra_mounts=list(manifest.mounts) if manifest else None
        )

        image = kwargs.get("image") or (manifest.fallback_image if manifest else None)
        container_name = kwargs.get("container_name") or (manifest.container_name if manifest else None)

        all_devices = list(context.devices)
        if manifest and manifest.devices:
            for d in manifest.devices:
                if d not in all_devices:
                    all_devices.append(d)

        return self._container_driver.run(
            cmd=cmd,
            args=args,
            env=context.env,
            workdir=context.workdir,
            timeout_sec=timeout_sec,
            interactive=interactive,
            image=image,
            mounts=context.mounts,
            devices=tuple(all_devices),
            container_name=container_name,
            **kwargs
        )
