from __future__ import annotations

import logging

import pytest

from config.env_config import AppConfig
from config.log_config import setup_logging

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_config(log_level: str = "INFO", log_file: str | None = None) -> AppConfig:
    return AppConfig(
        database_url="sqlite:///test.db",
        llm_provider="anthropic",
        llm_api_key="test-key",
        llm_model=None,
        max_result_rows=10000,
        log_level=log_level,
        log_file=log_file,
    )


@pytest.fixture(autouse=True)
def reset_root_logger():
    yield
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Tests — one per spec scenario
# ---------------------------------------------------------------------------


def test_returns_none():
    assert setup_logging(make_config()) is None


def test_default_info_level():
    setup_logging(make_config(log_level="INFO"))
    assert logging.getLogger().level == logging.INFO


def test_custom_debug_level():
    setup_logging(make_config(log_level="DEBUG"))
    assert logging.getLogger().level == logging.DEBUG


def test_formatter_contains_required_fields():
    setup_logging(make_config())
    root = logging.getLogger()
    expected = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    for handler in root.handlers:
        fmt = handler.formatter._fmt
        assert expected in fmt


def test_stream_handler_present():
    setup_logging(make_config(log_file=None))
    root = logging.getLogger()
    stream_handlers = [
        h
        for h in root.handlers
        if isinstance(h, logging.StreamHandler)
        and not isinstance(h, logging.FileHandler)
    ]
    assert len(stream_handlers) >= 1


def test_exactly_one_handler_no_file():
    setup_logging(make_config(log_file=None))
    assert len(logging.getLogger().handlers) == 1


def test_file_handler_added(tmp_path):
    log_file = str(tmp_path / "app.log")
    setup_logging(make_config(log_file=log_file))
    root = logging.getLogger()
    assert len(root.handlers) == 2
    file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1


def test_no_file_handler_when_none():
    setup_logging(make_config(log_file=None))
    root = logging.getLogger()
    file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 0


def test_idempotent_no_duplicates():
    setup_logging(make_config())
    count_after_first = len(logging.getLogger().handlers)
    setup_logging(make_config())
    assert len(logging.getLogger().handlers) == count_after_first


def test_idempotent_replaces_existing():
    extra = logging.StreamHandler()
    logging.getLogger().addHandler(extra)
    setup_logging(make_config())
    assert extra not in logging.getLogger().handlers


def test_no_env_var_access():
    source = open("config/log_config.py").read()
    for forbidden in ("os.getenv", "os.environ", "load_dotenv"):
        assert forbidden not in source, (
            f"Found forbidden call '{forbidden}' in config/log_config.py"
        )


def test_no_streamlit_import():
    source = open("config/log_config.py").read()
    import_lines = "\n".join(
        line for line in source.splitlines() if line.startswith(("import ", "from "))
    )
    assert "streamlit" not in import_lines
