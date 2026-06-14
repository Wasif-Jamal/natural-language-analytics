from __future__ import annotations

import dataclasses

import pytest

from config.env_config import AppConfig, load_config

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE_ENV = {
    "DATABASE_URL": "sqlite:///data/sales.db",
    "LLM_PROVIDER": "anthropic",
    "LLM_API_KEY": "test-key",
}


def _set_base(monkeypatch):
    for key, value in _BASE_ENV.items():
        monkeypatch.setenv(key, value)
    # Ensure optionals are absent so defaults kick in
    for opt in (
        "LLM_MODEL",
        "MAX_RESULT_ROWS",
        "LOG_LEVEL",
        "LOG_FILE",
        "GEMINI_API_KEY",
    ):
        monkeypatch.delenv(opt, raising=False)


# ---------------------------------------------------------------------------
# Phase 4 tests — one per spec scenario
# ---------------------------------------------------------------------------


def test_all_required_vars_returns_appconfig(monkeypatch):
    _set_base(monkeypatch)
    result = load_config()
    assert isinstance(result, AppConfig)


def test_appconfig_is_dataclass(monkeypatch):
    _set_base(monkeypatch)
    result = load_config()
    assert dataclasses.is_dataclass(result)
    # attribute access, not subscript
    assert result.database_url == "sqlite:///data/sales.db"


def test_missing_database_url_raises(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.delenv("DATABASE_URL")
    with pytest.raises(ValueError, match="DATABASE_URL"):
        load_config()


def test_missing_llm_provider_raises(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.delenv("LLM_PROVIDER")
    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        load_config()


@pytest.mark.parametrize(
    "provider, key_var, key_val",
    [
        ("anthropic", "LLM_API_KEY", "key-a"),
        ("openai", "LLM_API_KEY", "key-b"),
        ("gemini", "GEMINI_API_KEY", "key-c"),
        ("ollama", None, None),
    ],
)
def test_valid_providers_pass(monkeypatch, provider, key_var, key_val):
    _set_base(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    if key_var:
        monkeypatch.setenv(key_var, key_val)
    load_config()  # must not raise


def test_invalid_provider_raises(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "cohere")
    with pytest.raises(ValueError, match="cohere"):
        load_config()


def test_invalid_provider_message_lists_allowed(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "cohere")
    with pytest.raises(ValueError, match="anthropic"):
        load_config()


def test_gemini_reads_gemini_api_key(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "abc123")
    result = load_config()
    assert result.llm_api_key == "abc123"


def test_gemini_missing_gemini_api_key_raises(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        load_config()


def test_ollama_no_api_key_required(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = load_config()
    assert result.llm_api_key is None


def test_non_ollama_missing_llm_api_key_raises(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        load_config()


def test_max_result_rows_defaults_to_10000(monkeypatch):
    _set_base(monkeypatch)
    result = load_config()
    assert result.max_result_rows == 10000
    assert isinstance(result.max_result_rows, int)


def test_max_result_rows_cast_to_int(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.setenv("MAX_RESULT_ROWS", "500")
    result = load_config()
    assert result.max_result_rows == 500
    assert isinstance(result.max_result_rows, int)


def test_max_result_rows_non_numeric_raises(monkeypatch):
    _set_base(monkeypatch)
    monkeypatch.setenv("MAX_RESULT_ROWS", "lots")
    with pytest.raises(ValueError, match="MAX_RESULT_ROWS"):
        load_config()


def test_log_level_defaults_to_info(monkeypatch):
    _set_base(monkeypatch)
    result = load_config()
    assert result.log_level == "INFO"


def test_log_file_defaults_to_none(monkeypatch):
    _set_base(monkeypatch)
    result = load_config()
    assert result.log_file is None


def test_llm_model_defaults_to_none(monkeypatch):
    _set_base(monkeypatch)
    result = load_config()
    assert result.llm_model is None


def test_no_streamlit_import():
    source = open("config/env_config.py").read()
    assert "streamlit" not in source


def test_no_provider_sdk_import():
    source = open("config/env_config.py").read()
    import_lines = "\n".join(
        line for line in source.splitlines() if line.startswith(("import ", "from "))
    )
    for forbidden in ("anthropic", "openai", "google", "ollama"):
        assert forbidden not in import_lines, (
            f"Forbidden import '{forbidden}' found in config/env_config.py"
        )
