from __future__ import annotations

import anthropic as _anthropic_sdk
import openai as _openai_sdk
import requests as _requests
from google import genai as _genai

from config.env_config import AppConfig

_DEFAULTS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "gemini": "gemini-2.0-flash",
}

_OLLAMA_URL = "http://localhost:11434/api/chat"


class LLMClient:
    def __init__(self, config: AppConfig) -> None:
        provider = config.llm_provider
        if provider not in (*_DEFAULTS, "ollama"):
            raise ValueError(
                f"Unsupported LLM provider: '{provider}'. "
                f"Supported: {', '.join(sorted({*_DEFAULTS, 'ollama'}))}."
            )
        if provider == "ollama" and config.llm_model is None:
            raise ValueError(
                "LLM_MODEL must be set when LLM_PROVIDER=ollama — "
                "no default model is enforced for Ollama."
            )
        self._provider = provider
        self._api_key = config.llm_api_key
        self._model: str = (
            config.llm_model if config.llm_model is not None else _DEFAULTS[provider]
        )

    def complete(self, system: str, user: str) -> str:
        if self._provider == "anthropic":
            return self._anthropic(system, user)
        if self._provider == "openai":
            return self._openai(system, user)
        if self._provider == "gemini":
            return self._gemini(system, user)
        return self._ollama(system, user)

    def _anthropic(self, system: str, user: str) -> str:
        client = _anthropic_sdk.Anthropic(api_key=self._api_key)
        response = client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text

    def _openai(self, system: str, user: str) -> str:
        client = _openai_sdk.OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

    def _gemini(self, system: str, user: str) -> str:
        client = _genai.Client(api_key=self._api_key)
        response = client.models.generate_content(
            model=self._model,
            contents=user,
            config=_genai.types.GenerateContentConfig(
                system_instruction=system,
            ),
        )
        return response.text

    def _ollama(self, system: str, user: str) -> str:
        response = _requests.post(
            _OLLAMA_URL,
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
