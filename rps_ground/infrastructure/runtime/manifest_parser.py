"""
Runtime Manifest Parser for Environment Substrate.
Parses YAML files or dictionaries into immutable RuntimeManifestVO instances.
"""
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

from rps_ground.infrastructure.runtime.interfaces import RuntimeManifestVO


class RuntimeManifestParser:
    """Deserializes and validates runtime manifests."""

    @classmethod
    def parse_dict(cls, data: Dict[str, Any]) -> RuntimeManifestVO:
        tool_name = data.get("tool_name") or data.get("name")
        if not tool_name:
            raise ValueError("Runtime manifest must contain 'tool_name' or 'name'.")

        version = str(data.get("version", "latest"))
        fallback_image = data.get("fallback_image") or data.get("image")
        preferences: Tuple[str, ...] = tuple(data.get("isolation_preference", ("native", "venv", "container")))
        mounts: Tuple[str, ...] = tuple(data.get("mounts", ()))
        devices: Tuple[str, ...] = tuple(data.get("devices", ()))
        env: Dict[str, str] = {k: str(v) for k, v in data.get("env", {}).items()}
        default_args: Tuple[str, ...] = tuple(data.get("default_args", ()))
        container_name = data.get("container_name")

        return RuntimeManifestVO(
            tool_name=tool_name,
            version=version,
            fallback_image=fallback_image,
            isolation_preference=preferences,
            mounts=mounts,
            devices=devices,
            env=env,
            default_args=default_args,
            container_name=container_name
        )

    @classmethod
    def parse_yaml(cls, yaml_content: str) -> RuntimeManifestVO:
        data = yaml.safe_load(yaml_content) or {}
        return cls.parse_dict(data)

    @classmethod
    def parse_file(cls, path: Path) -> RuntimeManifestVO:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Manifest file not found: {p}")
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls.parse_dict(data)
