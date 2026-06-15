from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import starter
from config.env_config import AppConfig


def make_config() -> AppConfig:
    return AppConfig(
        database_url="sqlite:///:memory:",
        llm_provider="anthropic",
        llm_api_key="test-key",
        llm_model=None,
        max_result_rows=10_000,
        log_level="INFO",
        log_file=None,
    )


@pytest.fixture
def mock_deps(monkeypatch):
    session: dict = {}

    mock_st = MagicMock()
    mock_st.session_state = session
    monkeypatch.setattr(starter, "st", mock_st)

    monkeypatch.setattr(starter, "load_config", lambda: make_config())
    monkeypatch.setattr(starter, "setup_logging", MagicMock())

    mock_engine = MagicMock()
    monkeypatch.setattr(starter, "get_engine", lambda c: mock_engine)

    mock_llm = MagicMock()
    monkeypatch.setattr(starter, "LLMClient", lambda c: mock_llm)

    mock_inspector = MagicMock()
    mock_inspector.get_table_names.return_value = ["orders", "products"]
    mock_inspector.get_columns.return_value = [
        {"name": "id", "type": MagicMock(__str__=lambda s: "INTEGER")},
        {"name": "name", "type": MagicMock(__str__=lambda s: "VARCHAR")},
    ]
    monkeypatch.setattr(starter, "inspect", lambda e: mock_inspector)

    return {"session": session, "engine": mock_engine, "llm": mock_llm}


def test_all_session_keys_populated(mock_deps):
    starter.bootstrap()
    session = mock_deps["session"]
    assert "db_engine" in session
    assert "llm_client" in session
    assert "db_schema" in session
    assert "query_history" in session


def test_db_engine_stored(mock_deps):
    starter.bootstrap()
    assert mock_deps["session"]["db_engine"] is mock_deps["engine"]


def test_llm_client_stored(mock_deps):
    starter.bootstrap()
    assert mock_deps["session"]["llm_client"] is mock_deps["llm"]


def test_query_history_initialized_empty(mock_deps):
    starter.bootstrap()
    assert mock_deps["session"]["query_history"] == []


def test_db_schema_is_non_empty_dict(mock_deps):
    starter.bootstrap()
    schema = mock_deps["session"]["db_schema"]
    assert isinstance(schema, dict)
    assert len(schema) > 0


def test_schema_contains_table_names(mock_deps):
    starter.bootstrap()
    schema = mock_deps["session"]["db_schema"]
    assert "orders" in schema
    assert "products" in schema


def test_guard_prevents_re_run(mock_deps, monkeypatch):
    mock_load = MagicMock(return_value=make_config())
    monkeypatch.setattr(starter, "load_config", mock_load)
    mock_deps["session"]["db_engine"] = "already_set"

    starter.bootstrap()

    mock_load.assert_not_called()
    assert mock_deps["session"]["db_engine"] == "already_set"
