"""
Unit tests for Platform Substrates (Configuration, Persistence, Runtime).
"""

from rps_ground.infrastructure.config.configuration_substrate import (
    ConfigurationSubstrate,
    DatabaseConfigVO,
    GroundConfigVO,
)
from rps_ground.infrastructure.persistence.database_substrate import DatabaseSubstrate
from rps_ground.infrastructure.runtime.context_manager import RuntimeContextManager
from rps_ground.infrastructure.runtime.drivers.native_driver import NativeDriver
from rps_ground.infrastructure.runtime.drivers.venv_driver import VirtualEnvDriver
from rps_ground.infrastructure.runtime.environment_substrate import EnvironmentSubstrate


def test_configuration_substrate_yaml_loading():
    cfg_sub = ConfigurationSubstrate.get_instance()
    config = cfg_sub.config
    assert isinstance(config, GroundConfigVO)
    assert len(config.stations) == 5

    sjc = next(s for s in config.stations if s.code == "SJC")
    assert sjc.latitude_deg == -23.210
    assert sjc.longitude_deg == -45.880
    assert sjc.altitude_m == 660.0

    assert config.database.database == "rps_ground"
    assert config.database.port == 5432


def test_configuration_cascade_env_override(monkeypatch):
    monkeypatch.setenv("RPS_GROUND_DB_PORT", "5433")
    monkeypatch.setenv("RPS_GROUND_DB_NAME", "rps_custom_db")

    cfg_sub = ConfigurationSubstrate(auto_load=False)
    cfg = cfg_sub.load()
    assert cfg.database.port == 5433
    assert cfg.database.database == "rps_custom_db"


def test_runtime_context_manager():
    ctx_mgr = RuntimeContextManager()
    assert ctx_mgr.repo_root.exists()
    assert (ctx_mgr.repo_root / "pyproject.toml").exists()

    ctx = ctx_mgr.build_context()
    assert "RPS_GROUND_REPO_ROOT" in ctx.env
    assert ctx.workdir == ctx_mgr.repo_root


def test_native_and_venv_driver_execution():
    native = NativeDriver()
    res = native.run("echo", ["HEXAGONO_DOURADO"])
    assert res.is_success
    assert "HEXAGONO_DOURADO" in res.stdout

    venv_driver = VirtualEnvDriver()
    assert venv_driver.is_available()
    res_venv = venv_driver.run("python", ["-c", "print(1 + 1)"])
    assert res_venv.is_success
    assert "2" in res_venv.stdout


def test_environment_substrate_facade():
    env_sub = EnvironmentSubstrate()
    res = env_sub.run("python", ["-c", "print('SUBSTRATE_OK')"], regime="auto")
    assert res.is_success
    assert "SUBSTRATE_OK" in res.stdout


def test_database_substrate_graceful_health_check_when_inactive():
    # Unreachable database host/port to ensure no crash and graceful return False
    dummy_config = DatabaseConfigVO(host="127.0.0.1", port=59999, database="no_db")
    db_sub = DatabaseSubstrate(config=dummy_config)

    # Health check must return False gracefully, NOT raise unhandled exception
    assert db_sub.health_check() is False
    assert db_sub.is_server_binary_available() is True
