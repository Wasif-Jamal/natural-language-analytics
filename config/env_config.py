from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

_ALLOWED_PROVIDERS = {"anthropic", "openai", "gemini", "ollama"}
_DEFAULT_MAX_ROWS = 10_000
_DEFAULT_LOG_LEVEL = "INFO"


@dataclass
class AppConfig:
    database_url: str
    llm_provider: str
    llm_api_key: str | None
    llm_model: str | None
    max_result_rows: int
    log_level: str
    log_file: str | None


def load_config() -> AppConfig:
    load_dotenv()

    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        raise ValueError("DATABASE_URL is required but not set.")

    llm_provider = os.getenv("LLM_PROVIDER", "")
    if not llm_provider:
        raise ValueError("LLM_PROVIDER is required but not set.")
    if llm_provider not in _ALLOWED_PROVIDERS:
        allowed = ", ".join(sorted(_ALLOWED_PROVIDERS))
        raise ValueError(
            f"LLM_PROVIDER must be one of: {allowed}. Got: '{llm_provider}'."
        )

    if llm_provider == "ollama":
        llm_api_key = None
    elif llm_provider == "gemini":
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if not gemini_key:
            raise ValueError(
                "GEMINI_API_KEY is required for provider 'gemini' but not set."
            )
        llm_api_key = gemini_key
    else:
        key = os.getenv("LLM_API_KEY", "")
        if not key:
            raise ValueError(
                f"LLM_API_KEY is required for provider '{llm_provider}' but not set."
            )
        llm_api_key = key

    llm_model = os.getenv("LLM_MODEL", "") or None

    raw_max_rows = os.getenv("MAX_RESULT_ROWS", "")
    if raw_max_rows:
        try:
            max_result_rows = int(raw_max_rows)
        except ValueError:
            raise ValueError(
                f"MAX_RESULT_ROWS must be a positive integer. Got: '{raw_max_rows}'."
            )
    else:
        max_result_rows = _DEFAULT_MAX_ROWS

    log_level = os.getenv("LOG_LEVEL", _DEFAULT_LOG_LEVEL)
    log_file = os.getenv("LOG_FILE", "") or None

    return AppConfig(
        database_url=database_url,
        llm_provider=llm_provider,
        llm_api_key=llm_api_key,
        llm_model=llm_model,
        max_result_rows=max_result_rows,
        log_level=log_level,
        log_file=log_file,
    )
