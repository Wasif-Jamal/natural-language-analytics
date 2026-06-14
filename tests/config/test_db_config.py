from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ArgumentError as SAArgumentError
from sqlalchemy.exc import OperationalError as SAOperationalError

import config.db_config
from config.db_config import get_engine
from config.env_config import AppConfig

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_config(
    database_url: str = "sqlite:///:memory:",
    max_result_rows: int = 10_000,
) -> AppConfig:
    return AppConfig(
        database_url=database_url,
        llm_provider="anthropic",
        llm_api_key="test-key",
        llm_model=None,
        max_result_rows=max_result_rows,
        log_level="INFO",
        log_file=None,
    )


# ---------------------------------------------------------------------------
# Tests — one per spec scenario
# ---------------------------------------------------------------------------


def test_valid_sqlite_url_returns_engine():
    result = get_engine(make_config())
    assert isinstance(result, Engine)


def test_connectivity_probe_succeeds_for_memory_sqlite():
    get_engine(make_config())  # must not raise


def test_get_engine_sets_max_result_rows():
    get_engine(make_config(max_result_rows=500))
    assert config.db_config.MAX_RESULT_ROWS == 500


def test_max_result_rows_default_is_10000():
    get_engine(make_config())
    assert config.db_config.MAX_RESULT_ROWS == 10_000


def test_unreachable_host_raises_operational_error(monkeypatch):
    mock_engine = MagicMock()
    mock_engine.connect.side_effect = SAOperationalError("unreachable", None, None)
    monkeypatch.setattr(
        config.db_config, "_sa_create_engine", lambda *a, **kw: mock_engine
    )
    with pytest.raises(SAOperationalError):
        get_engine(make_config(database_url="postgresql://user:pass@localhost/db"))


def test_malformed_url_raises_argument_error():
    with pytest.raises(SAArgumentError):
        get_engine(make_config(database_url="notavalidurl"))


def test_no_streamlit_import():
    source = open("config/db_config.py").read()
    import_lines = "\n".join(
        line for line in source.splitlines() if line.startswith(("import ", "from "))
    )
    assert "streamlit" not in import_lines


def test_no_env_var_access():
    source = open("config/db_config.py").read()
    for forbidden in ("os.getenv", "os.environ", "load_dotenv"):
        assert forbidden not in source, (
            f"Found forbidden call '{forbidden}' in config/db_config.py"
        )
