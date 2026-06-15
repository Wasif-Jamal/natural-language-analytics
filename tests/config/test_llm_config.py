from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import config.llm_config
from config.env_config import AppConfig
from config.llm_config import LLMClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_config(
    provider: str = "anthropic",
    api_key: str | None = "test-key",
    model: str | None = None,
) -> AppConfig:
    return AppConfig(
        database_url="sqlite:///:memory:",
        llm_provider=provider,
        llm_api_key=api_key,
        llm_model=model,
        max_result_rows=10_000,
        log_level="INFO",
        log_file=None,
    )


# ---------------------------------------------------------------------------
# Constructor — provider validation
# ---------------------------------------------------------------------------


def test_constructor_valid_anthropic():
    LLMClient(make_config(provider="anthropic"))  # must not raise


def test_constructor_valid_openai():
    LLMClient(make_config(provider="openai"))


def test_constructor_valid_gemini():
    LLMClient(make_config(provider="gemini"))


def test_constructor_valid_ollama():
    LLMClient(make_config(provider="ollama", model="llama3"))


def test_unsupported_provider_raises_value_error():
    with pytest.raises(ValueError, match="cohere"):
        LLMClient(make_config(provider="cohere"))


def test_unsupported_provider_message_lists_supported():
    with pytest.raises(ValueError, match="anthropic"):
        LLMClient(make_config(provider="cohere"))


# ---------------------------------------------------------------------------
# Constructor — default model resolution
# ---------------------------------------------------------------------------


def test_anthropic_default_model():
    client = LLMClient(make_config(provider="anthropic", model=None))
    assert client._model == "claude-sonnet-4-6"


def test_openai_default_model():
    client = LLMClient(make_config(provider="openai", model=None))
    assert client._model == "gpt-4o"


def test_gemini_default_model():
    client = LLMClient(make_config(provider="gemini", model=None))
    assert client._model == "gemini-2.0-flash"


def test_llm_model_override_respected():
    client = LLMClient(
        make_config(provider="anthropic", model="claude-haiku-4-5-20251001")
    )
    assert client._model == "claude-haiku-4-5-20251001"


def test_ollama_no_model_raises_value_error():
    with pytest.raises(ValueError, match="LLM_MODEL"):
        LLMClient(make_config(provider="ollama", model=None))


# ---------------------------------------------------------------------------
# complete() — return type and routing
# ---------------------------------------------------------------------------


def test_complete_anthropic_returns_str(monkeypatch):
    mock_sdk = MagicMock()
    mock_sdk.Anthropic.return_value.messages.create.return_value.content = [
        MagicMock(text="SELECT 1")
    ]
    monkeypatch.setattr(config.llm_config, "_anthropic_sdk", mock_sdk)
    client = LLMClient(make_config(provider="anthropic"))
    assert client.complete("sys", "usr") == "SELECT 1"


def test_complete_openai_returns_str(monkeypatch):
    mock_sdk = MagicMock()
    mock_sdk.OpenAI.return_value.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="SELECT 2"))
    ]
    monkeypatch.setattr(config.llm_config, "_openai_sdk", mock_sdk)
    client = LLMClient(make_config(provider="openai"))
    assert client.complete("sys", "usr") == "SELECT 2"


def test_complete_gemini_returns_str(monkeypatch):
    mock_genai = MagicMock()
    mock_genai.Client.return_value.models.generate_content.return_value.text = (
        "SELECT 3"
    )
    monkeypatch.setattr(config.llm_config, "_genai", mock_genai)
    client = LLMClient(make_config(provider="gemini"))
    assert client.complete("sys", "usr") == "SELECT 3"


def test_complete_ollama_returns_str(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"message": {"content": "SELECT 4"}}
    mock_requests = MagicMock()
    mock_requests.post.return_value = mock_resp
    monkeypatch.setattr(config.llm_config, "_requests", mock_requests)
    client = LLMClient(make_config(provider="ollama", model="llama3"))
    assert client.complete("sys", "usr") == "SELECT 4"


# ---------------------------------------------------------------------------
# complete() — provider-specific call shape
# ---------------------------------------------------------------------------


def test_anthropic_passes_max_tokens_4096(monkeypatch):
    mock_sdk = MagicMock()
    mock_sdk.Anthropic.return_value.messages.create.return_value.content = [
        MagicMock(text="ok")
    ]
    monkeypatch.setattr(config.llm_config, "_anthropic_sdk", mock_sdk)
    LLMClient(make_config(provider="anthropic")).complete("sys", "usr")
    _, kwargs = mock_sdk.Anthropic.return_value.messages.create.call_args
    assert kwargs.get("max_tokens") == 4096


def test_openai_formats_system_user_messages(monkeypatch):
    mock_sdk = MagicMock()
    mock_sdk.OpenAI.return_value.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="ok"))
    ]
    monkeypatch.setattr(config.llm_config, "_openai_sdk", mock_sdk)
    LLMClient(make_config(provider="openai")).complete("my-system", "my-user")
    _, kwargs = mock_sdk.OpenAI.return_value.chat.completions.create.call_args
    messages = kwargs.get("messages")
    assert messages[0] == {"role": "system", "content": "my-system"}
    assert messages[1] == {"role": "user", "content": "my-user"}


def test_gemini_passes_system_instruction(monkeypatch):
    mock_genai = MagicMock()
    mock_genai.Client.return_value.models.generate_content.return_value.text = "ok"
    monkeypatch.setattr(config.llm_config, "_genai", mock_genai)
    LLMClient(make_config(provider="gemini")).complete("my-system", "my-user")
    _, kwargs = mock_genai.types.GenerateContentConfig.call_args
    assert kwargs.get("system_instruction") == "my-system"


def test_ollama_posts_to_correct_url_with_stream_false(monkeypatch):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"message": {"content": "ok"}}
    mock_requests = MagicMock()
    mock_requests.post.return_value = mock_resp
    monkeypatch.setattr(config.llm_config, "_requests", mock_requests)
    LLMClient(make_config(provider="ollama", model="llama3")).complete("sys", "usr")
    args, kwargs = mock_requests.post.call_args
    assert args[0] == "http://localhost:11434/api/chat"
    assert kwargs["json"]["stream"] is False


# ---------------------------------------------------------------------------
# Import guards
# ---------------------------------------------------------------------------


def test_no_streamlit_import():
    source = open("config/llm_config.py").read()
    import_lines = "\n".join(
        line for line in source.splitlines() if line.startswith(("import ", "from "))
    )
    assert "streamlit" not in import_lines


def test_no_env_var_access():
    source = open("config/llm_config.py").read()
    for forbidden in ("os.getenv", "os.environ", "load_dotenv"):
        assert forbidden not in source
